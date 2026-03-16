/**
 * extension.ts — Pigeon Chat VS Code Extension
 *
 * Opens a custom chat webview with full keystroke telemetry capture.
 * On every submit:
 *   1. Spawns classify_bridge.py → computes cognitive state from timing
 *   2. Reads operator-state from .github/copilot-instructions.md
 *   3. Injects state as system context prefix into the LM request
 *   4. Streams response back to the webview
 *
 * classify_bridge.py also writes operator_profile.md and refreshes
 * copilot-instructions.md directly — no git commit needed.
 * Copilot picks up the updated state on the next context load.
 *
 * Model priority: vscode.lm (Copilot) → DeepSeek (DEEPSEEK_API_KEY env)
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

interface ClassifyResult { state: string; hesitation: number; wpm: number; }

function classifySession(root: string, events: object[], submitted: boolean): Promise<ClassifyResult> {
    const fallback: ClassifyResult = { state: 'neutral', hesitation: 0, wpm: 0 };
    return new Promise(resolve => {
        const bridge = path.join(root, 'vscode-extension', 'classify_bridge.py');
        if (!fs.existsSync(bridge)) { resolve(fallback); return; }
        const proc = spawn('py', [bridge, root], { cwd: root });
        proc.stdin.write(JSON.stringify({ events, submitted }));
        proc.stdin.end();
        let out = '';
        proc.stdout.on('data', (d: Buffer) => out += d.toString());
        proc.on('close', () => { try { resolve(JSON.parse(out.trim())); } catch { resolve(fallback); } });
        proc.on('error', () => resolve(fallback));
    });
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
            const result = await classifySession(this._root, msg.events, true);
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
    context.subscriptions.push(
        vscode.commands.registerCommand('pigeon.openChat', () =>
            PigeonChatPanel.createOrShow(context))
    );
}

export function deactivate() {}
