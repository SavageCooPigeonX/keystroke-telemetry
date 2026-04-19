/**
 * cascadeProvider.ts — Gemini-only Thought Completion Ghost Text
 *
 * Fires on PAUSE in the editor. Calls the pre_query_engine server
 * (single Gemini Flash call) which reads organism state from semantic
 * filenames and completes the operator's thought. Sub-2s target.
 *
 * Shows results as inline ghost text (InlineCompletionProvider).
 *
 * Scale control via keybindings:
 *   Ctrl+Up:   scale up (sentence → paragraph → full_write → paper)
 *   Ctrl+Down: scale down
 */
import * as vscode from 'vscode';
import * as http from 'http';
import * as path from 'path';
import * as fs from 'fs';
import { spawn } from 'child_process';

const CASCADE_PORT = 8236;
const CASCADE_BASE = `http://127.0.0.1:${CASCADE_PORT}`;
const PAUSE_THRESHOLD_MS = 1650;
const MIN_FRAGMENT_LEN = 4;
const COOLDOWN_MS = 3000;

interface CompletionResponse {
    fragment: string;
    completed_thought: string;
    analysis: string;
    suggested_action: string;
    confidence: number;
    selected_files: Array<{ name: string; score: number; reasons: string[] }>;
    scale: { scale: number; label: string; reason: string };
    total_ms: number;
    codebase_kind: string;
    error?: string;
}

export class CascadeInlineProvider implements vscode.InlineCompletionItemProvider {
    private _lastEditMs = 0;
    private _pendingTimer: ReturnType<typeof setTimeout> | undefined;
    private _lastFragment = '';
    private _lastCompletion = '';
    private _cooldownUntil = 0;
    private _statusItem: vscode.StatusBarItem;
    private _filesBadge: vscode.StatusBarItem;
    private _simBadge: vscode.StatusBarItem;
    private _currentScale = 0; // 0 = auto, 1-4 = manual override
    private _simMode = false;
    private _root: string;
    private _logPath: string;
    private _cascadeAvailable = false;

    constructor(root: string, context: vscode.ExtensionContext) {
        this._root = root;
        this._logPath = path.join(root, 'logs', 'cascade_ghost.jsonl');

        // Status bar items
        this._statusItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right, 999);
        this._statusItem.text = '$(zap) Completer';
        this._statusItem.tooltip = 'Gemini thought completion engine';
        this._statusItem.show();
        context.subscriptions.push(this._statusItem);

        this._filesBadge = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right, 998);
        this._filesBadge.text = '';
        context.subscriptions.push(this._filesBadge);

        // Sim mode toggle badge
        this._simBadge = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right, 997);
        this._simBadge.text = '$(beaker) SIM OFF';
        this._simBadge.tooltip = 'Toggle sim mode — files self-score & debate intent on each thought completion';
        this._simBadge.command = 'pigeon.toggleSimMode';
        this._simBadge.show();
        context.subscriptions.push(this._simBadge);

        // Register as inline completion provider
        context.subscriptions.push(
            vscode.languages.registerInlineCompletionItemProvider(
                { pattern: '**' }, this)
        );

        // Listen for typing to detect pauses
        context.subscriptions.push(
            vscode.workspace.onDidChangeTextDocument(e => {
                if (e.document === vscode.window.activeTextEditor?.document) {
                    this._onType(e);
                }
            })
        );

        // Scale control keybindings
        context.subscriptions.push(
            vscode.commands.registerCommand('pigeon.cascadeScaleUp', () => {
                this._currentScale = Math.min((this._currentScale || 2) + 1, 4);
                this._statusItem.text = `$(zap) Scale: ${this._scaleLabel()}`;
            }),
            vscode.commands.registerCommand('pigeon.cascadeScaleDown', () => {
                this._currentScale = Math.max((this._currentScale || 2) - 1, 1);
                this._statusItem.text = `$(zap) Scale: ${this._scaleLabel()}`;
            }),
            vscode.commands.registerCommand('pigeon.cascadeScaleAuto', () => {
                this._currentScale = 0;
                this._statusItem.text = '$(zap) Completer';
            }),
            vscode.commands.registerCommand('pigeon.toggleSimMode', () => {
                this._simMode = !this._simMode;
                if (this._simMode) {
                    this._simBadge.text = '$(beaker) SIM ON';
                    this._simBadge.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                    vscode.window.showInformationMessage('Sim mode ON — files will self-score and debate each thought completion');
                } else {
                    this._simBadge.text = '$(beaker) SIM OFF';
                    this._simBadge.backgroundColor = undefined;
                }
            })
        );

        // Check if completion server is available
        this._checkServer();
    }

    private _scaleLabel(): string {
        return ['Auto', 'Sentence', 'Paragraph', 'Full Write', 'Paper'][this._currentScale];
    }

    private async _checkServer(): Promise<boolean> {
        try {
            const res = await this._httpGet('/health');
            this._cascadeAvailable = !!res;
            if (this._cascadeAvailable) {
                this._statusItem.text = '$(zap) Completer';
                this._statusItem.backgroundColor = undefined;
            }
            return this._cascadeAvailable;
        } catch {
            this._cascadeAvailable = false;
            this._statusItem.text = '$(warning) Completer offline';
            this._statusItem.backgroundColor = new vscode.ThemeColor(
                'statusBarItem.warningBackground');
            return false;
        }
    }

    private _onType(e: vscode.TextDocumentChangeEvent): void {
        this._lastEditMs = Date.now();

        // Clear any pending cascade
        if (this._pendingTimer) {
            clearTimeout(this._pendingTimer);
            this._pendingTimer = undefined;
        }

        // Reset status on new typing
        if (this._cascadeAvailable) {
            this._statusItem.text = '$(zap) Completer';
        }
        this._filesBadge.text = '';
        this._filesBadge.hide();

        // Schedule pause detection
        this._pendingTimer = setTimeout(() => {
            this._onPause();
        }, PAUSE_THRESHOLD_MS);
    }

    private async _onPause(): Promise<void> {
        const now = Date.now();
        if (now < this._cooldownUntil) return;

        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        // Get the text around the cursor as the fragment
        const doc = editor.document;
        const pos = editor.selection.active;
        const lineText = doc.lineAt(pos.line).text;

        // Build fragment from current line + a few lines above for context
        const startLine = Math.max(0, pos.line - 3);
        const fragment = doc.getText(new vscode.Range(startLine, 0, pos.line, pos.character)).trim();

        if (fragment.length < MIN_FRAGMENT_LEN) return;
        if (fragment === this._lastFragment) return;

        this._lastFragment = fragment;
        this._cooldownUntil = now + COOLDOWN_MS;

        // Check server availability
        if (!this._cascadeAvailable) {
            const ok = await this._checkServer();
            if (!ok) return;
        }

        this._statusItem.text = '$(loading~spin) Completing...';

        try {
            const result = await this._callCascade(fragment);
            if (!result) return;

            // L1: Show file badges immediately
            if (result.selected_files?.length > 0) {
                const names = result.selected_files
                    .slice(0, 3)
                    .map(f => f.name)
                    .join(' · ');
                this._filesBadge.text = `$(file-code) ${names}`;
                this._filesBadge.tooltip = result.selected_files
                    .map(f => `${f.name} (${f.score}) — ${f.reasons.join(', ')}`)
                    .join('\n');
                this._filesBadge.show();
            }

            // Store completion for inline provider to pick up
            if (result.completed_thought) {
                this._lastCompletion = result.completed_thought;
                if (result.analysis) {
                    this._lastCompletion += '\n\n' + result.analysis;
                }
                this._statusItem.text = `$(check) ${result.scale?.label || 'Done'} (${result.total_ms}ms)`;

                // Trigger inline completion refresh
                vscode.commands.executeCommand('editor.action.inlineSuggest.trigger');

                // Sim mode: fire file debate in background
                if (this._simMode && result.completed_thought) {
                    this._triggerSim(result.completed_thought, fragment);
                }

                // Log the cascade event
                this._logGhost(fragment, result);
            } else {
                this._statusItem.text = '$(zap) Completer';
                this._lastCompletion = '';
            }
        } catch (err) {
            this._statusItem.text = '$(error) Completer error';
            this._lastCompletion = '';
        }
    }

    // InlineCompletionItemProvider implementation
    provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        _context: vscode.InlineCompletionContext,
        _token: vscode.CancellationToken
    ): vscode.InlineCompletionItem[] | undefined {
        if (!this._lastCompletion) return undefined;

        // Show the cascade output as ghost text after the cursor
        const item = new vscode.InlineCompletionItem(
            this._lastCompletion,
            new vscode.Range(position, position)
        );

        // Clear after providing (one-shot)
        const completion = this._lastCompletion;
        this._lastCompletion = '';

        return [item];
    }

    // HTTP helpers
    private _httpGet(urlPath: string): Promise<string> {
        return new Promise((resolve, reject) => {
            const req = http.get(`${CASCADE_BASE}${urlPath}`, { timeout: 3000 }, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => resolve(data));
            });
            req.on('error', reject);
            req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
        });
    }

    private _callCascade(fragment: string): Promise<CompletionResponse | null> {
        return new Promise((resolve, reject) => {
            const body = JSON.stringify({ fragment });
            const options = {
                hostname: '127.0.0.1',
                port: CASCADE_PORT,
                path: '/complete',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(body),
                },
                timeout: 5000,
            };

            const req = http.request(options, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        resolve(JSON.parse(data));
                    } catch {
                        resolve(null);
                    }
                });
            });

            req.on('error', () => resolve(null));
            req.on('timeout', () => { req.destroy(); resolve(null); });
            req.write(body);
            req.end();
        });
    }

    private _triggerSim(intentText: string, promptText: string): void {
        // Spawn python run_sim in background — non-blocking
        // Results stream to logs/sim_results.jsonl (observable in sim_observatory.html)
        const venv = path.join(this._root, '.venv', 'Scripts', 'python.exe');
        const pyExe = fs.existsSync(venv) ? venv : 'py';
        const escaped = intentText.replace(/'/g, "\\'").slice(0, 200);
        const escapedPrompt = promptText.replace(/'/g, "\\'").slice(0, 200);
        const child = spawn(pyExe, [
            '-c',
            `import sys; sys.path.insert(0,'${this._root.replace(/\\/g, '/')}'); ` +
            `from src.file_sim_seq001_v001 import run_sim; ` +
            `run_sim('${escaped}', prompt_text='${escapedPrompt}', top_n=5)`,
        ], {
            cwd: this._root,
            detached: true,
            stdio: 'ignore',
            env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
        });
        child.unref();
        this._simBadge.text = '$(loading~spin) SIM…';
        // Reset badge after 8 seconds
        setTimeout(() => {
            if (this._simMode) {
                this._simBadge.text = '$(beaker) SIM ON';
                this._simBadge.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
            }
        }, 8000);
    }

    private _logGhost(fragment: string, result: CompletionResponse): void {
        try {
            const dir = path.dirname(this._logPath);
            if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
            const entry = {
                ts: new Date().toISOString(),
                fragment: fragment.slice(-200),
                thought: result.completed_thought?.slice(0, 200),
                files: result.selected_files?.map(f => f.name) ?? [],
                scale: result.scale?.label,
                confidence: result.confidence,
                total_ms: result.total_ms,
                codebase_kind: result.codebase_kind,
            };
            fs.appendFileSync(this._logPath, JSON.stringify(entry) + '\n', 'utf-8');
        } catch { /* non-critical logging */ }
    }
}
