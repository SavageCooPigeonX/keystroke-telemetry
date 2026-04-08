"""thought_completer.py — passive always-on-top code analysis overlay.

Watches your VS Code typing (via os_hook's keystroke log), shows real-time
code analysis in a corner popup when you pause. Catches bugs, suggests
next steps, spots missing pieces — not sentence completion.

Launch:  py src/thought_completer.py
         py src/thought_completer.py --corner tr --pause 1500
         py src/thought_completer.py --web --port 8235  (Railway mode)

Hotkeys (global when popup is focused):
    Ctrl+Shift+C   — copy analysis to clipboard
    Ctrl+Shift+X   — dismiss analysis
    Ctrl+Q         — quit

The popup auto-detects which repo you're in from VS Code window titles
and switches context accordingly.
"""
from __future__ import annotations
import ctypes
import json
import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite')
GEMINI_TIMEOUT = 12
LOG_PATH = ROOT / 'logs' / 'thought_completions.jsonl'
KEYSTROKE_LOG = ROOT / 'logs' / 'os_keystrokes.jsonl'

DEFAULT_PAUSE_MS = 3500
DEFAULT_CORNER = 'br'
DEFAULT_WIDTH = 520
DEFAULT_HEIGHT = 220
DEFAULT_OPACITY = 0.92
POLL_INTERVAL_MS = 200  # how often we check the keystroke log

# ── Windows API for repo detection ───────────────────────────────────────────

user32 = ctypes.windll.user32

# callback type for EnumWindows
_WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))


def _get_foreground_title() -> str:
    hwnd = user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(hwnd, buf, 512)
    return buf.value


def _find_vscode_title() -> str | None:
    """Find VS Code window title by enumerating all windows.

    Can't use GetForegroundWindow because the popup itself is foreground.
    """
    result = []

    def _cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value
        if title and 'Visual Studio Code' in title:
            result.append(title)
        return True

    user32.EnumWindows(_WNDENUMPROC(_cb), 0)
    return result[0] if result else None


def _detect_repo_from_title() -> str | None:
    """Extract workspace/repo name from VS Code window title.

    Title format: 'filename - workspace - Visual Studio Code'
    """
    try:
        title = _find_vscode_title()
        if not title:
            return None
        parts = title.split(' - ')
        if len(parts) >= 3:
            return parts[-2].strip()
        elif len(parts) == 2:
            return parts[0].strip()
    except Exception:
        pass
    return None


# ── Gemini + context ─────────────────────────────────────────────────────────

def _load_api_key() -> str | None:
    env_path = ROOT / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith('GEMINI_API_KEY='):
                return line.split('=', 1)[1].strip()
    return os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')


_ctx_cache: dict = {}
_ctx_ts: float = 0


def _load_context(repo_root: Path | None = None) -> dict:
    global _ctx_cache, _ctx_ts
    now = time.time()
    if _ctx_cache and (now - _ctx_ts) < 300:
        return _ctx_cache

    r = repo_root or ROOT
    ctx: dict = {}

    journal = r / 'logs' / 'prompt_journal.jsonl'
    if journal.exists():
        try:
            lines = journal.read_text('utf-8', errors='ignore').strip().splitlines()
            ctx['recent_prompts'] = []
            for line in lines[-5:]:
                entry = json.loads(line)
                ctx['recent_prompts'].append({
                    'msg': entry.get('msg', '')[:300],
                    'intent': entry.get('intent', ''),
                })
        except Exception:
            pass

    telem = r / 'logs' / 'prompt_telemetry_latest.json'
    if telem.exists():
        try:
            t = json.loads(telem.read_text('utf-8', errors='ignore'))
            ctx['hot_modules'] = t.get('hot_modules', [])[:5]
        except Exception:
            pass

    unsaid = r / 'logs' / 'unsaid_reconstructions.jsonl'
    if unsaid.exists():
        try:
            lines = unsaid.read_text('utf-8', errors='ignore').strip().splitlines()
            ctx['unsaid_threads'] = []
            for line in lines[-5:]:
                entry = json.loads(line)
                ctx['unsaid_threads'].append(
                    entry.get('reconstructed', entry.get('deleted', ''))[:200])
        except Exception:
            pass

    _ctx_cache = ctx
    _ctx_ts = now
    return ctx


SYSTEM_PROMPT = """You are a developer's real-time thinking partner. You watch what they type and respond based on WHAT they're typing.

DETECT MODE:
- If the buffer looks like CODE (functions, variables, imports, brackets, indentation, operators, etc.) → ANALYZE it.
- If the buffer looks like PROSE or a PROMPT (natural language, instructions, questions) → COMPLETE their sentence.

CODE MODE (analyzing):
- Point out bugs, missing error handling, edge cases, or style issues in 2-4 short observations.
- Suggest the next logical line or block they should write.
- Be specific — name the variable, the missing check, the off-by-one.
- Keep it concise. No fluff.

PROSE MODE (completing):
- Complete their CURRENT thought, then continue into the next 1-2 related thoughts.
- Target 2-3 full sentences of continuation. Don't stop at one fragment.
- Match their voice: casual, lowercase, fragments ok, dashes ok.
- If mid-word, complete the word first then continue.
- Think about what comes AFTER — what would they logically say next?

ALWAYS:
- Output ONLY the text. No quotes, labels, metadata, no markdown, no headers.
- Don't repeat what they typed. Start where they stopped.
- Use their recent prompts and hot modules for context.
- If buffer is too short (<3 words) or ambiguous, return empty string.
- Be specific. Use module names, file names, technical terms from their context.
"""

import urllib.request


def _looks_like_code(text: str) -> bool:
    """Heuristic: does the buffer look like code vs prose?"""
    indicators = 0
    for sig in ('def ', 'class ', 'import ', 'from ', 'return ', 'if ', 'for ',
                'while ', '()', '{}', '[]', ' = ', '==', '!=', '+=', '-=',
                'self.', 'print(', 'try:', 'except', 'lambda ', '->',
                '"""', "'''", '#', '    ', '\t'):
        if sig in text:
            indicators += 1
    return indicators >= 2


def _build_user_prompt(buffer: str, ctx: dict) -> str:
    is_code = _looks_like_code(buffer)
    mode = 'CODE' if is_code else 'PROSE'
    parts = [f'MODE: {mode}\nBUFFER: """{buffer}"""']
    if ctx.get('recent_prompts'):
        recent = '\n'.join(f"  - [{p['intent']}] {p['msg']}"
                           for p in ctx['recent_prompts'][-3:])
        parts.append(f'RECENT:\n{recent}')
    if ctx.get('hot_modules'):
        mods = ', '.join(m['module'] for m in ctx['hot_modules'][:3])
        parts.append(f'HOT: {mods}')
    if ctx.get('unsaid_threads'):
        parts.append(f'UNSAID: {"; ".join(ctx["unsaid_threads"][-3:])}')
    if is_code:
        parts.append('Analyze this code. Bugs, issues, next step. Output ONLY observations.')
    else:
        parts.append('Continue their text. 2-3 full sentences. Output ONLY continuation.')
    return '\n\n'.join(parts)


def _call_gemini(buffer: str) -> str:
    api_key = _load_api_key()
    if not api_key:
        return ''
    ctx = _load_context()
    user_prompt = _build_user_prompt(buffer, ctx)
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 400,
            'topP': 0.9,
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = data['candidates'][0]['content']['parts']
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    return part['text'].strip()
            return parts[-1].get('text', '').strip()
    except Exception as e:
        print(f'[completer] gemini error: {e}')
        return ''


def _log_completion(entry: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry['ts'] = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ── Keystroke log tail reader ────────────────────────────────────────────────

class BufferWatcher:
    """Tail os_keystrokes.jsonl to get the live typing buffer."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self._offset = 0
        self.buffer = ''
        self.context = 'editor'
        self.last_ts = 0
        self._init_offset()

    def _init_offset(self):
        """Seek to end of file so we only read new events."""
        if self.log_path.exists():
            self._offset = self.log_path.stat().st_size

    def poll(self) -> bool:
        """Read new lines from the log. Returns True if buffer changed."""
        if not self.log_path.exists():
            return False
        try:
            size = self.log_path.stat().st_size
            if size <= self._offset:
                if size < self._offset:
                    self._offset = 0  # file was truncated
                return False

            with open(self.log_path, 'rb') as f:
                f.seek(self._offset)
                new_data = f.read().decode('utf-8', errors='ignore')
                self._offset = f.tell()

            changed = False
            for line in new_data.strip().splitlines():
                try:
                    evt = json.loads(line)
                except Exception:
                    continue
                new_buf = evt.get('buffer', '')
                new_ctx = evt.get('context', self.context)
                new_ts = evt.get('ts', 0)
                if new_buf != self.buffer or new_ctx != self.context:
                    changed = True
                self.buffer = new_buf
                self.context = new_ctx
                self.last_ts = new_ts
                # submit/discard = buffer cleared
                if evt.get('type') in ('submit', 'discard'):
                    self.buffer = ''
                    changed = True
            return changed
        except Exception:
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# DESKTOP POPUP — passive overlay, always-on-top
# ═══════════════════════════════════════════════════════════════════════════════

def run_popup(corner='br', pause_ms=3500, width=520, height=220, opacity=0.92):
    import tkinter as tk

    BG = '#0d1117'
    SURFACE = '#161b22'
    TEXT_C = '#e6edf3'
    GHOST_C = '#6e7681'
    ACCENT = '#58a6ff'
    GREEN = '#3fb950'
    RED = '#f85149'
    DIM = '#8b949e'
    FONT = 'Cascadia Code'

    class App:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title('thought completer')
            self.root.configure(bg=BG)
            self.root.attributes('-topmost', True)
            self.root.attributes('-alpha', opacity)
            self.root.protocol('WM_DELETE_WINDOW', self._quit)
            # keep title bar for easy close/minimize

            # position
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            pad = 12
            pos = {
                'br': (sw - width - pad, sh - height - pad - 48),
                'bl': (pad, sh - height - pad - 48),
                'tr': (sw - width - pad, pad),
                'tl': (pad, pad),
            }
            x, y = pos.get(corner, pos['br'])
            self.root.geometry(f'{width}x{height}+{x}+{y}')

            # state
            self.watcher = BufferWatcher(KEYSTROKE_LOG)
            self.completion = ''
            self.completion_buffer = ''
            self.n_accepted = 0
            self.n_rejected = 0
            self.pause_after_id = None
            self.completing = False
            self.current_repo = _detect_repo_from_title() or ROOT.name
            self.last_change_time = 0  # epoch when buffer last changed
            self._completed_buffer = None  # buffer text we already completed (prevent re-fire)
            self.dragging = False
            self.drag_x = 0
            self.drag_y = 0

            self._build_ui()
            self._bind_keys()
            self._start_polling()

        def _build_ui(self):
            r = self.root
            mono = (FONT, 10)
            small = (FONT, 8)

            # ── title bar (draggable) ──
            hdr = tk.Frame(r, bg=SURFACE, height=22)
            hdr.pack(fill='x')
            hdr.pack_propagate(False)
            hdr.bind('<Button-1>', self._drag_start)
            hdr.bind('<B1-Motion>', self._drag_motion)

            tk.Label(hdr, text='\U0001f9e0 thought completer', bg=SURFACE,
                     fg=ACCENT, font=(FONT, 8, 'bold')).pack(side='left', padx=6)
            self.repo_lbl = tk.Label(hdr, text=self.current_repo, bg=SURFACE,
                                     fg=DIM, font=small)
            self.repo_lbl.pack(side='left', padx=4)
            self.stats_lbl = tk.Label(hdr, text='\u2713 0  \u2717 0', bg=SURFACE,
                                      fg=DIM, font=small)
            self.stats_lbl.pack(side='right', padx=2)
            self.status_lbl = tk.Label(hdr, text='watching', bg=SURFACE,
                                       fg=DIM, font=small)
            self.status_lbl.pack(side='right', padx=4)

            # close / minimize buttons
            close_btn = tk.Label(hdr, text=' \u2715 ', bg=SURFACE, fg=RED,
                                 font=(FONT, 10, 'bold'), cursor='hand2')
            close_btn.pack(side='right', padx=0)
            close_btn.bind('<Button-1>', lambda e: self._quit())
            close_btn.bind('<Enter>', lambda e: close_btn.config(bg='#da3633'))
            close_btn.bind('<Leave>', lambda e: close_btn.config(bg=SURFACE))

            min_btn = tk.Label(hdr, text=' \u2500 ', bg=SURFACE, fg=DIM,
                               font=(FONT, 10), cursor='hand2')
            min_btn.pack(side='right', padx=0)
            min_btn.bind('<Button-1>', lambda e: self.root.iconify())
            min_btn.bind('<Enter>', lambda e: min_btn.config(bg='#30363d'))
            min_btn.bind('<Leave>', lambda e: min_btn.config(bg=SURFACE))

            # ── unified text display (buffer + inline completion) ──
            self.text_box = tk.Text(r, bg=BG, fg=TEXT_C, font=(FONT, 11),
                                    wrap='word', borderwidth=0, highlightthickness=0,
                                    padx=10, pady=8, cursor='arrow',
                                    state='disabled', spacing1=2, spacing3=2)
            self.text_box.pack(fill='both', expand=True)
            self.text_box.tag_configure('buffer', foreground=TEXT_C)
            self.text_box.tag_configure('completion', foreground=GREEN,
                                        font=(FONT, 11, 'italic'))
            # clicking completion copies it
            self.text_box.tag_bind('completion', '<Button-1>', self._accept)

            # ── footer ──
            ftr = tk.Frame(r, bg=SURFACE, height=18)
            ftr.pack(fill='x')
            ftr.pack_propagate(False)
            tk.Label(ftr, text='ctrl+shift+c copy \u00b7 ctrl+shift+x dismiss \u00b7 type in VS Code',
                     bg=SURFACE, fg=GHOST_C, font=(FONT, 7)).pack(side='left', padx=6)
            self.ctx_lbl = tk.Label(ftr, text='editor', bg=SURFACE, fg=DIM,
                                    font=(FONT, 7))
            self.ctx_lbl.pack(side='right', padx=6)

            # toast
            self.toast_lbl = tk.Label(r, text='', bg=GREEN, fg='#000',
                                      font=(FONT, 9, 'bold'))

        def _bind_keys(self):
            # Global hotkeys work even when popup isn't focused via low-level hook
            # But for simplicity, bind when popup gets focus
            self.root.bind('<Control-Shift-KeyPress-C>', self._accept)
            self.root.bind('<Control-Shift-KeyPress-c>', self._accept)
            self.root.bind('<Control-Shift-KeyPress-X>', self._dismiss)
            self.root.bind('<Control-Shift-KeyPress-x>', self._dismiss)
            self.root.bind('<Control-q>', lambda e: self._quit())

        def _drag_start(self, event):
            self.drag_x = event.x
            self.drag_y = event.y

        def _drag_motion(self, event):
            x = self.root.winfo_x() + event.x - self.drag_x
            y = self.root.winfo_y() + event.y - self.drag_y
            self.root.geometry(f'+{x}+{y}')

        # ── polling loop ──

        def _start_polling(self):
            self._poll_tick()
            self._repo_tick()

        def _poll_tick(self):
            """Check for new keystrokes from os_hook."""
            changed = self.watcher.poll()
            buf = self.watcher.buffer.strip()
            ctx = self.watcher.context

            self.ctx_lbl.config(text=ctx)

            if changed:
                self.last_change_time = time.time()
                self._completed_buffer = None  # buffer changed, allow new completion
                print(f'[poll] changed buf={buf[-40:]!r} len={len(buf)}')

                # if buffer changed and we had a completion, check if still valid
                if self.completion and buf != self.completion_buffer:
                    self._log(False, buf)
                    self.completion = ''
                    self.completion_buffer = ''

                self._refresh_display(buf)

                # cancel any pending completion — user is still typing
                if self.pause_after_id:
                    self.root.after_cancel(self.pause_after_id)
                    self.pause_after_id = None
                self.status_lbl.config(text='typing...', fg=DIM)

            else:
                # no new data — check if user has PAUSED long enough
                elapsed = (time.time() - self.last_change_time) * 1000 if self.last_change_time > 0 else 0
                can_complete = (buf and len(buf) >= 8
                                and not self.completion and not self.completing
                                and self.last_change_time > 0
                                and self.pause_after_id is None
                                and self._completed_buffer != buf)

                if can_complete and elapsed >= pause_ms:
                    print(f'[poll] FIRE elapsed={elapsed:.0f}ms buf={buf[-40:]!r}')
                    self.status_lbl.config(text='paused — thinking...', fg=ACCENT)
                    self.pause_after_id = self.root.after(
                        0, lambda: self._request_completion(buf))
                elif can_complete and elapsed > 500:
                    # show a countdown/waiting indicator
                    secs_left = max(0, (pause_ms - elapsed) / 1000)
                    self.status_lbl.config(text=f'pause {secs_left:.1f}s...', fg=DIM)

            self.root.after(POLL_INTERVAL_MS, self._poll_tick)

        def _repo_tick(self):
            """Periodically check which VS Code workspace is active."""
            repo = _detect_repo_from_title()
            if repo and repo != self.current_repo:
                self.current_repo = repo
                self.repo_lbl.config(text=repo)
                # invalidate context cache when repo switches
                global _ctx_cache, _ctx_ts
                _ctx_cache = {}
                _ctx_ts = 0
            self.root.after(3000, self._repo_tick)

        # ── display ──

        def _refresh_display(self, buf):
            """Render buffer + inline completion in the text widget."""
            self.text_box.config(state='normal')
            self.text_box.delete('1.0', 'end')
            display = buf[-300:] if buf else 'waiting for input in VS Code...'
            self.text_box.insert('end', display, 'buffer')
            if self.completion:
                self.text_box.insert('end', self.completion, 'completion')
            self.text_box.config(state='disabled')
            # auto-scroll to end
            self.text_box.see('end')

        # ── completion ──

        def _request_completion(self, buf):
            if self.completing:
                return
            # verify buffer hasn't changed since timer was set
            current = self.watcher.buffer.strip()
            if current != buf or len(buf) < 8:
                return
            self.completing = True
            self._completed_buffer = buf  # mark this buffer as attempted
            self.status_lbl.config(text='analyzing...', fg=ACCENT)

            def _do():
                result = _call_gemini(buf)
                self.root.after(0, lambda: self._show(buf, result))

            threading.Thread(target=_do, daemon=True).start()

        def _show(self, buf, completion):
            self.completing = False
            self.pause_after_id = None
            current = self.watcher.buffer.strip()
            if not completion or current != buf:
                self.status_lbl.config(text='watching', fg=DIM)
                return
            self.completion = completion
            self.completion_buffer = buf
            self._refresh_display(buf)
            self.status_lbl.config(text='ctrl+shift+c copy', fg=GREEN)

        def _accept(self, event=None):
            if not self.completion:
                return
            # copy completion to clipboard
            full_text = self.completion
            self.root.clipboard_clear()
            self.root.clipboard_append(full_text)
            self.root.update()
            self._log(True, self.watcher.buffer)
            self.n_accepted += 1
            self._update_stats()
            self._toast('copied!', GREEN)
            self.completion = ''
            self.completion_buffer = ''
            self._refresh_display(self.watcher.buffer.strip())
            self.status_lbl.config(text='watching', fg=DIM)

        def _dismiss(self, event=None):
            if not self.completion:
                return
            self._log(False, self.watcher.buffer)
            self.n_rejected += 1
            self._update_stats()
            self.completion = ''
            self.completion_buffer = ''
            self._refresh_display(self.watcher.buffer.strip())
            self.status_lbl.config(text='dismissed', fg=RED)

        def _log(self, accepted, final_text):
            if not self.completion:
                return
            _log_completion({
                'buffer': self.completion_buffer[:2000],
                'completion': self.completion[:500],
                'accepted': accepted,
                'final_text': (final_text or '')[:2000],
                'repo': self.current_repo,
                'context': self.watcher.context,
            })

        def _update_stats(self):
            self.stats_lbl.config(text=f'\u2713 {self.n_accepted}  \u2717 {self.n_rejected}')

        def _toast(self, msg, color):
            self.toast_lbl.config(text=f'  {msg}  ', bg=color)
            self.toast_lbl.place(relx=0.5, rely=0.5, anchor='center')
            self.root.after(1200, lambda: self.toast_lbl.place_forget())

        def _quit(self):
            self.root.destroy()

        def run(self):
            self.root.mainloop()

    print(f'[thought completer] passive overlay | corner={corner} pause={pause_ms}ms')
    print(f'[thought completer] model: {GEMINI_MODEL}')
    print(f'[thought completer] watching: {KEYSTROKE_LOG}')
    print(f'[thought completer] log: {LOG_PATH}')
    app = App()
    app.run()


# ═══════════════════════════════════════════════════════════════════════════════
# WEB SERVER MODE (Railway deploy)
# ═══════════════════════════════════════════════════════════════════════════════

WEB_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>thought completer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#e6edf3;font-family:'Cascadia Code',monospace;font-size:14px;height:100vh;display:flex;flex-direction:column}
#h{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid #30363d;background:#161b22;font-size:12px;color:#8b949e}
#h .t{color:#58a6ff;font-weight:600}
#w{flex:1;position:relative}
#g{position:absolute;inset:0;padding:16px;white-space:pre-wrap;font:inherit;pointer-events:none;z-index:1;line-height:1.6}
.ty{color:transparent}.co{color:#484f58;font-style:italic}
#i{position:absolute;inset:0;padding:16px;background:transparent;color:#e6edf3;border:none;outline:none;resize:none;font:inherit;line-height:1.6;z-index:2;caret-color:#58a6ff}
#b{padding:6px 12px;border-top:1px solid #30363d;background:#161b22;font-size:11px;color:#8b949e;display:flex;justify-content:space-between}
</style></head><body>
<div id="h"><span class="t">&#x1f9e0; thought completer</span><span id="s">ready</span></div>
<div id="w"><div id="g"><span class="ty"></span><span class="co"></span></div>
<textarea id="i" placeholder="start typing..." spellcheck="false" autofocus></textarea></div>
<div id="b"><span>tab accept · esc dismiss · ctrl+enter copy</span><span id="st">✓0 ✗0</span></div>
<script>
let pt,cc='',cb='',na=0,nr=0;
const i=document.getElementById('i'),gt=document.querySelector('.ty'),gc=document.querySelector('.co'),s=document.getElementById('s'),st=document.getElementById('st');
function ug(){gt.textContent=i.value;gc.textContent=(cc&&i.value===cb)?cc:'';if(cc&&i.value!==cb){lg(0);cc=cb=''}}
function lg(a){if(!cc)return;fetch('/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({buffer:cb,completion:cc,accepted:!!a,final_text:i.value.slice(0,2e3)})}).catch(()=>{});a?na++:nr++;st.textContent='\u2713'+na+' \u2717'+nr}
async function rq(){const b=i.value.trim();if(b.length<8)return;s.textContent='...';try{const r=await(await fetch('/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({buffer:b})})).json();if(r.completion&&i.value.trim()===b){cc=r.completion;cb=i.value;ug();s.textContent='tab'}else s.textContent='ready'}catch(e){s.textContent='err'}}
i.addEventListener('input',()=>{ug();clearTimeout(pt);s.textContent='typing';pt=setTimeout(rq,2e3)});
i.addEventListener('keydown',e=>{if(e.key==='Tab'&&cc){e.preventDefault();i.value=cb+cc;lg(1);cc=cb='';ug();s.textContent='ready';clearTimeout(pt);pt=setTimeout(rq,2e3)}if(e.key==='Escape'&&cc){e.preventDefault();lg(0);cc=cb='';ug()}if(e.key==='Enter'&&e.ctrlKey){e.preventDefault();const t=i.value.trim();t&&navigator.clipboard.writeText(t).then(()=>{i.value='';cc=cb='';ug()})}});
</script></body></html>"""


def run_web(port=8235):
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _c(self):
            for h, v in [('Access-Control-Allow-Origin', '*'),
                         ('Access-Control-Allow-Methods', 'GET,POST,OPTIONS'),
                         ('Access-Control-Allow-Headers', 'Content-Type')]:
                self.send_header(h, v)
        def _j(self, d, s=200):
            b = json.dumps(d, ensure_ascii=False).encode()
            self.send_response(s); self.send_header('Content-Type', 'application/json')
            self._c(); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
        def do_OPTIONS(self):
            self.send_response(204); self._c(); self.end_headers()
        def do_GET(self):
            if self.path in ('/', '/index.html'):
                b = WEB_HTML.encode()
                self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
                self._c(); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
            elif self.path == '/health': self._j({'status': 'ok', 'model': GEMINI_MODEL})
            elif self.path == '/context': self._j(_load_context())
            else: self.send_error(404)
        def do_POST(self):
            ln = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(ln) if ln else b'{}'
            try: data = json.loads(raw)
            except Exception: self._j({'error': 'bad json'}, 400); return
            if self.path == '/complete':
                buf = data.get('buffer', '').strip()
                self._j({'completion': '' if len(buf) < 8 else _call_gemini(buf)})
            elif self.path == '/log':
                _log_completion(data); self._j({'ok': True})
            else: self.send_error(404)

    class S(ThreadingMixIn, HTTPServer): daemon_threads = True
    srv = S(('0.0.0.0', port), H)
    print(f'[thought completer] web on http://localhost:{port}')
    try: srv.serve_forever()
    except KeyboardInterrupt: srv.shutdown()


# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description='thought completer — passive overlay')
    p.add_argument('--web', action='store_true', help='web server mode (Railway)')
    p.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8235)))
    p.add_argument('--corner', default=DEFAULT_CORNER, choices=['tl', 'tr', 'bl', 'br'])
    p.add_argument('--pause', type=int, default=DEFAULT_PAUSE_MS)
    p.add_argument('--width', type=int, default=DEFAULT_WIDTH)
    p.add_argument('--height', type=int, default=DEFAULT_HEIGHT)
    p.add_argument('--opacity', type=float, default=DEFAULT_OPACITY)
    args = p.parse_args()

    if not _load_api_key():
        print('[completer] WARNING: no GEMINI_API_KEY in .env or environment')

    if args.web or os.environ.get('PORT'):
        run_web(args.port)
    else:
        run_popup(args.corner, args.pause, args.width, args.height, args.opacity)


if __name__ == '__main__':
    main()
