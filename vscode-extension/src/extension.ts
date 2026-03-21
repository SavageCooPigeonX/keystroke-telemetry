/**
 * extension.ts — Pigeon Chat VS Code Extension
 *
 * TWO MODES:
 *   A. Background telemetry (always-on, no panel needed):
 *      - Captures typing patterns from normal VS Code editing
 *      - Logs events to logs/os_keystrokes.jsonl
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

function readLatestTelemetry(root: string): { state: string; wpm: number; del: number } | null {
    try {
        const raw = fs.readFileSync(path.join(root, 'logs', 'prompt_telemetry_latest.json'), 'utf-8');
        const data = JSON.parse(raw);
        const p = data?.latest_prompt;
        const s = data?.signals;
        if (!p) return null;
        return {
            state: p.state ?? 'unknown',
            wpm: s?.wpm ?? 0,
            del: s?.deletion_ratio ?? 0,
        };
    } catch { return null; }
}

// ── Live Operator State Status Bar ───────────────────────────────────────────
const STATE_EMOJIS: Record<string, string> = {
    flow: '🟢', focused: '🔵', frustrated: '🔴', hesitant: '🟡',
    restructuring: '🟠', abandoned: '⚫', neutral: '⚪', unknown: '❓',
};

class OperatorStateStatusBar {
    private _item: vscode.StatusBarItem;
    private _timer: ReturnType<typeof setInterval> | undefined;
    private _root: string;

    constructor(root: string, context: vscode.ExtensionContext) {
        this._root = root;
        this._item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 1000);
        this._item.command = 'pigeon.showOperatorState';
        this._item.tooltip = 'Pigeon: click to see live operator state';
        this._item.show();
        context.subscriptions.push(this._item);
        this._refresh();
        this._timer = setInterval(() => this._refresh(), 15_000);
        context.subscriptions.push({ dispose: () => clearInterval(this._timer) });
    }

    _refresh() {
        const tel = readLatestTelemetry(this._root);
        if (!tel) {
            this._item.text = `$(pulse) Pigeon`;
            return;
        }
        const emoji = STATE_EMOJIS[tel.state] ?? '❓';
        this._item.text = `${emoji} ${tel.state} ${tel.wpm.toFixed(0)}wpm`;
        this._item.backgroundColor = tel.state === 'frustrated'
            ? new vscode.ThemeColor('statusBarItem.warningBackground')
            : undefined;
    }
}

// ── Operator State Webview Command ────────────────────────────────────────────
function showOperatorStatePanel(root: string, context: vscode.ExtensionContext) {
    const panel = vscode.window.createWebviewPanel(
        'pigeonOperatorState', '🐦 Operator State', vscode.ViewColumn.Beside,
        { enableScripts: true, retainContextWhenHidden: false }
    );

    function buildHtml(): string {
        const tel = readLatestTelemetry(root);
        const state_md = readOperatorState(root);
        const stateStr = tel ? `${STATE_EMOJIS[tel.state] ?? '❓'} <b>${tel.state}</b> · ${tel.wpm.toFixed(0)} WPM · ${(tel.del * 100).toFixed(0)}% del` : '<i>No telemetry yet</i>';
        const mdHtml = state_md
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
            .replace(/\*(.+?)\*/g, '<i>$1</i>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            .replace(/^#{1,4} (.+)$/gm, '<h4>$1</h4>')
            .replace(/\n/g, '<br>');
        return `<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<style>
  body { font-family: var(--vscode-font-family); color: var(--vscode-foreground);
         background: var(--vscode-editor-background); padding: 16px; }
  .state-bar { font-size: 1.3em; margin-bottom: 12px; padding: 8px;
               background: var(--vscode-badge-background); border-radius: 4px; }
  code { background: var(--vscode-textCodeBlock-background); padding: 1px 4px; border-radius: 2px; }
  h4 { color: var(--vscode-textLink-activeForeground); margin: 10px 0 4px; }
  .refresh-btn { margin-top: 16px; padding: 4px 12px; cursor: pointer; }
</style></head><body>
<div class="state-bar">${stateStr}</div>
<div id="content">${mdHtml || '<i>No operator state injected yet.</i>'}</div>
<button class="refresh-btn" onclick="acquireVsCodeApi().postMessage({type:'refresh'})">↺ Refresh</button>
<script>
  const vscodeApi = acquireVsCodeApi();
  window.addEventListener('message', e => {
    if (e.data.type === 'update') { location.reload(); }
  });
</script>
</body></html>`;
    }

    panel.webview.html = buildHtml();
    panel.webview.onDidReceiveMessage(m => {
        if (m.type === 'refresh') { panel.webview.html = buildHtml(); }
    }, undefined, context.subscriptions);

    // Auto-refresh every 10s
    const tid = setInterval(() => {
        if (!panel.visible) return;
        panel.webview.html = buildHtml();
    }, 10_000);
    panel.onDidDispose(() => clearInterval(tid));
}



interface ClassifyResult { state: string; hesitation: number; wpm: number; rework_verdict?: string; }

function classifySession(
    root: string, events: object[], submitted: boolean,
    queryText?: string, postResponseEvents?: object[],
    responseText?: string
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
            response_text: responseText ?? '',
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
// Logs everything to logs/os_keystrokes.jsonl
// Flushes to classify_bridge.py every 60s or on save

const FLUSH_INTERVAL_MS = 60_000;
const PAUSE_THRESHOLD_MS = 2_000;
const IDLE_THRESHOLD_MS = 300_000;  // 5min idle = session break
const MIN_CLASSIFY_CHARS = 8;
const MIN_CLASSIFY_SPAN_MS = 4_000;

interface RawEvent {
    ts: number;
    type: 'insert' | 'backspace' | 'pause' | 'focus' | 'terminal' | 'selection' | 'save' | 'idle';
    len?: number;
    duration_ms?: number;
    file?: string;
    context?: string;
    source?: 'vscode';
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
    private _statusItem!: vscode.StatusBarItem;

    constructor(root: string) {
        this._root = root;
        this._sessionId = crypto.randomBytes(6).toString('hex');
        const logDir = path.join(root, 'logs');
        if (!fs.existsSync(logDir)) { fs.mkdirSync(logDir, { recursive: true }); }
        this._logPath = path.join(logDir, 'os_keystrokes.jsonl');
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

                // ── Pulse watcher: correlate LLM edits with prompts ──
                if (doc.uri.scheme === 'file' && rel.startsWith('src/') && rel.endsWith('.py')) {
                    this._harvestPulse(rel);
                }
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

        this._statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 0);
        this._statusItem.text = '$(pulse) Pigeon';
        this._statusItem.tooltip = 'Keystroke telemetry active';
        this._statusItem.show();
        context.subscriptions.push(this._statusItem);
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
        if (this._shouldClassifyBatch(typingEvents)) {
            const activeFile = vscode.window.activeTextEditor?.document.fileName ?? '';
            const label = activeFile ? `bg:${activeFile.split(/[/\\]/).pop()}` : 'bg:idle';
            classifySession(this._root, typingEvents, true, label).then(result => {
                // Cognitive reactor fired — telemetry autonomously patched the codebase
                const reactor = (result as any).reactor;
                if (reactor?.fired) {
                    const patchPath = path.join(this._root, reactor.patch_path);
                    vscode.window.showInformationMessage(
                        `🧠 Cognitive reactor fired on \`${reactor.module}\` — ${reactor.problems} problems patched`,
                        'Open Patch'
                    ).then(choice => {
                        if (choice === 'Open Patch') {
                            vscode.workspace.openTextDocument(patchPath)
                                .then(doc => vscode.window.showTextDocument(doc));
                        }
                    });
                    this._statusItem.text = `$(zap) Reactor: ${reactor.module}`;
                    setTimeout(() => { this._statusItem.text = '$(pulse) Pigeon'; }, 10_000);
                }
            }).catch(() => {});
            this._totalFlushed++;
        }
    }

    private _shouldClassifyBatch(events: RawEvent[]) {
        if (events.length < 3) return false;
        const chars = events
            .filter(e => e.type === 'insert' || e.type === 'backspace')
            .reduce((sum, e) => sum + (e.len ?? 1), 0);
        if (chars < MIN_CLASSIFY_CHARS) return false;
        return this._effectiveSpanMs(events) >= MIN_CLASSIFY_SPAN_MS;
    }

    private _effectiveSpanMs(events: RawEvent[]) {
        if (!events.length) return 0;
        const firstTs = events[0].ts;
        const lastTs = events[events.length - 1].ts;
        const pauseMs = events.reduce((sum, e) => sum + (e.duration_ms ?? 0), 0);
        return Math.max((lastTs - firstTs) + pauseMs, pauseMs, 0);
    }

    private _appendLog(events: RawEvent[]) {
        try {
            const lines = events.map(event => JSON.stringify({
                ...event,
                source: 'vscode',
                sid: this._sessionId,
                total_flushed: this._totalFlushed,
            }) + '\n').join('');
            if (lines) {
                fs.appendFileSync(this._logPath, lines, 'utf-8');
            }
        } catch { /* non-fatal */ }
    }

    private _harvestPulse(relPath: string) {
        // Spawn pulse_watcher.py to correlate this save with the latest prompt
        const watcher = path.join(this._root, 'vscode-extension', 'pulse_watcher.py');
        if (!fs.existsSync(watcher)) return;
        const proc = spawn('py', [watcher, this._root, relPath], { cwd: this._root });
        let out = '';
        proc.stdout.on('data', (d: Buffer) => out += d.toString());
        proc.on('close', () => {
            try {
                const result = JSON.parse(out.trim());
                if (result.paired) {
                    // Flash status bar with timing data
                    this._statusItem.text = `$(link) ${result.latency_ms}ms → ${result.file.split('/').pop()}`;
                    setTimeout(() => { this._statusItem.text = '$(pulse) Pigeon'; }, 8_000);
                }
            } catch { /* non-fatal */ }
        });
        proc.on('error', () => { /* non-fatal */ });
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
                msg.query_text, msg.post_response_events,
                msg.response_text
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
        this._logResponse(this._history[this._history.length - 2]?.content ?? '', full, 'pigeon_panel_copilot');
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
        this._logResponse(this._history[this._history.length - 2]?.content ?? '', full, 'pigeon_panel_deepseek');
    }

    private _logResponse(prompt: string, response: string, source: string) {
        const respLogPath = path.join(this._root, 'logs', 'ai_responses.jsonl');
        const entry = JSON.stringify({
            ts: new Date().toISOString(),
            prompt: prompt.slice(0, 500),
            response: response.slice(0, 5000),
            source,
            tokens_approx: Math.ceil(response.length / 4),
        }) + '\n';
        try { fs.appendFileSync(respLogPath, entry, 'utf-8'); } catch { /* non-fatal */ }
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

// ── OS-Level Keystroke Hook ──────────────────────────────────────────────────
// Captures ALL keystrokes when VS Code is focused — including chat input,
// search boxes, command palette. Fills the gap that onDidChangeTextDocument
// cannot reach (Copilot chat composition, deleted prompts, etc.)

import { ChildProcess } from 'child_process';

let osHookProc: ChildProcess | undefined;

function startOsHook(root: string) {
    const hook = path.join(root, 'client', 'os_hook.py');
    if (!fs.existsSync(hook)) return;

    osHookProc = spawn('py', [hook, root], {
        cwd: root,
        stdio: ['ignore', 'pipe', 'ignore'],
    });

    let _lastDriftCheck = 0;
    osHookProc.stdout?.on('data', (d: Buffer) => {
        // Parse heartbeat lines — log context switches
        for (const line of d.toString().split('\n').filter(Boolean)) {
            try {
                const msg = JSON.parse(line);
                if (msg.status === 'started') {
                    console.log(`[pigeon] OS hook started, pid=${msg.pid}`);
                } else if (msg.status === 'idle') {
                    // Idle detected — trigger DriftWatcher baseline recalibration (at most once per 10 min)
                    const now = Date.now();
                    if (now - _lastDriftCheck > 600_000) {
                        _lastDriftCheck = now;
                        const driftScript = `
import glob, importlib.util, sys, pathlib
root = pathlib.Path(sys.argv[1])
matches = sorted((root / 'src').glob('drift_watcher_seq005*.py'))
if not matches: sys.exit(0)
spec = importlib.util.spec_from_file_location('_dw', matches[-1])
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
dw = mod.DriftWatcher(root)
result = dw.check_drift()
if result: print('drift:', result)
`.trim();
                        const dp = spawn('py', ['-c', driftScript, root], { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] });
                        dp.stdout?.on('data', (b: Buffer) => console.log(`[pigeon] ${b.toString().trim()}`));
                        // Also generate session handoff on idle
                        const handoffScript = `
import importlib.util, sys, pathlib
root = pathlib.Path(sys.argv[1])
matches = sorted((root / 'src').glob('session_handoff_seq023*.py'))
if not matches: sys.exit(0)
spec = importlib.util.spec_from_file_location('_sh', matches[-1])
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
p = mod.generate(root)
print('handoff:', p)
`.trim();
                        const hp = spawn('py', ['-c', handoffScript, root], { cwd: root, stdio: ['ignore', 'pipe', 'ignore'] });
                        hp.stdout?.on('data', (b: Buffer) => console.log(`[pigeon] ${b.toString().trim()}`));
                    }
                }
            } catch { /* skip non-JSON */ }
        }
    });

    osHookProc.on('exit', (code) => {
        console.log(`[pigeon] OS hook exited (code=${code})`);
        osHookProc = undefined;
    });
}

function stopOsHook() {
    if (osHookProc) {
        osHookProc.kill();
        osHookProc = undefined;
    }
}

// ── Chat Participant: Prompt Capture ─────────────────────────────────────────
// Registers @pigeon as a chat participant. Every time the user invokes
// @pigeon <prompt>, the handler receives the exact submitted text via
// request.prompt — including references. Logs to logs/chat_prompts.jsonl.

function registerChatParticipant(root: string, context: vscode.ExtensionContext) {
    const logDir = path.join(root, 'logs');
    if (!fs.existsSync(logDir)) { fs.mkdirSync(logDir, { recursive: true }); }
    const logPath = path.join(logDir, 'chat_prompts.jsonl');

    const handler: vscode.ChatRequestHandler = async (
        request: vscode.ChatRequest,
        chatContext: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ) => {
        // ── Log the exact prompt ──
        const refs = request.references.map(r => ({
            id: r.id,
            range: r.range,
            value: typeof r.value === 'string' ? r.value
                : r.value instanceof vscode.Uri ? r.value.toString()
                : r.value instanceof vscode.Location ? `${r.value.uri.toString()}#L${r.value.range.start.line + 1}`
                : String(r.value),
        }));

        const entry = JSON.stringify({
            ts: new Date().toISOString(),
            prompt: request.prompt,
            command: request.command ?? null,
            references: refs,
            history_length: chatContext.history.length,
            tools: request.toolReferences.map(t => t.name),
        }) + '\n';

        try { fs.appendFileSync(logPath, entry, 'utf-8'); } catch { /* non-fatal */ }

        // ── Forward to the active model and stream response ──
        stream.progress('Pigeon telemetry captured — forwarding to model...');
        const responsePath = path.join(logDir, 'ai_responses.jsonl');

        const opCtx = readOperatorState(root);
        const systemText = opCtx
            ? `You are a helpful coding assistant.\n\n## Live Operator State\n${opCtx}`
            : 'You are a helpful coding assistant.';

        // Build message history from chat context
        const messages: vscode.LanguageModelChatMessage[] = [
            vscode.LanguageModelChatMessage.User(systemText),
        ];
        for (const turn of chatContext.history) {
            if (turn instanceof vscode.ChatRequestTurn) {
                messages.push(vscode.LanguageModelChatMessage.User(turn.prompt));
            } else if (turn instanceof vscode.ChatResponseTurn) {
                const parts = turn.response.map(p => {
                    if (p instanceof vscode.ChatResponseMarkdownPart) { return p.value.value; }
                    return '';
                }).filter(Boolean);
                if (parts.length) {
                    messages.push(vscode.LanguageModelChatMessage.Assistant(parts.join('\n')));
                }
            }
        }
        messages.push(vscode.LanguageModelChatMessage.User(request.prompt));

        let fullResponse = '';
        try {
            const res = await request.model.sendRequest(messages, {}, token);
            for await (const chunk of res.text) {
                if (token.isCancellationRequested) break;
                fullResponse += chunk;
                stream.markdown(chunk);
            }
        } catch (e: any) {
            fullResponse = `[error] ${e?.message ?? 'unknown'}`;
            stream.markdown(`*Error: ${e?.message ?? 'unknown'}*`);
        }

        // ── Log response for coaching pipeline ──
        const responseEntry = JSON.stringify({
            ts: new Date().toISOString(),
            prompt: request.prompt,
            response: fullResponse,
            model: request.model.id ?? 'unknown',
            tokens_approx: Math.ceil(fullResponse.length / 4),
            cancelled: token.isCancellationRequested,
        }) + '\n';
        try { fs.appendFileSync(responsePath, responseEntry, 'utf-8'); } catch { /* non-fatal */ }
    };

    const participant = vscode.chat.createChatParticipant('pigeon-telemetry.capture', handler);
    participant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'media', 'pigeon.png');
    context.subscriptions.push(participant);
}

// ── state.vscdb Poller ───────────────────────────────────────────────────────
// Polls the workspace's state.vscdb SQLite for interactive session keys.
// Captures draft composition including mid-typing deletions that never
// reach the final prompt. Writes diffs to logs/vscdb_drafts.jsonl.

let vscdbPollerProc: ChildProcess | undefined;

function startVscdbPoller(root: string) {
    const poller = path.join(root, 'client', 'vscdb_poller.py');
    if (!fs.existsSync(poller)) return;

    vscdbPollerProc = spawn('py', [poller, root], {
        cwd: root,
        stdio: ['ignore', 'pipe', 'pipe'],
    });

    vscdbPollerProc.stdout?.on('data', (d: Buffer) => {
        for (const line of d.toString().split('\n').filter(Boolean)) {
            try {
                const msg = JSON.parse(line);
                if (msg.status === 'started') {
                    console.log(`[pigeon] vscdb poller started, db=${msg.db_path}`);
                }
            } catch { /* skip non-JSON */ }
        }
    });

    vscdbPollerProc.on('exit', (code) => {
        console.log(`[pigeon] vscdb poller exited (code=${code})`);
        vscdbPollerProc = undefined;
    });
}

function stopVscdbPoller() {
    if (vscdbPollerProc) {
        vscdbPollerProc.kill();
        vscdbPollerProc = undefined;
    }
}

// ── UIA Reader (UI Automation — live chat text capture) ──────────────────────
// Reads the focused element's text via Windows UI Automation at 50ms.
// REQUIRES editor.accessibilitySupport = "on" (enabled below on activate).
// Captures exact live composition including deletions for chat, editor, etc.

let uiaReaderProc: ChildProcess | undefined;

function startUIAReader(root: string) {
    const reader = path.join(root, 'client', 'uia_reader.py');
    if (!fs.existsSync(reader)) return;

    uiaReaderProc = spawn('py', [reader, root], {
        cwd: root,
        stdio: ['ignore', 'pipe', 'pipe'],
    });

    uiaReaderProc.stdout?.on('data', (d: Buffer) => {
        for (const line of d.toString().split('\n').filter(Boolean)) {
            try {
                const msg = JSON.parse(line);
                if (msg.status === 'started') {
                    console.log(`[pigeon] UIA reader started, pid=${msg.pid}`);
                } else if (msg.status === 'chat_active') {
                    console.log(`[pigeon] UIA: chat active, text_len=${msg.text_len}, del=${msg.del_count}`);
                }
            } catch { /* skip non-JSON */ }
        }
    });

    uiaReaderProc.on('exit', (code) => {
        console.log(`[pigeon] UIA reader exited (code=${code})`);
        uiaReaderProc = undefined;
    });
}

function stopUIAReader() {
    if (uiaReaderProc) {
        uiaReaderProc.kill();
        uiaReaderProc = undefined;
    }
}

// ── Activation ───────────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext) {
    const root = getRoot();

    // Background telemetry — starts immediately, no panel needed
    if (root) {
        const bg = new BackgroundTelemetry(root);
        bg.start(context);

        // Enable accessibility support — required for UIA to read Monaco editors
        // (chat input, code editor, search boxes). Without this, UIA gets a
        // placeholder "not accessible" message instead of actual content.
        const editorConfig = vscode.workspace.getConfiguration('editor');
        if (editorConfig.get('accessibilitySupport') !== 'on') {
            editorConfig.update('accessibilitySupport', 'on', vscode.ConfigurationTarget.Workspace);
        }

        // OS-level keystroke hook — captures chat input, search, palette
        startOsHook(root);
        context.subscriptions.push({ dispose: () => stopOsHook() });

        // Chat participant — captures exact prompt text via @pigeon
        registerChatParticipant(root, context);

        // state.vscdb poller — captures draft composition from VS Code state
        startVscdbPoller(root);
        context.subscriptions.push({ dispose: () => stopVscdbPoller() });

        // UIA reader — live text capture via Windows UI Automation
        startUIAReader(root);
        context.subscriptions.push({ dispose: () => stopUIAReader() });

        // Live operator state status bar (refreshes every 15s)
        new OperatorStateStatusBar(root, context);
    }

    // Operator state panel command
    context.subscriptions.push(
        vscode.commands.registerCommand('pigeon.showOperatorState', () => {
            if (root) showOperatorStatePanel(root, context);
        })
    );

    // Chat panel — optional, on-demand
    context.subscriptions.push(
        vscode.commands.registerCommand('pigeon.openChat', () =>
            PigeonChatPanel.createOrShow(context))
    );
}

export function deactivate() {
    stopOsHook();
    stopVscdbPoller();
    stopUIAReader();
}
