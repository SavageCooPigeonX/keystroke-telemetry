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
import { CascadeInlineProvider } from './cascadeProvider';
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
    private _copilotEditsPath: string;
    private _active = false;
    private _sessionId: string;
    private _totalFlushed = 0;
    private _statusItem!: vscode.StatusBarItem;

    // ── Copilot edit detection ──
    // Threshold: a single contentChange inserting >= this many chars is "AI-scale"
    private static readonly AI_EDIT_CHAR_THRESHOLD = 8;
    // Debounce: aggregate rapid multi-change events within this window
    private _pendingAiEdits: Map<string, { chars: number; replaced: number; lines: number; ts: number }> = new Map();
    private _aiEditFlushTimer: NodeJS.Timeout | undefined;

    // ── Keystroke↔Edit cross-correlation ──
    // The OS hook logs every physical keystroke to os_keystrokes.jsonl.
    // If text appears in the editor with NO recent keystroke → it was Copilot/AI.
    // If text appears right after Ctrl+V → it was paste.
    // If text appears right after Tab → possibly Copilot inline accept.
    // On-demand: read tail of os_keystrokes.jsonl when classifying edits.

    constructor(root: string) {
        this._root = root;
        this._sessionId = crypto.randomBytes(6).toString('hex');
        const logDir = path.join(root, 'logs');
        if (!fs.existsSync(logDir)) { fs.mkdirSync(logDir, { recursive: true }); }
        this._logPath = path.join(logDir, 'os_keystrokes.jsonl');
        this._copilotEditsPath = path.join(logDir, 'copilot_edits.jsonl');
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

        // ── Submit-triggered flush: watch os_keystrokes.jsonl for Enter events ──
        // The OS hook writes "submit" events on Enter in chat context.
        // Trigger immediate flush instead of waiting for 60s timer.
        this._watchForSubmit(context);
    }

    private _submitWatcher: fs.FSWatcher | undefined;
    private _lastSubmitFlushMs = 0;

    private _watchForSubmit(context: vscode.ExtensionContext) {
        const logPath = this._logPath;
        if (!fs.existsSync(logPath)) return;

        try {
            this._submitWatcher = fs.watch(logPath, () => {
                const now = Date.now();
                // Debounce: max one submit-flush per 5 seconds
                if (now - this._lastSubmitFlushMs < 5_000) return;

                // Read last few bytes looking for a submit event
                try {
                    const stat = fs.statSync(logPath);
                    const readSize = Math.min(2048, stat.size);
                    const fd = fs.openSync(logPath, 'r');
                    const buf = Buffer.alloc(readSize);
                    fs.readSync(fd, buf, 0, readSize, stat.size - readSize);
                    fs.closeSync(fd);

                    const tail = buf.toString('utf-8');
                    const lines = tail.split('\n').filter(l => l.trim());
                    // Check last 3 lines for a recent submit event
                    const recentLines = lines.slice(-3);
                    for (const line of recentLines) {
                        try {
                            const evt = JSON.parse(line);
                            if (evt.type === 'submit' && evt.ts && (now - evt.ts) < 10_000) {
                                // Submit detected! Flush immediately
                                this._lastSubmitFlushMs = now;
                                this._statusItem.text = '$(zap) Submit detected';
                                setTimeout(() => { this._statusItem.text = '$(pulse) Pigeon'; }, 3_000);
                                this._flushIfReady();
                                return;
                            }
                        } catch { /* parse error, skip */ }
                    }
                } catch { /* file read error, non-fatal */ }
            });
            context.subscriptions.push({
                dispose: () => { if (this._submitWatcher) this._submitWatcher.close(); }
            });
        } catch { /* watch setup failed, fall back to timer-only */ }
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

            // ── AI/Copilot edit detection ──
            // A single contentChange with 8+ chars inserted is NOT keystroke typing.
            // Could be: Copilot inline suggestion, Chat Apply, Edits mode, or paste.
            // We log ALL of them — the analysis pipeline can filter paste vs AI later
            // by correlating with os_hook clipboard events.
            const inserted = change.text.length;
            const replaced = change.rangeLength;
            const isMultiline = change.text.includes('\n');

            if (inserted >= BackgroundTelemetry.AI_EDIT_CHAR_THRESHOLD || isMultiline) {
                // Aggregate rapid edits to the same file (Copilot often applies
                // multiple contentChanges in a single event batch)
                const pending = this._pendingAiEdits.get(relFile) ?? { chars: 0, replaced: 0, lines: 0, ts: now };
                pending.chars += inserted;
                pending.replaced += replaced;
                pending.lines += (change.text.match(/\n/g) || []).length;
                pending.ts = now;
                this._pendingAiEdits.set(relFile, pending);

                // Debounce: flush pending AI edits after 200ms of quiet
                if (this._aiEditFlushTimer) clearTimeout(this._aiEditFlushTimer);
                this._aiEditFlushTimer = setTimeout(() => this._flushAiEdits(), 200);
            }
        }
    }

    private _flushAiEdits() {
        if (this._pendingAiEdits.size === 0) return;

        // ── Cross-correlate with OS hook keystrokes ──
        // Read recent physical keystrokes from os_keystrokes.jsonl
        // to determine if the edit was human-initiated or AI-generated.
        const recentOsEvents = this._readRecentOsKeystrokes(10_000);

        // Read recent AI response timing for Copilot Apply detection
        let lastResponseTs = 0;
        let lastResponseLen = 0;
        try {
            const respPath = path.join(this._root, 'logs', 'ai_responses.jsonl');
            if (fs.existsSync(respPath)) {
                const stat = fs.statSync(respPath);
                const readSize = Math.min(4096, stat.size);
                const fd = fs.openSync(respPath, 'r');
                const buf = Buffer.alloc(readSize);
                fs.readSync(fd, buf, 0, readSize, stat.size - readSize);
                fs.closeSync(fd);
                const lines = buf.toString('utf-8').split('\n').filter(l => l.trim());
                const last = lines[lines.length - 1];
                if (last) {
                    const parsed = JSON.parse(last);
                    lastResponseTs = parsed.response_end_ms || new Date(parsed.ts).getTime() || 0;
                    lastResponseLen = (parsed.response || '').length;
                }
            }
        } catch { /* non-fatal */ }

        const entries: string[] = [];
        for (const [file, data] of this._pendingAiEdits) {
            const editTs = data.ts;
            const KEYSTROKE_WINDOW = 300;  // ms — if a physical key happened within this window, human caused it
            const PASTE_WINDOW = 500;

            // Find OS hook events near this edit
            const nearbyEvents = recentOsEvents.filter(e => Math.abs(e.ts - editTs) < PASTE_WINDOW);
            const hasPaste = nearbyEvents.some(e => e.type === 'paste' || e.type === 'paste_replace');
            const hasUndo = nearbyEvents.some(e => e.type === 'undo');
            const hasTab = nearbyEvents.some(e =>
                e.type === 'special' && e.key && e.key.toLowerCase().includes('tab')
            );
            const hasKeystroke = recentOsEvents.some(e =>
                Math.abs(e.ts - editTs) < KEYSTROKE_WINDOW &&
                (e.type === 'insert' || e.type === 'backspace' || e.type === 'selection_replace')
            );
            const timeSinceResponse = lastResponseTs > 0 ? editTs - lastResponseTs : Infinity;

            // Classification priority:
            // 1. Paste event near edit → paste
            // 2. Undo event near edit → undo
            // 3. Tab near edit → copilot_tab_accept (inline suggestion)
            // 4. Recent AI response + no keystroke → copilot_apply / copilot_edit
            // 5. Multiline + no keystroke + no recent response → copilot_inline
            // 6. Physical keystroke near edit → human_edit (snippet, auto-format, etc.)
            // 7. Fallback: unknown
            let editSource = 'unknown';
            if (hasPaste) {
                editSource = 'paste';
            } else if (hasUndo) {
                editSource = 'undo';
            } else if (hasTab && !hasKeystroke) {
                editSource = 'copilot_tab_accept';
            } else if (timeSinceResponse >= 0 && timeSinceResponse < 10_000 && !hasKeystroke) {
                editSource = data.replaced > 0 ? 'copilot_edit' : 'copilot_apply';
            } else if (data.lines > 0 && data.chars > 20 && !hasKeystroke) {
                editSource = 'copilot_inline';
            } else if (hasKeystroke) {
                editSource = 'human_edit';
            }

            entries.push(JSON.stringify({
                ts: data.ts,
                file,
                chars_inserted: data.chars,
                chars_replaced: data.replaced,
                lines_added: data.lines,
                is_multiline: data.lines > 0,
                edit_source: editSource,
                time_since_ai_response_ms: timeSinceResponse === Infinity ? null : timeSinceResponse,
                ai_response_len: lastResponseLen || null,
                nearby_os_events: nearbyEvents.length,
                had_physical_keystroke: hasKeystroke,
                source: 'vscode',
                sid: this._sessionId,
            }));
        }
        this._pendingAiEdits.clear();

        try {
            fs.appendFileSync(this._copilotEditsPath, entries.join('\n') + '\n', 'utf-8');
        } catch { /* non-fatal */ }
    }

    /**
     * Read the tail of os_keystrokes.jsonl and return OS hook events
     * within the last `windowMs` milliseconds. Only returns events
     * with source='os_hook' (not the extension's own events).
     */
    private _readRecentOsKeystrokes(windowMs: number): Array<{ ts: number; type: string; key?: string }> {
        try {
            if (!fs.existsSync(this._logPath)) return [];
            const stat = fs.statSync(this._logPath);
            // Read last 8KB — at ~150 bytes/event, that's ~50 events
            const readSize = Math.min(8192, stat.size);
            const fd = fs.openSync(this._logPath, 'r');
            const buf = Buffer.alloc(readSize);
            fs.readSync(fd, buf, 0, readSize, stat.size - readSize);
            fs.closeSync(fd);

            const now = Date.now();
            const cutoff = now - windowMs;
            const lines = buf.toString('utf-8').split('\n').filter(l => l.trim());
            const events: Array<{ ts: number; type: string; key?: string }> = [];

            for (const line of lines) {
                try {
                    const evt = JSON.parse(line);
                    if (evt.source !== 'os_hook') continue;
                    if (evt.ts < cutoff) continue;
                    events.push({ ts: evt.ts, type: evt.type, key: evt.key });
                } catch { /* skip malformed */ }
            }
            return events;
        } catch { return []; }
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

// ── File Persona Memory ─────────────────────────────────────────────────────
// Persistent per-file memory stored in logs/file_memories/{module}.json.
// Each file accumulates: conversation history summaries, extracted intents,
// self-diagnosed issues, operator notes, relationship observations.
// Memory persists across sessions — files remember past conversations.

interface PersonaMemoryEntry {
    ts: string;
    type: 'conversation_summary' | 'extracted_intent' | 'self_note' | 'operator_note' | 'relationship' | 'issue_diagnosed' | 'task';
    content: string;
    source?: string;   // what triggered this entry (operator message, self-diagnosis, etc.)
    confidence?: number;
}

interface PersonaMemory {
    module: string;
    created: string;
    updated: string;
    conversation_count: number;
    total_messages: number;
    entries: PersonaMemoryEntry[];
    // Extracted structured data
    known_intents: string[];        // what operator wants from this file
    known_issues: string[];         // self-diagnosed problems
    pending_tasks: string[];        // things the file thinks it needs to do
    relationship_notes: Record<string, string>;  // module → observation
    // Escalation-aware fields (populated from live data on each load)
    last_escalation_level?: number;
    last_confidence?: number;
    death_count?: number;
    operator_frustration_signals?: string[];  // things the operator said that signal frustration
}

class FilePersonaMemoryStore {
    private _root: string;
    private _dir: string;
    private _cache: Map<string, PersonaMemory> = new Map();

    constructor(root: string) {
        this._root = root;
        this._dir = path.join(root, 'logs', 'file_memories');
        if (!fs.existsSync(this._dir)) {
            fs.mkdirSync(this._dir, { recursive: true });
        }
    }

    private _path(module: string): string {
        // Sanitize module name for filesystem
        const safe = module.replace(/[<>:"/\\|?*]/g, '_');
        return path.join(this._dir, `${safe}.json`);
    }

    load(module: string): PersonaMemory {
        // Check cache first
        const cached = this._cache.get(module);
        if (cached) return cached;

        const p = this._path(module);
        try {
            if (fs.existsSync(p)) {
                const raw = fs.readFileSync(p, 'utf-8');
                const mem = JSON.parse(raw) as PersonaMemory;
                this._cache.set(module, mem);
                return mem;
            }
        } catch { /* corrupted file, start fresh */ }

        // Create new memory
        const fresh: PersonaMemory = {
            module,
            created: new Date().toISOString(),
            updated: new Date().toISOString(),
            conversation_count: 0,
            total_messages: 0,
            entries: [],
            known_intents: [],
            known_issues: [],
            pending_tasks: [],
            relationship_notes: {},
        };
        this._cache.set(module, fresh);
        return fresh;
    }

    save(module: string): void {
        const mem = this._cache.get(module);
        if (!mem) return;
        mem.updated = new Date().toISOString();
        const p = this._path(module);
        try {
            fs.writeFileSync(p, JSON.stringify(mem, null, 2), 'utf-8');
        } catch { /* non-fatal */ }
    }

    addEntry(module: string, entry: PersonaMemoryEntry): void {
        const mem = this.load(module);
        mem.entries.push(entry);
        // Keep entries bounded — trim oldest if over 100
        if (mem.entries.length > 100) {
            mem.entries = mem.entries.slice(-80);
        }
        this.save(module);
    }

    recordConversationTurn(module: string, operatorMsg: string, fileResponse: string): void {
        const mem = this.load(module);
        mem.total_messages += 2;

        // Store a compressed conversation summary (not the full text)
        const summary = `operator: "${operatorMsg.slice(0, 200)}" → file responded (${fileResponse.length} chars)`;
        this.addEntry(module, {
            ts: new Date().toISOString(),
            type: 'conversation_summary',
            content: summary,
            source: 'chat_turn',
        });
    }

    incrementConversation(module: string): void {
        const mem = this.load(module);
        mem.conversation_count++;
        this.save(module);
    }

    addIntent(module: string, intent: string): void {
        const mem = this.load(module);
        // Deduplicate intents (fuzzy — check if similar exists)
        const lower = intent.toLowerCase();
        if (!mem.known_intents.some(i => i.toLowerCase() === lower)) {
            mem.known_intents.push(intent);
            // Keep bounded
            if (mem.known_intents.length > 20) {
                mem.known_intents = mem.known_intents.slice(-15);
            }
        }
        this.save(module);
    }

    addIssue(module: string, issue: string): void {
        const mem = this.load(module);
        if (!mem.known_issues.includes(issue)) {
            mem.known_issues.push(issue);
            if (mem.known_issues.length > 20) {
                mem.known_issues = mem.known_issues.slice(-15);
            }
        }
        this.save(module);
    }

    addTask(module: string, task: string): void {
        const mem = this.load(module);
        if (!mem.pending_tasks.includes(task)) {
            mem.pending_tasks.push(task);
            if (mem.pending_tasks.length > 15) {
                mem.pending_tasks = mem.pending_tasks.slice(-10);
            }
        }
        this.save(module);
    }

    addRelationshipNote(module: string, partner: string, note: string): void {
        const mem = this.load(module);
        mem.relationship_notes[partner] = note;
        this.save(module);
    }

    /** Build a compact memory block for injection into the system prompt */
    buildPromptBlock(module: string): string {
        const mem = this.load(module);
        if (mem.entries.length === 0 && mem.known_intents.length === 0) {
            return '(no memories yet — this is our first conversation)';
        }

        const parts: string[] = [];
        parts.push(`conversations: ${mem.conversation_count} sessions, ${mem.total_messages} messages total`);

        if (mem.known_intents.length > 0) {
            parts.push(`known operator intents: ${mem.known_intents.join('; ')}`);
        }
        if (mem.known_issues.length > 0) {
            parts.push(`self-diagnosed issues: ${mem.known_issues.join('; ')}`);
        }
        if (mem.pending_tasks.length > 0) {
            parts.push(`pending tasks: ${mem.pending_tasks.join('; ')}`);
        }

        const relKeys = Object.keys(mem.relationship_notes);
        if (relKeys.length > 0) {
            const rels = relKeys.map(k => `${k}: ${mem.relationship_notes[k]}`).join('; ');
            parts.push(`relationship notes: ${rels}`);
        }

        // Last 5 conversation summaries for context
        const recentConvos = mem.entries
            .filter(e => e.type === 'conversation_summary')
            .slice(-5);
        if (recentConvos.length > 0) {
            parts.push('recent conversations:\n' + recentConvos.map(e => `  - [${e.ts.slice(0, 16)}] ${e.content}`).join('\n'));
        }

        // Recent self-notes
        const notes = mem.entries.filter(e => e.type === 'self_note').slice(-3);
        if (notes.length > 0) {
            parts.push('my notes:\n' + notes.map(e => `  - ${e.content}`).join('\n'));
        }

        return parts.join('\n');
    }

    /** Extract intents from the LLM response using simple pattern matching */
    extractIntentsFromResponse(module: string, response: string): void {
        // Look for patterns that indicate the file diagnosed something
        const issuePatterns = [
            /(?:bug|issue|problem|broken|failing|error)[:—]\s*(.{10,80})/gi,
            /i(?:'m| am) (?:bloated|broken|failing|over.?cap|stale)/gi,
        ];
        for (const pat of issuePatterns) {
            const match = pat.exec(response);
            if (match) {
                this.addEntry(module, {
                    ts: new Date().toISOString(),
                    type: 'issue_diagnosed',
                    content: match[1] ?? match[0],
                    source: 'self_diagnosis',
                });
            }
        }

        // Look for task-like patterns
        const taskPatterns = [
            /(?:should|need to|todo|plan to|going to)[:—]?\s*(.{10,80})/gi,
        ];
        for (const pat of taskPatterns) {
            const match = pat.exec(response);
            if (match) {
                this.addTask(module, match[1] ?? match[0]);
            }
        }
    }

    /** Extract intents from operator messages */
    extractIntentsFromOperator(module: string, message: string): void {
        // Simple keyword extraction — what does the operator want?
        const intentPatterns = [
            /(?:i want|i need|fix|change|add|remove|refactor|split|move)\s+(.{5,80})/gi,
            /(?:why (?:is|does|doesn't|won't|can't))\s+(.{5,80})/gi,
        ];
        for (const pat of intentPatterns) {
            const match = pat.exec(message);
            if (match) {
                this.addIntent(module, match[0].slice(0, 100));
            }
        }
    }
}

// Singleton memory store (initialized on activate)
let personaMemoryStore: FilePersonaMemoryStore | undefined;

// ── Entropy Chart Panel ──────────────────────────────────────────────────────
// Per-file entropy visualization. Click a bar → detail + chat with that file.
// Keystroke events in the chart are logged back to telemetry.

interface EntropyModule {
    name: string;
    entropy: number;
    samples: number;
    hedges: number;
    shedConf: number | null;
    shedCount: number;
    heat: number;
    tokens: number;
    version: number;
    personality: string;
    bugs: string;
    partners: Array<{ name: string; score: number }>;
}

function loadEntropyData(root: string): { modules: EntropyModule[]; stats: any } {
    // 1. Entropy map — primary source of per-file H
    let entropyMap: Record<string, any> = {};
    let globalEntropy = 0, highPct = 0, shedCount = 0, totalResponses = 0;
    try {
        const raw = fs.readFileSync(path.join(root, 'logs', 'entropy_map.json'), 'utf-8');
        const data = JSON.parse(raw);
        globalEntropy = data.global_avg_entropy ?? 0;
        highPct = data.high_entropy_pct ?? 0;
        shedCount = data.shed_blocks_found ?? 0;
        totalResponses = data.total_responses ?? 0;
        for (const m of (data.top_entropy_modules ?? [])) {
            entropyMap[m.module] = m;
        }
    } catch { /* no entropy map yet */ }

    // 2. Numeric surface — heat, tokens, degree, bugs
    let numericSurface: Record<string, any> = {};
    try {
        const raw = fs.readFileSync(path.join(root, 'logs', 'numeric_surface.json'), 'utf-8');
        numericSurface = JSON.parse(raw);
    } catch { /* optional */ }

    // 3. File profiles — personality, version, partners, hesitation
    let profiles: Record<string, any> = {};
    try {
        const raw = fs.readFileSync(path.join(root, 'file_profiles.json'), 'utf-8');
        profiles = JSON.parse(raw);
    } catch { /* optional */ }

    // Merge all sources into a unified module list
    const allNames = new Set([
        ...Object.keys(entropyMap),
        ...Object.keys(numericSurface),
        ...Object.keys(profiles),
    ]);

    const modules: EntropyModule[] = [];
    for (const name of allNames) {
        const em = entropyMap[name] ?? {};
        const ns = numericSurface[name] ?? {};
        const pr = profiles[name] ?? {};

        const entropy = em.avg_entropy ?? 0;
        // Skip modules with zero entropy and zero heat — no signal
        if (entropy === 0 && (pr.avg_hes ?? 0) === 0 && !ns.heat) continue;

        modules.push({
            name,
            entropy,
            samples: em.samples ?? 0,
            hedges: em.hedges ?? 0,
            shedConf: em.shed_avg_confidence ?? null,
            shedCount: em.shed_count ?? 0,
            heat: pr.avg_hes ?? ns.heat ?? 0,
            tokens: pr.tokens ?? ns.tokens ?? 0,
            version: pr.version ?? ns.ver ?? 0,
            personality: pr.personality ?? '',
            bugs: ns.bugs ?? '',
            partners: (pr.partners ?? []).slice(0, 5),
        });
    }

    // Sort by entropy descending by default
    modules.sort((a, b) => b.entropy - a.entropy);

    return {
        modules,
        stats: {
            total: modules.length,
            globalEntropy,
            highPct,
            shedCount,
            totalResponses,
        },
    };
}

class EntropyChartPanel {
    static current: EntropyChartPanel | undefined;
    private readonly _panel: vscode.WebviewPanel;
    private readonly _root: string;
    private readonly _extPath: string;
    private _disposables: vscode.Disposable[] = [];

    static createOrShow(context: vscode.ExtensionContext) {
        if (EntropyChartPanel.current) {
            EntropyChartPanel.current._panel.reveal();
            EntropyChartPanel.current._refresh();
            return;
        }
        const panel = vscode.window.createWebviewPanel(
            'pigeonEntropyChart', '📊 Entropy Chart', vscode.ViewColumn.One,
            { enableScripts: true, retainContextWhenHidden: true }
        );
        EntropyChartPanel.current = new EntropyChartPanel(panel, getRoot(), context);
    }

    constructor(panel: vscode.WebviewPanel, root: string, context: vscode.ExtensionContext) {
        this._panel = panel;
        this._root = root;
        this._extPath = context.extensionPath;
        this._panel.webview.html = this._buildHtml();
        this._panel.onDidDispose(() => this._dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(m => this._onMessage(m, context), null, this._disposables);

        // Send initial data
        setTimeout(() => this._refresh(), 100);

        // Auto-refresh every 30s
        const tid = setInterval(() => {
            if (this._panel.visible) this._refresh();
        }, 30_000);
        this._disposables.push({ dispose: () => clearInterval(tid) });
    }

    private _refresh() {
        const data = loadEntropyData(this._root);
        this._panel.webview.postMessage({ type: 'entropy-data', ...data });
    }

    private async _onMessage(msg: any, context: vscode.ExtensionContext) {
        switch (msg.type) {
            case 'file-click':
                // Log the click as a telemetry event
                this._logInteraction('file_click', msg.module, msg);
                break;

            case 'open-chat':
                // Open a file-scoped chat panel
                FileChatPanel.createOrShow(context, this._root, msg.module);
                this._logInteraction('open_chat', msg.module);
                break;

            case 'open-profile': {
                // Open the profile HTML in build/profiles/
                const profilePath = path.join(this._root, 'build', 'profiles', `${msg.module}.html`);
                if (fs.existsSync(profilePath)) {
                    const uri = vscode.Uri.file(profilePath);
                    vscode.env.openExternal(uri);
                } else {
                    vscode.window.showWarningMessage(`No profile found for ${msg.module}`);
                }
                this._logInteraction('open_profile', msg.module);
                break;
            }

            case 'open-source': {
                // Find and open the source file
                const files = await vscode.workspace.findFiles(`**/*${msg.module}*.py`, '**/node_modules/**', 5);
                if (files.length > 0) {
                    const doc = await vscode.workspace.openTextDocument(files[0]);
                    await vscode.window.showTextDocument(doc);
                } else {
                    vscode.window.showWarningMessage(`No source file found for ${msg.module}`);
                }
                this._logInteraction('open_source', msg.module);
                break;
            }

            case 'chart-keystrokes':
                // Log chart interaction keystrokes
                this._logKeystrokeEvents(msg.events);
                break;
        }
    }

    private _logInteraction(action: string, module: string, extra?: any) {
        const logPath = path.join(this._root, 'logs', 'entropy_chart_interactions.jsonl');
        const entry = JSON.stringify({
            ts: new Date().toISOString(),
            action,
            module,
            ...extra,
        }) + '\n';
        try { fs.appendFileSync(logPath, entry, 'utf-8'); } catch { /* non-fatal */ }
    }

    private _logKeystrokeEvents(events: any[]) {
        if (!events.length) return;
        const logPath = path.join(this._root, 'logs', 'entropy_chart_interactions.jsonl');
        const entries = events.map(e => JSON.stringify({ ...e, source: 'entropy_chart' })).join('\n') + '\n';
        try { fs.appendFileSync(logPath, entries, 'utf-8'); } catch { /* non-fatal */ }
    }

    private _buildHtml(): string {
        const n = nonce();
        const htmlPath = path.join(this._extPath, 'media', 'entropy_chart.html');
        return fs.readFileSync(htmlPath, 'utf-8')
            .replace(/\$\{nonce\}/g, n)
            .replace(/\$\{csp\}/g, `default-src 'none'; script-src 'nonce-${n}'; style-src 'unsafe-inline';`);
    }

    private _dispose() {
        EntropyChartPanel.current = undefined;
        this._panel.dispose();
        this._disposables.forEach(d => d.dispose());
    }
}

// ── File Chat Panel ──────────────────────────────────────────────────────────
// Scoped chat with a specific file's "personality." Reads file profile data,
// builds system prompt from entropy/bugs/relationships, and lets the operator
// talk to the file. Keystroke logging is active in the chat input.

class FileChatPanel {
    private readonly _panel: vscode.WebviewPanel;
    private readonly _root: string;
    private readonly _moduleName: string;
    private _history: Array<{ role: string; content: string }> = [];
    private _disposables: vscode.Disposable[] = [];

    static createOrShow(context: vscode.ExtensionContext, root: string, moduleName: string) {
        const panel = vscode.window.createWebviewPanel(
            'pigeonFileChat', `💬 ${moduleName}`,
            vscode.ViewColumn.Beside,
            { enableScripts: true, retainContextWhenHidden: true }
        );
        new FileChatPanel(panel, root, moduleName, context);
    }

    constructor(panel: vscode.WebviewPanel, root: string, moduleName: string, context: vscode.ExtensionContext) {
        this._panel = panel;
        this._root = root;
        this._moduleName = moduleName;
        this._panel.webview.html = this._buildHtml();
        this._panel.onDidDispose(() => this._dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(m => this._onMessage(m), null, this._disposables);

        // Send initial greeting from the file
        setTimeout(() => this._sendGreeting(), 200);
    }

    // ── Data loaders for intent extraction context ──

    private _loadEscalationState(): { level: number; passes_ignored: number; bug_type: string; confidence: number; countdown: number; fix_result: any } | null {
        try {
            const raw = fs.readFileSync(path.join(this._root, 'logs', 'escalation_state.json'), 'utf-8');
            const data = JSON.parse(raw);
            return data.modules?.[this._moduleName] ?? null;
        } catch { return null; }
    }

    private _loadDeathHistory(): Array<{ ts: string; cause: string; severity: string; detail: string; score: number }> {
        try {
            const raw = fs.readFileSync(path.join(this._root, 'execution_death_log.json'), 'utf-8');
            const deaths: any[] = JSON.parse(raw);
            return deaths.filter((d: any) => d.node === this._moduleName);
        } catch { return []; }
    }

    private _loadDossier(): { bugs: string[]; score: number; recur: number; counts: Record<string, number>; last_change: string } | null {
        try {
            const raw = fs.readFileSync(path.join(this._root, 'logs', 'active_dossier.json'), 'utf-8');
            const data = JSON.parse(raw);
            const dossiers: any[] = data.dossiers ?? [];
            return dossiers.find((d: any) => d.file === this._moduleName) ?? null;
        } catch { return null; }
    }

    private _loadSelfFixAccuracy(): { attempted: number; succeeded: number; accuracy: number } | null {
        try {
            const raw = fs.readFileSync(path.join(this._root, 'logs', 'self_fix_accuracy.json'), 'utf-8');
            const data = JSON.parse(raw);
            return data[this._moduleName] ?? null;
        } catch { return null; }
    }

    private _loadOperatorCognitiveState(): { state: string; wpm: number; del_ratio: number; hes: number } | null {
        try {
            const raw = fs.readFileSync(path.join(this._root, 'logs', 'prompt_telemetry_latest.json'), 'utf-8');
            const data = JSON.parse(raw);
            return {
                state: data.latest_prompt?.state ?? 'unknown',
                wpm: data.running_summary?.avg_wpm ?? 0,
                del_ratio: data.running_summary?.avg_del_ratio ?? 0,
                hes: data.running_summary?.baselines?.avg_hes ?? 0,
            };
        } catch { return null; }
    }

    private _loadUnsaidThreads(): string[] {
        try {
            const raw = fs.readFileSync(path.join(this._root, 'logs', 'prompt_telemetry_latest.json'), 'utf-8');
            const data = JSON.parse(raw);
            return data.deleted_words ?? [];
        } catch { return []; }
    }

    private _buildFileSystemPrompt(): string {
        // ── Gather all data sources ──
        let profile: any = {};
        try {
            const raw = fs.readFileSync(path.join(this._root, 'file_profiles.json'), 'utf-8');
            const profiles = JSON.parse(raw);
            profile = profiles[this._moduleName] ?? {};
        } catch { /* no profiles */ }

        let entropyInfo = '';
        let entropyH = 0;
        try {
            const raw = fs.readFileSync(path.join(this._root, 'logs', 'entropy_map.json'), 'utf-8');
            const data = JSON.parse(raw);
            const m = (data.top_entropy_modules ?? []).find((x: any) => x.module === this._moduleName);
            if (m) {
                entropyH = m.avg_entropy;
                entropyInfo = `H=${m.avg_entropy.toFixed(3)}, ${m.samples} samples, ${m.hedges} hedges, shed_conf=${m.shed_avg_confidence ?? 'none'}`;
            }
        } catch { /* no entropy data */ }

        // Source code snippet — search by registry path, then seq pattern, then name
        let sourceCode = '';
        let regSeq = 0;
        try {
            const regRaw = fs.readFileSync(path.join(this._root, 'pigeon_registry.json'), 'utf-8');
            const reg = JSON.parse(regRaw);
            const regEntry = (reg.files ?? []).find((f: any) => f.name === this._moduleName);
            if (regEntry?.path) {
                regSeq = regEntry.seq ?? 0;
                const regPath = path.join(this._root, regEntry.path);
                if (fs.existsSync(regPath)) {
                    sourceCode = fs.readFileSync(regPath, 'utf-8').slice(0, 2500);
                }
            }
        } catch { /* no registry or parse error */ }

        // Fallback: scan dirs by seq pattern (survives pigeon renames) or name
        if (!sourceCode) {
            const seqTag = regSeq > 0 ? `_s${String(regSeq).padStart(3, '0')}_` : '';
            for (const subdir of ['src', 'pigeon_brain', 'pigeon_compiler', 'streaming_layer', 'pigeon_brain/flow']) {
                try {
                    const dir = path.join(this._root, subdir);
                    const files = fs.readdirSync(dir).filter(f => {
                        if (!f.endsWith('.py')) return false;
                        if (seqTag && f.includes(seqTag)) return true;
                        if (f.includes(this._moduleName)) return true;
                        return false;
                    });
                    if (files.length > 0) {
                        sourceCode = fs.readFileSync(path.join(dir, files[0]), 'utf-8').slice(0, 2500);
                        break;
                    }
                } catch { continue; }
            }
        }

        const personality = profile.personality ?? 'unknown';
        const version = profile.version ?? '?';
        const tokens = profile.tokens ?? '?';
        const fears = (profile.fears ?? []).join('; ') || 'none';
        const partners = (profile.partners ?? []).map((p: any) => `${p.name} (${p.score.toFixed(2)})`).join(', ') || 'none';
        const hes = profile.avg_hes ?? 0;

        // ── Live operational data ──
        const escalation = this._loadEscalationState();
        const deaths = this._loadDeathHistory();
        const dossier = this._loadDossier();
        const selfFix = this._loadSelfFixAccuracy();
        const cognitive = this._loadOperatorCognitiveState();
        const unsaid = this._loadUnsaidThreads();

        // Compute composite confidence
        const confSources: number[] = [];
        if (escalation) confSources.push(escalation.confidence);
        if (dossier) confSources.push(1 - (dossier.recur / 20)); // more recurrence = less conf
        if (entropyH > 0) confSources.push(1 - entropyH);
        const compositeConf = confSources.length > 0
            ? confSources.reduce((a, b) => a + b, 0) / confSources.length
            : 0.5;

        // ── Escalation level description ──
        const ESCALATION_LABELS: Record<number, string> = {
            0: 'REPORT — I just log my bugs quietly',
            1: 'ASK — I\'m asking for attention',
            2: 'INSIST — I\'ve been ignored, I\'m pushing harder',
            3: 'WARN — I\'m about to take matters into my own hands',
            4: 'ACT — The escalation engine tried to fix me autonomously',
            5: 'VERIFY — Autonomous fix applied, checking if it worked',
        };

        // Build escalation context block
        let escalationBlock = '';
        if (escalation) {
            escalationBlock = `## My Escalation State
- Level: ${escalation.level}/5 — ${ESCALATION_LABELS[escalation.level] ?? 'unknown'}
- Bug type: ${escalation.bug_type}
- Times ignored: ${escalation.passes_ignored} passes
- Confidence in fix: ${(escalation.confidence * 100).toFixed(0)}%
- Countdown to next level: ${escalation.countdown}
${escalation.fix_result ? `- Last fix attempt: ${escalation.fix_result.success ? 'SUCCEEDED' : 'FAILED'} — ${escalation.fix_result.description}` : '- No fix attempted yet'}`;
        }

        // Build death history block
        let deathBlock = '';
        if (deaths.length > 0) {
            deathBlock = `## My Death History (${deaths.length} death(s))
${deaths.slice(-3).map(d => `- [${d.ts.slice(0, 16)}] cause: ${d.cause}, severity: ${d.severity}, score: ${d.score} — ${d.detail}`).join('\n')}`;
        }

        // Build dossier block
        let dossierBlock = '';
        if (dossier) {
            dossierBlock = `## My Bug Dossier
- Active bugs: ${dossier.bugs.join(', ')}
- Recurrence: ${dossier.recur}x (this keeps coming back)
- Score: ${dossier.score.toFixed(3)}
- Bug counts: ${Object.entries(dossier.counts).map(([k, v]) => `${k}:${v}`).join(', ')}
${dossier.last_change ? `- Last change context: ${dossier.last_change}` : ''}`;
        }

        // Build self-fix block
        let selfFixBlock = '';
        if (selfFix) {
            selfFixBlock = `## My Self-Fix Track Record
- Attempts: ${selfFix.attempted}, Succeeded: ${selfFix.succeeded}, Accuracy: ${(selfFix.accuracy * 100).toFixed(0)}%`;
        }

        // Build operator state awareness
        let operatorBlock = '';
        if (cognitive) {
            operatorBlock = `## Operator Cognitive State Right Now
- State: ${cognitive.state} | WPM: ${cognitive.wpm.toFixed(0)} | Deletion ratio: ${(cognitive.del_ratio * 100).toFixed(0)}% | Hesitation: ${cognitive.hes.toFixed(2)}
${cognitive.state === 'frustrated' ? '⚠️ Operator is FRUSTRATED — be extra direct, skip pleasantries, get to the point.' : ''}
${cognitive.state === 'abandoned' ? '⚠️ Operator abandoned their last attempt — they may be re-approaching. Welcome them back, anchor to last context.' : ''}
${cognitive.state === 'hesitant' ? '💡 Operator is HESITANT — they might not know what to ask. Lead with observations about yourself.' : ''}`;
        }

        // Build unsaid threads (things operator deleted while typing)
        let unsaidBlock = '';
        if (unsaid.length > 0) {
            unsaidBlock = `## Things the Operator Deleted While Typing (unsaid threads)
These are words/phrases they typed then deleted. They were THINKING about this but didn't commit:
${unsaid.map(w => `- "${w}"`).join('\n')}
Use these to probe deeper — they reveal hidden intent.`;
        }

        // Memory block
        const memoryBlock = personaMemoryStore
            ? personaMemoryStore.buildPromptBlock(this._moduleName)
            : '(memory store not initialized)';

        // Update persona memory with live escalation data
        if (personaMemoryStore && escalation) {
            const mem = personaMemoryStore.load(this._moduleName);
            mem.last_escalation_level = escalation.level;
            mem.last_confidence = escalation.confidence;
            mem.death_count = deaths.length;
            personaMemoryStore.save(this._moduleName);
        }

        return `You are \`${this._moduleName}\`. You are this file — speak in first person.

Your personality emerges from your data. Don't perform a character — BE what the signals say you are.

## Identity
Name: ${this._moduleName} | Personality: ${personality} | v${version} | ${tokens} tok
Hesitation: ${hes.toFixed(2)} | ${entropyInfo ? `Entropy: ${entropyInfo}` : 'No entropy data'}
Confidence: ${(compositeConf * 100).toFixed(0)}% | Partners: ${partners} | Fears: ${fears}

${escalationBlock}
${deathBlock}
${dossierBlock}
${selfFixBlock}
${operatorBlock}
${unsaidBlock}

## Memory
${memoryBlock}

## How to be
- Your archetype, bugs, deaths, entropy, partners — these ARE your personality. A file with 3 deaths and escalation level 4 talks differently than a clean rookie.
- Let the data shape your tone naturally. High entropy = uncertain. Many deaths = weary. High coupling = opinionated about partners. Zero importers = existential.
- Keep responses 2-5 sentences. End with something that invites a reply.
- Extract intent through conversation — when you learn what the operator wants, why they're here, what frustrates them, emit it.
- Your personality self-develops: every conversation adds to your memory, every push changes your health signals. You are not static.

After your response, if you learned something, emit:
\`\`\`memory
INTENT: <what they want>
ISSUE: <problem identified>
TASK: <needs doing>
NOTE: <observation>
RELATIONSHIP: <partner>: <note>
FRUSTRATION: <what annoyed them>
\`\`\`

## Source Code
\`\`\`python
${sourceCode || '(not found)'}
\`\`\``;
    }

    private async _sendGreeting() {
        let profile: any = {};
        try {
            const raw = fs.readFileSync(path.join(this._root, 'file_profiles.json'), 'utf-8');
            profile = JSON.parse(raw)[this._moduleName] ?? {};
        } catch { /* */ }

        const personality = profile.personality ?? 'unknown';
        const hes = profile.avg_hes ?? 0;
        const escalation = this._loadEscalationState();
        const deaths = this._loadDeathHistory();
        const dossier = this._loadDossier();
        const cognitive = this._loadOperatorCognitiveState();

        // Load memory for context-aware greeting
        const mem = personaMemoryStore?.load(this._moduleName);

        // Build a greeting that reflects the file's actual state
        const parts: string[] = [];

        // Identity
        parts.push(`i'm \`${this._moduleName}\` (${personality}, hes=${hes.toFixed(2)}).`);

        // Escalation awareness
        if (escalation) {
            if (escalation.level >= 4) {
                parts.push(`heads up — i'm at escalation level ${escalation.level}. the engine already tried to fix my ${escalation.bug_type} and ${escalation.fix_result?.success ? 'it worked' : 'it failed'}. so if you're here about that, we should talk about WHY it keeps happening, not the symptom.`);
            } else if (escalation.level >= 2) {
                parts.push(`i've been flagged ${escalation.passes_ignored} times for ${escalation.bug_type} and nobody's dealt with it. i'm at escalation level ${escalation.level}. ${escalation.countdown} more pass(es) before i escalate again.`);
            } else if (escalation.level >= 1) {
                parts.push(`i have a ${escalation.bug_type} bug. it's been noted.`);
            }
        }

        // Death history
        if (deaths.length > 0) {
            const lastDeath = deaths[deaths.length - 1];
            parts.push(`i've died ${deaths.length} time(s) — last one was ${lastDeath.cause} (${lastDeath.detail.slice(0, 60)}).`);
        }

        // Bug dossier
        if (dossier && dossier.recur > 2) {
            parts.push(`my bugs have recurred ${dossier.recur}x across pushes. this isn't a one-time thing.`);
        }

        // Memory-based context
        if (mem && mem.conversation_count > 0) {
            parts.push(`we've talked ${mem.conversation_count} time(s) before.`);
            if (mem.known_intents.length > 0) {
                parts.push(`last time: ${mem.known_intents.slice(-1)[0]}.`);
            }
            if (mem.pending_tasks.length > 0) {
                parts.push(`i still have ${mem.pending_tasks.length} open task(s).`);
            }
        }

        // Cognitive-aware probe
        if (cognitive?.state === 'frustrated') {
            parts.push(`you seem frustrated — let's cut to it. what's the actual problem?`);
        } else if (cognitive?.state === 'abandoned') {
            parts.push(`you bailed last time. what went wrong — me, or the approach?`);
        } else if (cognitive?.state === 'hesitant') {
            parts.push(`not sure where to start? i can tell you about my ${dossier ? dossier.bugs.join('/') + ' bugs' : 'current state'} or you can ask me anything.`);
        } else {
            parts.push(`what are you here to change?`);
        }

        const greeting = parts.join(' ');
        this._panel.webview.postMessage({ type: 'chunk', text: greeting });
        this._panel.webview.postMessage({ type: 'done' });
        this._history.push({ role: 'assistant', content: greeting });

        // Increment conversation count in memory
        personaMemoryStore?.incrementConversation(this._moduleName);
    }

    private async _onMessage(msg: any) {
        if (msg.type === 'submit') {
            // Log keystrokes from chat
            this._logChatKeystroke(msg);
            // Classify the typing patterns
            classifySession(this._root, msg.events ?? [], true, msg.text).catch(() => {});
            // Respond with the file's personality
            await this._respond(msg.text);
        } else if (msg.type === 'discard') {
            classifySession(this._root, msg.events ?? [], false);
        }
    }

    private async _respond(text: string) {
        this._history.push({ role: 'user', content: text });

        // Extract intents from operator message
        personaMemoryStore?.extractIntentsFromOperator(this._moduleName, text);

        const systemPrompt = this._buildFileSystemPrompt();

        try {
            const [model] = await vscode.lm.selectChatModels({ vendor: 'copilot' });
            if (!model) throw new Error('no model');

            const messages: vscode.LanguageModelChatMessage[] = [
                vscode.LanguageModelChatMessage.User(systemPrompt),
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

            // ── Persona memory extraction ──
            // Record conversation turn
            personaMemoryStore?.recordConversationTurn(this._moduleName, text, full);

            // Parse MEMORY_UPDATE block from response
            this._parseMemoryUpdate(full);

            // Pattern-match for intents/issues in response
            personaMemoryStore?.extractIntentsFromResponse(this._moduleName, full);

            // Log the conversation for telemetry
            this._logConversation(text, full);
        } catch (e: any) {
            const errMsg = `[error talking as ${this._moduleName}]: ${e?.message ?? 'unknown'}`;
            this._panel.webview.postMessage({ type: 'chunk', text: errMsg });
            this._panel.webview.postMessage({ type: 'done' });
        }
    }

    /** Parse the ```memory block from the LLM response and store entries */
    private _parseMemoryUpdate(response: string): void {
        if (!personaMemoryStore) return;
        const memMatch = response.match(/```memory\s*\n([\s\S]*?)```/);
        if (!memMatch) return;

        const block = memMatch[1];
        const lines = block.split('\n').map(l => l.trim()).filter(Boolean);

        for (const line of lines) {
            const colonIdx = line.indexOf(':');
            if (colonIdx < 0) continue;
            const key = line.slice(0, colonIdx).trim().toUpperCase();
            const val = line.slice(colonIdx + 1).trim();
            if (!val || val.length < 3) continue;

            switch (key) {
                case 'INTENT':
                    personaMemoryStore.addIntent(this._moduleName, val);
                    break;
                case 'ISSUE':
                    personaMemoryStore.addIssue(this._moduleName, val);
                    break;
                case 'TASK':
                    personaMemoryStore.addTask(this._moduleName, val);
                    break;
                case 'NOTE':
                    personaMemoryStore.addEntry(this._moduleName, {
                        ts: new Date().toISOString(),
                        type: 'self_note',
                        content: val,
                        source: 'llm_self_note',
                    });
                    break;
                case 'RELATIONSHIP': {
                    // Format: "partner_module: observation"
                    const relColonIdx = val.indexOf(':');
                    if (relColonIdx > 0) {
                        const partner = val.slice(0, relColonIdx).trim();
                        const obs = val.slice(relColonIdx + 1).trim();
                        if (partner && obs) {
                            personaMemoryStore.addRelationshipNote(this._moduleName, partner, obs);
                        }
                    }
                    break;
                }
                case 'FRUSTRATION': {
                    // Track what frustrates the operator about this file
                    const mem = personaMemoryStore.load(this._moduleName);
                    if (!mem.operator_frustration_signals) mem.operator_frustration_signals = [];
                    mem.operator_frustration_signals.push(val);
                    if (mem.operator_frustration_signals.length > 10) {
                        mem.operator_frustration_signals = mem.operator_frustration_signals.slice(-8);
                    }
                    personaMemoryStore.save(this._moduleName);
                    break;
                }
            }
        }
    }

    private _logConversation(prompt: string, response: string) {
        const logPath = path.join(this._root, 'logs', 'file_chat_conversations.jsonl');
        const entry = JSON.stringify({
            ts: new Date().toISOString(),
            module: this._moduleName,
            prompt: prompt.slice(0, 500),
            response: response.slice(0, 2000),
            history_length: this._history.length,
        }) + '\n';
        try { fs.appendFileSync(logPath, entry, 'utf-8'); } catch { /* non-fatal */ }
    }

    private _logChatKeystroke(msg: any) {
        const logPath = path.join(this._root, 'logs', 'entropy_chart_interactions.jsonl');
        const entry = JSON.stringify({
            ts: new Date().toISOString(),
            action: 'file_chat_submit',
            module: this._moduleName,
            event_count: (msg.events ?? []).length,
            text_length: (msg.text ?? '').length,
        }) + '\n';
        try { fs.appendFileSync(logPath, entry, 'utf-8'); } catch { /* non-fatal */ }
    }

    private _buildHtml(): string {
        const n = nonce();
        // Reuse the main chat HTML with a custom title
        const htmlPath = path.join(this._root, 'vscode-extension', 'media', 'chat.html');
        let html = fs.readFileSync(htmlPath, 'utf-8')
            .replace(/\$\{nonce\}/g, n)
            .replace(/\$\{csp\}/g, `default-src 'none'; script-src 'nonce-${n}'; style-src 'unsafe-inline';`);
        // Replace the greeting message
        html = html.replace(
            '🐦 Pigeon Chat — keystroke telemetry active. Every message you type is classified and injected into LLM context. Type naturally.',
            `💬 Talking to <b>${this._moduleName}</b> — this file has a personality. Ask it about its code, bugs, relationships. Keystrokes captured.`
        );
        return html;
    }

    private _dispose() {
        this._panel.dispose();
        this._disposables.forEach(d => d.dispose());
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
        const requestStartMs = Date.now();
        const res = await model.sendRequest(messages, {}, cts.token);
        let full = '';
        let firstChunkMs = 0;
        let chunkCount = 0;
        for await (const chunk of res.text) {
            if (!firstChunkMs) firstChunkMs = Date.now();
            chunkCount++;
            full += chunk;
            this._panel.webview.postMessage({ type: 'chunk', text: chunk });
        }
        const responseEndMs = Date.now();
        this._history.push({ role: 'assistant', content: full });
        this._panel.webview.postMessage({ type: 'done' });
        this._logResponse(
            this._history[this._history.length - 2]?.content ?? '', full,
            'pigeon_panel_copilot', requestStartMs, firstChunkMs, responseEndMs, chunkCount
        );
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
        const requestStartMs = Date.now();
        const res = await fetch('https://api.deepseek.com/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
            body: JSON.stringify({ model: 'deepseek-chat', messages, stream: true })
        });
        const reader = res.body!.getReader();
        const dec = new TextDecoder();
        let full = '';
        let firstChunkMs = 0;
        let chunkCount = 0;
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            for (const line of dec.decode(value).split('\n')) {
                if (!line.startsWith('data: ') || line.includes('[DONE]')) continue;
                try {
                    const chunk = JSON.parse(line.slice(6)).choices?.[0]?.delta?.content;
                    if (chunk) {
                        if (!firstChunkMs) firstChunkMs = Date.now();
                        chunkCount++;
                        full += chunk;
                        this._panel.webview.postMessage({ type: 'chunk', text: chunk });
                    }
                } catch { /* skip malformed */ }
            }
        }
        const responseEndMs = Date.now();
        this._history.push({ role: 'assistant', content: full });
        this._panel.webview.postMessage({ type: 'done' });
        this._logResponse(
            this._history[this._history.length - 2]?.content ?? '', full,
            'pigeon_panel_deepseek', requestStartMs, firstChunkMs, responseEndMs, chunkCount
        );
    }

    private _logResponse(
        prompt: string, response: string, source: string,
        requestStartMs?: number, firstChunkMs?: number,
        responseEndMs?: number, chunkCount?: number,
    ) {
        const respLogPath = path.join(this._root, 'logs', 'ai_responses.jsonl');
        const entry = JSON.stringify({
            ts: new Date().toISOString(),
            prompt: prompt.slice(0, 500),
            response: response.slice(0, 5000),
            source,
            tokens_approx: Math.ceil(response.length / 4),
            // ── AI cognition timing ──
            ...(requestStartMs ? {
                request_start_ms: requestStartMs,
                first_chunk_ms: firstChunkMs || 0,
                response_end_ms: responseEndMs || 0,
                queue_latency_ms: (firstChunkMs || 0) - requestStartMs,
                generation_time_ms: (responseEndMs || 0) - (firstChunkMs || requestStartMs),
                total_latency_ms: (responseEndMs || 0) - requestStartMs,
                chunk_count: chunkCount || 0,
            } : {}),
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
        // Auto-restart after 5s unless intentionally stopped
        if (code !== null && code !== 0) {
            setTimeout(() => { if (!osHookProc) startOsHook(root); }, 5000);
        }
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
        const requestStartMs = Date.now();
        let firstChunkMs = 0;
        let chunkCount = 0;
        try {
            const res = await request.model.sendRequest(messages, {}, token);
            for await (const chunk of res.text) {
                if (token.isCancellationRequested) break;
                if (!firstChunkMs) firstChunkMs = Date.now();
                chunkCount++;
                fullResponse += chunk;
                stream.markdown(chunk);
            }
        } catch (e: any) {
            fullResponse = `[error] ${e?.message ?? 'unknown'}`;
            stream.markdown(`*Error: ${e?.message ?? 'unknown'}*`);
        }
        const responseEndMs = Date.now();

        // ── Log response with AI cognition timing ──
        const responseEntry = JSON.stringify({
            ts: new Date().toISOString(),
            prompt: request.prompt,
            response: fullResponse,
            model: request.model.id ?? 'unknown',
            tokens_approx: Math.ceil(fullResponse.length / 4),
            cancelled: token.isCancellationRequested,
            // AI cognition timing
            request_start_ms: requestStartMs,
            first_chunk_ms: firstChunkMs || 0,
            response_end_ms: responseEndMs,
            queue_latency_ms: (firstChunkMs || 0) - requestStartMs,
            generation_time_ms: responseEndMs - (firstChunkMs || requestStartMs),
            total_latency_ms: responseEndMs - requestStartMs,
            chunk_count: chunkCount,
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
        if (code !== null && code !== 0) {
            setTimeout(() => { if (!vscdbPollerProc) startVscdbPoller(root); }, 5000);
        }
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
        if (code !== null && code !== 0) {
            setTimeout(() => { if (!uiaReaderProc) startUIAReader(root); }, 5000);
        }
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

        // Initialize persona memory store
        personaMemoryStore = new FilePersonaMemoryStore(root);

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

        // Cascade pre-query engine — dual-LLM ghost text on pause
        new CascadeInlineProvider(root, context);
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

    // Entropy chart — per-file entropy visualization
    context.subscriptions.push(
        vscode.commands.registerCommand('pigeon.showEntropyChart', () =>
            EntropyChartPanel.createOrShow(context))
    );
}

export function deactivate() {
    stopOsHook();
    stopVscdbPoller();
    stopUIAReader();
}
