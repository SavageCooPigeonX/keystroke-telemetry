/**
 * extension.ts — Pigeon Chat VS Code Extension
 *
 * TWO MODES:
 *   A. Background telemetry (always-on, no panel needed):
 *      - Captures typing patterns from normal VS Code editing
 *      - Logs events to logs/keystroke_live.jsonl
 *      - Flushes session to classify_bridge.py every 60s of activity
 *        or on file save — updates operator_profile, copilot-instructions, etc.
 *
 *   B. Pigeon Chat panel (optional, on-demand):
 *      - Custom chat webview with per-message classification
 *      - Injects operator-state into LLM system prompt
 *
 * classify_bridge.py writes operator_profile.md and refreshes
 * copilot-instructions.md directly — Copilot picks up the updated
 * state on the next context load.
 */
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn } from 'child_process';
import * as crypto from 'crypto';

function nonce() { return crypto.randomBytes(16).toString('hex'); }

function getRoot(): string {
    return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '';
}

function readOperatorState(root: string): string {
    try {
        const text = fs.readFileSync(
            path.join(root, '.github', 'copilot-instructions.md'), 'utf-8');
        const m = text.match(
            /<!-- pigeon:operator-state -->([\s\S]*?)<!-- \/pigeon:operator-state -->/);
        return m ? m[1].trim() : '';
    } catch { return ''; }
}

interface ClassifyResult { state: string; hesitation: number; wpm: number; rework_verdict?: string; }

function classifySession(
    root: string, events: object[], submitted: boolean,
    queryText?: string, postResponseEvents?: object[]
): Promise<ClassifyResult> {
    const fallback: ClassifyResult = { state: 'neutral', hesitation: 0, wpm: 0 };
    return new Promise(resolve => {
        const bridge = path.join(root, 'vscode-extension', 'classify_bridge.py');
        if (!fs.existsSync(bridge)) { resolve(fallback); return; }
        const proc = spawn('py', [bridge, root], { cwd: root });
        proc.stdin.write(JSON.stringify({
            events, submitted,
            query_text: queryText ?? '',
            post_response_events: postResponseEvents ?? [],
        }));
        proc.stdin.end();
        let out = '';
        proc.stdout.on('data', (d: Buffer) => out += d.toString());
        proc.on('close', () => { try { resolve(JSON.parse(out.trim())); } catch { resolve(fallback); } });
        proc.on('error', () => resolve(fallback));
    });
}

// ── Background Telemetry ─────────────────────────────────────────────────────
// Always-on process. Captures ALL operator activity:
//   - Editor typing (any scheme — files, untitled, notebooks, search editors)
//   - Terminal activity (shell commands, output reading pauses)
//   - Context switches (file focus changes = research/browsing signal)
//   - Selection changes (reading/scanning signal when no typing)
// Logs everything to logs/keystroke_live.jsonl
// Flushes to classify_bridge.py every 60s or on save

const FLUSH_INTERVAL_MS = 60_000;
const PAUSE_THRESHOLD_MS = 2_000;
const IDLE_THRESHOLD_MS = 300_000;  // 5min idle = session break

interface RawEvent {
    ts: number;
    type: 'insert' | 'backspace' | 'pause' | 'focus' | 'terminal' | 'selection' | 'save' | 'idle';
    len?: number;
    duration_ms?: number;
    file?: string;
    context?: string;
}

class BackgroundTelemetry {
    private _events: RawEvent[] = [];
    private _lastActivityMs = 0;
    private _flushTimer: NodeJS.Timeout | undefined;
    private _root: string;
    private _logPath: string;
    private _active = false;
    private _sessionId: string;
    private _totalFlushed = 0;

    constructor(root: string) {
        this._root = root;
        this._sessionId = crypto.randomBytes(6).toString('hex');
        const logDir = path.join(root, 'logs');
        if (!fs.existsSync(logDir)) { fs.mkdirSync(logDir, { recursive: true }); }
        this._logPath = path.join(logDir, 'keystroke_live.jsonl');
    }

    start(context: vscode.ExtensionContext) {
        if (this._active) return;
        this._active = true;

        // ── Editor typing: ALL document schemes (files, untitled, search, notebooks) ──
        context.subscriptions.push(
            vscode.workspace.onDidChangeTextDocument(e => this._onDocChange(e))
        );

        // ── File saves ──
        context.subscriptions.push(
            vscode.workspace.onDidSaveTextDocument(doc => {
                const rel = this._relPath(doc.uri);
                this._push({ ts: Date.now(), type: 'save', file: rel });
                this._flushIfReady();
            })
        );

        // ── Focus changes: file switches = context switches / browsing ──
        context.subscriptions.push(
            vscode.window.onDidChangeActiveTextEditor(editor => {
                if (!editor) return;
                const now = Date.now();
                const rel = this._relPath(editor.document.uri);
                // Gap since last activity = reading/browsing time
                const gap = this._lastActivityMs > 0 ? now - this._lastActivityMs : 0;
                this._push({ ts: now, type: 'focus', file: rel,
                    duration_ms: gap > PAUSE_THRESHOLD_MS ? gap : undefined,
                    context: editor.document.uri.scheme });
                this._lastActivityMs = now;
            })
        );

        // ── Selection changes: scanning/reading code without editing ──
        context.subscriptions.push(
            vscode.window.onDidChangeTextEditorSelection(e => {
                // Only record meaningful selections (not cursor blinks)
                const sel = e.selections[0];
                if (!sel || sel.isEmpty) return;
                const now = Date.now();
                // Throttle: max 1 selection event per 2 seconds
                const lastSelIdx = this._events.map(ev => ev.type).lastIndexOf('selection');
                if (lastSelIdx >= 0 && now - this._events[lastSelIdx].ts < 2000) return;
                const rel = this._relPath(e.textEditor.document.uri);
                this._push({ ts: now, type: 'selection', file: rel,
                    len: e.textEditor.document.getText(sel).length });
            })
        );

        // ── Terminal activity: detect when operator is in terminal ──
        context.subscriptions.push(
            vscode.window.onDidChangeActiveTerminal(term => {
                if (!term) return;
                this._push({ ts: Date.now(), type: 'terminal',
                    context: term.name });
                this._lastActivityMs = Date.now();
            })
        );
        context.subscriptions.push(
            vscode.window.onDidOpenTerminal(term => {
                this._push({ ts: Date.now(), type: 'terminal',
                    context: `open:${term.name}` });
            })
        );

        // ── Periodic flush + idle detection ──
        this._flushTimer = setInterval(() => {
            const now = Date.now();
            if (this._lastActivityMs > 0 && (now - this._lastActivityMs) >= IDLE_THRESHOLD_MS) {
                // Operator went idle — record break and flush
                this._push({ ts: now, type: 'idle',
                    duration_ms: now - this._lastActivityMs });
                this._flushIfReady();
                this._lastActivityMs = 0;  // reset for next active period
            } else {
                this._flushIfReady();
            }
        }, FLUSH_INTERVAL_MS);
        context.subscriptions.push({
            dispose: () => { if (this._flushTimer) clearInterval(this._flushTimer); }
        });

        // Log startup
        this._push({ ts: Date.now(), type: 'focus', context: 'session_start' });
        this._appendLog([{ ts: Date.now(), type: 'focus', context: 'session_start' }]);

        const bar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 0);
        bar.text = '$(pulse) Pigeon';
        bar.tooltip = 'Keystroke telemetry active';
        bar.show();
        context.subscriptions.push(bar);
    }

    private _relPath(uri: vscode.Uri): string {
        if (uri.scheme === 'file') {
            return path.relative(this._root, uri.fsPath).replace(/\\/g, '/');
        }
        return `${uri.scheme}:${uri.path}`;
    }

    private _push(event: RawEvent) {
        this._events.push(event);
        if (event.type !== 'idle') {
            this._lastActivityMs = event.ts;
        }
    }

    private _onDocChange(e: vscode.TextDocumentChangeEvent) {
        // Capture ALL schemes — files, untitled, search editors, notebooks, scm input
        const now = Date.now();
        const relFile = this._relPath(e.document.uri);

        // Detect pause
        if (this._lastActivityMs > 0) {
            const gap = now - this._lastActivityMs;
            if (gap >= PAUSE_THRESHOLD_MS) {
                this._push({ ts: now, type: 'pause', duration_ms: gap, file: relFile });
            }
        }

        for (const change of e.contentChanges) {
            if (change.text.length > 0 && change.rangeLength === 0) {
                this._push({ ts: now, type: 'insert', len: change.text.length, file: relFile });
            } else if (change.rangeLength > 0 && change.text.length === 0) {
                this._push({ ts: now, type: 'backspace', len: change.rangeLength, file: relFile });
            } else if (change.rangeLength > 0 && change.text.length > 0) {
                this._push({ ts: now, type: 'backspace', len: change.rangeLength, file: relFile });
                this._push({ ts: now, type: 'insert', len: change.text.length, file: relFile });
            }
        }
    }

    private _flushIfReady() {
        if (this._events.length < 3) return;

        const batch = [...this._events];
        this._events = [];

        // Append to local JSONL log
        this._appendLog(batch);

        // Fire classify_bridge in background — updates operator_profile + copilot-instructions
        const typingEvents = batch.filter(e => e.type === 'insert' || e.type === 'backspace' || e.type === 'pause');
        if (typingEvents.length >= 3) {
            const activeFile = vscode.window.activeTextEditor?.document.fileName ?? '';
            const label = activeFile ? `bg:${activeFile.split(/[/\\]/).pop()}` : 'bg:idle';
            classifySession(this._root, typingEvents, true, label).catch(() => {});
            this._totalFlushed++;
        }
    }

    private _appendLog(events: RawEvent[]) {
        try {
            const files = [...new Set(events.map(e => e.file).filter(Boolean))];
            const types: Record<string, number> = {};
            for (const e of events) { types[e.type] = (types[e.type] || 0) + 1; }
            const line = JSON.stringify({
                ts: new Date().toISOString(),
                sid: this._sessionId,
                n: events.length,
                types,
                files: files.slice(0, 20),
                span_ms: events.length > 1 ? events[events.length - 1].ts - events[0].ts : 0,
                total_flushed: this._totalFlushed,
            }) + '\n';
            fs.appendFileSync(this._logPath, line, 'utf-8');
        } catch { /* non-fatal */ }
    }
}

// ── Chat Panel ───────────────────────────────────────────────────────────────

class PigeonChatPanel {
    static current: PigeonChatPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _root: string;
    private readonly _extPath: string;
    private _history: Array<{ role: string; content: string }> = [];
    private _disposables: vscode.Disposable[] = [];

    static createOrShow(context: vscode.ExtensionContext) {
        if (PigeonChatPanel.current) { PigeonChatPanel.current._panel.reveal(); return; }
        const panel = vscode.window.createWebviewPanel(
            'pigeonChat', '🐦 Pigeon Chat', vscode.ViewColumn.Beside,
            { enableScripts: true, retainContextWhenHidden: true }
        );
        PigeonChatPanel.current = new PigeonChatPanel(panel, getRoot(), context.extensionPath);
    }

    constructor(panel: vscode.WebviewPanel, root: string, extPath: string) {
        this._panel = panel; this._root = root; this._extPath = extPath;
        this._panel.webview.html = this._buildHtml();
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(m => this._onMessage(m), null, this._disposables);
    }

    private async _onMessage(msg: any) {
        if (msg.type === 'submit') {
            const result = await classifySession(
                this._root, msg.events, true,
                msg.query_text, msg.post_response_events
            );
            this._panel.webview.postMessage({ type: 'state', ...result });
            const opCtx = readOperatorState(this._root);
            await this._respond(msg.text, opCtx);
        } else if (msg.type === 'discard') {
            classifySession(this._root, msg.events, false); // fire & forget
        }
    }

    private async _respond(text: string, opCtx: string) {
        this._history.push({ role: 'user', content: text });
        try {
            await this._callCopilot(opCtx);
        } catch {
            await this._callDeepSeek(opCtx);
        }
    }

    private async _callCopilot(opCtx: string) {
        const [model] = await vscode.lm.selectChatModels({ vendor: 'copilot' });
        if (!model) throw new Error('no copilot model');
        const systemText = opCtx
            ? `You are a helpful assistant.\n\n## Live Operator State\n${opCtx}`
            : 'You are a helpful assistant.';
        const messages: vscode.LanguageModelChatMessage[] = [
            vscode.LanguageModelChatMessage.User(systemText),
            ...this._history.map(h =>
                h.role === 'user'
                    ? vscode.LanguageModelChatMessage.User(h.content)
                    : vscode.LanguageModelChatMessage.Assistant(h.content)
            )
        ];
        const cts = new vscode.CancellationTokenSource();
        const res = await model.sendRequest(messages, {}, cts.token);
        let full = '';
        for await (const chunk of res.text) {
            full += chunk;
            this._panel.webview.postMessage({ type: 'chunk', text: chunk });
        }
        this._history.push({ role: 'assistant', content: full });
        this._panel.webview.postMessage({ type: 'done' });
    }

    private async _callDeepSeek(opCtx: string) {
        const key = process.env.DEEPSEEK_API_KEY;
        if (!key) {
            this._panel.webview.postMessage({ type: 'error', text: 'No model available. Install GitHub Copilot or set DEEPSEEK_API_KEY.' });
            return;
        }
        const messages = [
            ...(opCtx ? [{ role: 'system', content: opCtx }] : []),
            ...this._history
        ];
        const res = await fetch('https://api.deepseek.com/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
            body: JSON.stringify({ model: 'deepseek-chat', messages, stream: true })
        });
        const reader = res.body!.getReader();
        const dec = new TextDecoder();
        let full = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            for (const line of dec.decode(value).split('\n')) {
                if (!line.startsWith('data: ') || line.includes('[DONE]')) continue;
                try {
                    const chunk = JSON.parse(line.slice(6)).choices?.[0]?.delta?.content;
                    if (chunk) { full += chunk; this._panel.webview.postMessage({ type: 'chunk', text: chunk }); }
                } catch { /* skip malformed */ }
            }
        }
        this._history.push({ role: 'assistant', content: full });
        this._panel.webview.postMessage({ type: 'done' });
    }

    private _buildHtml(): string {
        const n = nonce();
        const htmlPath = path.join(this._extPath, 'media', 'chat.html');
        return fs.readFileSync(htmlPath, 'utf-8')
            .replace(/\$\{nonce\}/g, n)
            .replace(/\$\{csp\}/g, `default-src 'none'; script-src 'nonce-${n}'; style-src 'unsafe-inline';`);
    }

    dispose() {
        PigeonChatPanel.current = undefined;
        this._panel.dispose();
        this._disposables.forEach(d => d.dispose());
    }
}

// ── Activation ───────────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext) {
    const root = getRoot();

    // Background telemetry — starts immediately, no panel needed
    if (root) {
        const bg = new BackgroundTelemetry(root);
        bg.start(context);
    }

    // Chat panel — optional, on-demand
    context.subscriptions.push(
        vscode.commands.registerCommand('pigeon.openChat', () =>
            PigeonChatPanel.createOrShow(context))
    );
}

export function deactivate() {}
