import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

export interface MutationStreamChange {
    insertedText: string;
    insertedLength: number;
    replacedLength: number;
    rangeStartLine: number;
    rangeStartCharacter: number;
    rangeEndLine: number;
    rangeEndCharacter: number;
    excerpt: string;
}

export interface MutationStreamEvent {
    ts: number;
    file: string;
    docVersion: number;
    editSource: string;
    charsInserted: number;
    charsReplaced: number;
    linesAdded: number;
    isMultiline: boolean;
    paceMs: number;
    telemetryState: string;
    personality: string;
    opinion: string;
    partnerHint?: string;
    excerpt: string;
    changes: MutationStreamChange[];
}

const STREAM_LOG = path.join('logs', 'mutation_stream.jsonl');
const mutationEmitter = new vscode.EventEmitter<MutationStreamEvent>();

function nonce(): string {
    return `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`;
}

function readMutationHistory(root: string, limit = 36): MutationStreamEvent[] {
    const logPath = path.join(root, STREAM_LOG);
    if (!fs.existsSync(logPath)) return [];

    try {
        const stat = fs.statSync(logPath);
        const readSize = Math.min(256 * 1024, stat.size);
        const fd = fs.openSync(logPath, 'r');
        const buf = Buffer.alloc(readSize);
        fs.readSync(fd, buf, 0, readSize, stat.size - readSize);
        fs.closeSync(fd);

        return buf.toString('utf-8')
            .split('\n')
            .filter(line => line.trim())
            .map(line => {
                try {
                    return JSON.parse(line) as MutationStreamEvent;
                } catch {
                    return null;
                }
            })
            .filter((entry): entry is MutationStreamEvent => !!entry)
            .slice(-limit);
    } catch {
        return [];
    }
}

export function recordMutationStreamEvent(root: string, event: MutationStreamEvent): void {
    const logPath = path.join(root, STREAM_LOG);
    try {
        fs.mkdirSync(path.dirname(logPath), { recursive: true });
        fs.appendFileSync(logPath, JSON.stringify(event) + '\n', 'utf-8');
    } catch {
        // Best-effort persistence only.
    }
    mutationEmitter.fire(event);
}

export class MutationStreamPanel {
    static current: MutationStreamPanel | undefined;

    private readonly _panel: vscode.WebviewPanel;
    private readonly _root: string;
    private readonly _disposables: vscode.Disposable[] = [];

    static createOrShow(context: vscode.ExtensionContext, root: string): void {
        if (MutationStreamPanel.current) {
            MutationStreamPanel.current._panel.reveal(vscode.ViewColumn.One);
            MutationStreamPanel.current._refresh();
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'pigeonMutationStream',
            'Mutation Stream',
            vscode.ViewColumn.One,
            { enableScripts: true, retainContextWhenHidden: true },
        );

        MutationStreamPanel.current = new MutationStreamPanel(panel, root, context);
    }

    constructor(panel: vscode.WebviewPanel, root: string, context: vscode.ExtensionContext) {
        this._panel = panel;
        this._root = root;
        this._panel.webview.html = this._buildHtml();
        this._panel.onDidDispose(() => this._dispose(), null, this._disposables);
        this._panel.webview.onDidReceiveMessage(msg => this._onMessage(msg), null, this._disposables);
        this._disposables.push(
            mutationEmitter.event(event => {
                this._panel.webview.postMessage({ type: 'mutation-event', event });
            }),
        );
        context.subscriptions.push(...this._disposables);
        setTimeout(() => this._refresh(), 100);
    }

    private _refresh(): void {
        const history = readMutationHistory(this._root);
        const stats = {
            total: history.length,
            copilot: history.filter(entry => entry.editSource.startsWith('copilot')).length,
            latestState: history.length > 0 ? history[history.length - 1].telemetryState : 'unknown',
        };
        this._panel.webview.postMessage({ type: 'hydrate', history, stats });
    }

    private async _onMessage(msg: any): Promise<void> {
        switch (msg?.type) {
            case 'refresh':
                this._refresh();
                break;
            case 'open-file': {
                if (typeof msg.file !== 'string' || !msg.file) return;
                const target = path.join(this._root, msg.file);
                if (!fs.existsSync(target)) {
                    vscode.window.showWarningMessage(`No file found for ${msg.file}`);
                    return;
                }
                const doc = await vscode.workspace.openTextDocument(target);
                await vscode.window.showTextDocument(doc, { preview: false });
                break;
            }
        }
    }

    private _buildHtml(): string {
        const n = nonce();
        return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${n}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg0: #081118;
      --bg1: #0d1720;
      --bg2: #142430;
      --ink: #e7f0f2;
      --muted: #98a8ad;
      --teal: #82d6cb;
      --amber: #f1be62;
      --coral: #f28d71;
      --line: rgba(226, 239, 243, 0.12);
      --glass: rgba(10, 18, 24, 0.76);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 10% 10%, rgba(242, 141, 113, 0.16), transparent 24%),
        radial-gradient(circle at 85% 0%, rgba(130, 214, 203, 0.18), transparent 28%),
        linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 50%, var(--bg2) 100%);
      overflow: hidden;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      background: repeating-linear-gradient(
        180deg,
        transparent 0,
        transparent 16px,
        rgba(255, 255, 255, 0.018) 16px,
        rgba(255, 255, 255, 0.018) 17px
      );
      pointer-events: none;
      opacity: 0.65;
    }

    .shell {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-rows: auto auto 1fr;
      height: 100vh;
      padding: 18px;
      gap: 14px;
    }

    .hero, .controls, .card {
      background: var(--glass);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
      backdrop-filter: blur(14px);
    }

    .hero {
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: 16px;
      padding: 18px 20px;
    }

    .kicker {
      text-transform: uppercase;
      letter-spacing: 0.22em;
      font-size: 11px;
      color: var(--muted);
    }

    h1 {
      margin: 8px 0 6px;
      font: 500 30px/1.05 "Iowan Old Style", "Georgia", serif;
      letter-spacing: 0.01em;
    }

    .subhead {
      color: var(--muted);
      max-width: 70ch;
      line-height: 1.45;
      margin: 0;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .stat {
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stat-label {
      font-size: 11px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 6px;
    }

    .stat-value {
      font-size: 22px;
      font-weight: 600;
    }

    .controls {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 16px;
    }

    .cluster {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    button, label.toggle {
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(255, 255, 255, 0.04);
      color: var(--ink);
      border-radius: 999px;
      padding: 8px 12px;
      font: inherit;
      cursor: pointer;
    }

    button.active {
      border-color: rgba(130, 214, 203, 0.45);
      background: rgba(130, 214, 203, 0.12);
    }

    label.toggle {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
    }

    input[type="checkbox"] {
      accent-color: var(--teal);
    }

    .stage {
      position: relative;
      overflow: auto;
      padding-right: 8px;
    }

    .stream {
      display: grid;
      gap: 14px;
      padding-bottom: 24px;
    }

    .card {
      position: relative;
      overflow: hidden;
      padding: 16px 16px 14px;
      transform-style: preserve-3d;
      animation: card-in 540ms cubic-bezier(0.19, 1, 0.22, 1) both;
    }

    .card::after {
      content: "";
      position: absolute;
      inset: auto -30% -60% 35%;
      height: 120px;
      background: radial-gradient(circle, rgba(130, 214, 203, 0.12), transparent 65%);
      pointer-events: none;
    }

    .source-copilot_apply, .source-copilot_tab_accept { border-left: 3px solid var(--teal); }
    .source-copilot_edit, .source-copilot_inline { border-left: 3px solid var(--amber); }
    .source-paste, .source-human_edit { border-left: 3px solid rgba(255, 255, 255, 0.2); }
    .source-undo, .source-unknown { border-left: 3px solid var(--coral); }

    .meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }

    .file {
      font: 600 16px/1.2 "IBM Plex Mono", "Cascadia Code", monospace;
      word-break: break-all;
    }

    .badges {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .badge {
      padding: 4px 8px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--muted);
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .opinion {
      display: flex;
      gap: 8px;
      align-items: baseline;
      margin-bottom: 12px;
    }

    .opinion strong {
      color: var(--ink);
      font-size: 15px;
    }

    .opinion span {
      color: var(--muted);
      font-size: 13px;
    }

    .assembly {
      position: relative;
      padding: 14px;
      border-radius: 14px;
      background: rgba(7, 12, 17, 0.62);
      border: 1px solid rgba(255, 255, 255, 0.05);
      font: 13px/1.5 "Cascadia Code", "Fira Code", monospace;
      min-height: 72px;
      white-space: pre-wrap;
      overflow: hidden;
    }

    .assembly::before {
      content: "mutation assembly";
      position: absolute;
      right: 12px;
      top: 10px;
      font-size: 10px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: rgba(255, 255, 255, 0.2);
    }

    .assembly-line {
      opacity: 0;
      transform: translate3d(0, 12px, 32px) rotateX(50deg);
      filter: blur(5px);
      animation: line-in 420ms cubic-bezier(0.19, 1, 0.22, 1) forwards;
    }

    .footer {
      margin-top: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      color: var(--muted);
      font-size: 12px;
    }

    .footer button {
      padding: 7px 10px;
      font-size: 12px;
    }

    .empty {
      padding: 30px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed rgba(255, 255, 255, 0.12);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.02);
    }

    @keyframes card-in {
      from {
        opacity: 0;
        transform: perspective(1400px) rotateX(74deg) translateY(38px) scale(0.93);
      }
      to {
        opacity: 1;
        transform: perspective(1400px) rotateX(0deg) translateY(0) scale(1);
      }
    }

    @keyframes line-in {
      from {
        opacity: 0;
        transform: translate3d(0, 12px, 32px) rotateX(50deg);
        filter: blur(5px);
      }
      to {
        opacity: 1;
        transform: translate3d(0, 0, 0) rotateX(0deg);
        filter: blur(0);
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div>
        <div class="kicker">organism playback</div>
        <h1>Live mutation stream</h1>
        <p class="subhead">Real edit events are staged as assemblies instead of dead diffs. The timing follows the operator pace captured with each mutation, so the file growth feels read rather than dumped.</p>
      </div>
      <div class="stats">
        <div class="stat"><div class="stat-label">stream events</div><div class="stat-value" id="stat-total">0</div></div>
        <div class="stat"><div class="stat-label">copilot-sourced</div><div class="stat-value" id="stat-copilot">0</div></div>
        <div class="stat"><div class="stat-label">operator state</div><div class="stat-value" id="stat-state">unknown</div></div>
      </div>
    </section>

    <section class="controls">
      <div class="cluster">
        <button id="refreshBtn">refresh</button>
        <label class="toggle"><input id="copilotOnly" type="checkbox" checked> copilot only</label>
      </div>
      <div class="cluster">
        <button class="speed active" data-speed="1">auto pace</button>
        <button class="speed" data-speed="0.65">slow drift</button>
        <button class="speed" data-speed="1.5">fast cut</button>
      </div>
    </section>

    <div class="stage">
      <div id="stream" class="stream"></div>
    </div>
  </div>

  <script nonce="${n}">
    const vscodeApi = acquireVsCodeApi();
    const state = {
      allEvents: [],
      copilotOnly: true,
      speed: 1,
    };

    const stream = document.getElementById('stream');
    const statTotal = document.getElementById('stat-total');
    const statCopilot = document.getElementById('stat-copilot');
    const statState = document.getElementById('stat-state');
    const copilotOnly = document.getElementById('copilotOnly');
    const speedButtons = [...document.querySelectorAll('.speed')];

    document.getElementById('refreshBtn').addEventListener('click', () => {
      vscodeApi.postMessage({ type: 'refresh' });
    });

    copilotOnly.addEventListener('change', () => {
      state.copilotOnly = copilotOnly.checked;
      renderAll();
    });

    speedButtons.forEach(button => {
      button.addEventListener('click', () => {
        state.speed = Number(button.dataset.speed || '1');
        speedButtons.forEach(entry => entry.classList.toggle('active', entry === button));
      });
    });

    function isCopilotSource(source) {
      return typeof source === 'string' && source.startsWith('copilot');
    }

    function passesFilter(event) {
      return !state.copilotOnly || isCopilotSource(event.editSource);
    }

    function humanTime(ts) {
      const delta = Math.max(0, Date.now() - ts);
      if (delta < 1000) return 'now';
      if (delta < 60000) return Math.round(delta / 1000) + 's ago';
      return Math.round(delta / 60000) + 'm ago';
    }

    function sourceClass(source) {
      return 'source-' + String(source || 'unknown').replace(/[^a-z0-9_]+/gi, '_');
    }

    function summarize(event) {
      const parts = [];
      parts.push('+' + event.charsInserted);
      if (event.charsReplaced > 0) parts.push('~' + event.charsReplaced);
      if (event.linesAdded > 0) parts.push(event.linesAdded + ' lines');
      return parts.join(' · ');
    }

    function sourceLabel(source) {
      return String(source || 'unknown').replace(/_/g, ' ');
    }

    function buildLines(event) {
      const excerpt = (event.excerpt || '').trim();
      if (excerpt) {
        return excerpt.split(/\r?\n/).slice(0, 8);
      }
      const inserted = (event.changes || [])
        .map(change => (change.insertedText || '').trim())
        .filter(Boolean)
        .join('\n');
      if (inserted) {
        return inserted.split(/\r?\n/).slice(0, 8);
      }
      return ['// mutation captured with no excerpt'];
    }

    function updateStats() {
      statTotal.textContent = String(state.allEvents.length);
      statCopilot.textContent = String(state.allEvents.filter(event => isCopilotSource(event.editSource)).length);
      statState.textContent = state.allEvents.length ? state.allEvents[state.allEvents.length - 1].telemetryState : 'unknown';
    }

    function trimStream() {
      while (stream.children.length > 18) {
        stream.removeChild(stream.lastElementChild);
      }
    }

    function attachAssembly(codeHost, event) {
      const lines = buildLines(event);
      const totalMs = Math.max(240, Math.round((event.paceMs || 1200) / state.speed));
      const stepMs = Math.max(80, Math.floor(totalMs / Math.max(lines.length, 1)));
      lines.forEach((line, index) => {
        window.setTimeout(() => {
          const node = document.createElement('div');
          node.className = 'assembly-line';
          node.textContent = line.length > 220 ? line.slice(0, 220) + ' ...' : line || ' ';
          codeHost.appendChild(node);
        }, index * stepMs);
      });
    }

    function renderCard(event, prepend) {
      if (!passesFilter(event)) return;

      const card = document.createElement('article');
      card.className = 'card ' + sourceClass(event.editSource);
      card.innerHTML = [
        '<div class="meta">',
        '  <div class="file"></div>',
        '  <div class="badges">',
        '    <span class="badge"></span>',
        '    <span class="badge"></span>',
        '    <span class="badge"></span>',
        '  </div>',
        '</div>',
        '<div class="opinion"><strong></strong><span></span></div>',
        '<div class="assembly"></div>',
        '<div class="footer">',
        '  <span class="footnote"></span>',
        '  <button type="button">open file</button>',
        '</div>'
      ].join('');

      card.querySelector('.file').textContent = event.file;
      const badges = card.querySelectorAll('.badge');
      badges[0].textContent = sourceLabel(event.editSource);
      badges[1].textContent = event.personality || 'unprofiled';
      badges[2].textContent = event.telemetryState || 'unknown';
      card.querySelector('.opinion strong').textContent = event.opinion || 'mutating';
      card.querySelector('.opinion span').textContent = event.partnerHint
        ? 'nearest partner: ' + event.partnerHint
        : 'no partner hint';
      card.querySelector('.footnote').textContent = humanTime(event.ts) + ' · ' + summarize(event);
      card.querySelector('button').addEventListener('click', () => {
        vscodeApi.postMessage({ type: 'open-file', file: event.file });
      });

      const host = card.querySelector('.assembly');
      attachAssembly(host, event);

      if (prepend) {
        stream.prepend(card);
      } else {
        stream.appendChild(card);
      }
      trimStream();
    }

    function renderEmpty() {
      stream.innerHTML = '<div class="empty">waiting for mutation events — once a file changes, the assembly stream will stage it here.</div>';
    }

    function renderAll() {
      stream.innerHTML = '';
      const visible = state.allEvents.filter(passesFilter);
      if (!visible.length) {
        renderEmpty();
        return;
      }
      visible.slice(-12).forEach(event => renderCard(event, false));
    }

    window.addEventListener('message', event => {
      const message = event.data;
      if (message.type === 'hydrate') {
        state.allEvents = Array.isArray(message.history) ? message.history : [];
        updateStats();
        renderAll();
      }
      if (message.type === 'mutation-event' && message.event) {
        state.allEvents.push(message.event);
        updateStats();
        if (!stream.querySelector('.empty')) {
          renderCard(message.event, true);
        } else {
          renderAll();
        }
      }
    });

    renderEmpty();
  </script>
</body>
</html>`;
    }

    private _dispose(): void {
        MutationStreamPanel.current = undefined;
        this._panel.dispose();
        while (this._disposables.length > 0) {
            const disposable = this._disposables.pop();
            disposable?.dispose();
        }
    }
}