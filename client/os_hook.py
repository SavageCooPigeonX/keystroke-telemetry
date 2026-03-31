"""OS-level keystroke hook — captures ALL input when VS Code is focused.

This is the nuclear option for telemetry.  It sees everything:
editor typing, chat input, search boxes, command palette, terminal.
The extension's TextDocument watcher only sees file edits — this
captures the unseen: Copilot chat composition, deleted prompts,
hesitation in search, abandoned command palette queries.

Architecture:
  - pynput listener runs in background thread
  - ctypes checks foreground window every keystroke (< 0.1ms on Windows)
  - Only records when window title contains 'Visual Studio Code'
  - Writes to logs/os_keystrokes.jsonl in batches
  - Extension spawns this on activate, kills on deactivate
  - A 'context' field tags each keystroke with the active VS Code region
    (inferred from key patterns: Ctrl+Shift+I = chat, Ctrl+P = palette, etc.)

Schema (os_keystrokes.jsonl):
  {"ts": <epoch_ms>, "key": "<key>", "type": "press|release",
   "context": "editor|chat|terminal|palette|search|unknown",
   "buffer": "<current composition buffer>", "buffer_len": <int>}

Argv: <repo_root>
Stdout: JSON status lines for the extension to read
"""
import ctypes
import json
import os
import sys
import threading
import time
from pathlib import Path

# Only import pynput at runtime — it's an optional dependency
try:
    from pynput import keyboard
    from pynput import mouse as pynput_mouse
except ImportError:
    print(json.dumps({"status": "error", "msg": "pynput not installed"}))
    sys.exit(1)

# ── Configuration ────────────────────────────────────────────────────────────

FLUSH_INTERVAL_S = 5       # Write to disk every 5 seconds
IDLE_TIMEOUT_S = 300       # 5 min idle → pause recording
BUFFER_MAX_LEN = 500       # Max composition buffer size
VSCODE_WINDOW_MATCH = 'Visual Studio Code'
_WORKSPACE_NAME: str | None = None  # set by main() from repo root folder name

# ── Windows API for foreground window ────────────────────────────────────────

user32 = ctypes.windll.user32


def _get_foreground_title() -> str:
    hwnd = user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def _is_vscode_focused() -> bool:
    """Check if foreground window is THIS workspace's VS Code window."""
    try:
        title = _get_foreground_title()
        if VSCODE_WINDOW_MATCH not in title:
            return False
        # Scope to this workspace — title format: "file - workspace - Visual Studio Code"
        if _WORKSPACE_NAME and _WORKSPACE_NAME not in title:
            return False
        return True
    except Exception:
        return False


# ── Clipboard reader (ctypes, no subprocess) ────────────────────────────────

_CF_UNICODETEXT = 13
_kernel32 = ctypes.windll.kernel32


def _read_clipboard() -> str:
    """Read current clipboard text via Win32 API. Returns '' on failure."""
    try:
        if not user32.OpenClipboard(0):
            return ''
        try:
            handle = user32.GetClipboardData(_CF_UNICODETEXT)
            if not handle:
                return ''
            _kernel32.GlobalLock.restype = ctypes.c_wchar_p
            text = _kernel32.GlobalLock(handle)
            result = str(text) if text else ''
            _kernel32.GlobalUnlock(handle)
            return result
        finally:
            user32.CloseClipboard()
    except Exception:
        return ''


# ── Mouse selection tracker ─────────────────────────────────────────────────

class MouseSelectionTracker:
    """Detects mouse drag gestures (= text selection) in VS Code."""

    def __init__(self):
        self._press_pos: tuple[int, int] | None = None
        self._press_time: float = 0.0
        self.has_selection = False  # True after a drag; cleared by KeystrokeRecorder

    def on_click(self, x: int, y: int, button, pressed: bool):
        if not _is_vscode_focused():
            return
        if button != pynput_mouse.Button.left:
            return

        if pressed:
            self._press_pos = (x, y)
            self._press_time = time.time()
        else:
            # Release — check if it was a drag (selection) vs a click
            if self._press_pos:
                dx = abs(x - self._press_pos[0])
                dy = abs(y - self._press_pos[1])
                # > 5px movement = drag = selection
                if dx > 5 or dy > 5:
                    self.has_selection = True
                else:
                    # Plain click = deselect / place cursor
                    self.has_selection = False
            self._press_pos = None


# ── Context detection ────────────────────────────────────────────────────────
# Infer what part of VS Code the user is typing in based on key combos.
# This is heuristic but surprisingly accurate.

class ContextTracker:
    def __init__(self):
        self.context = 'editor'
        self._ctrl = False
        self._shift = False

    def on_key(self, key_str: str, pressed: bool) -> str:
        if key_str in ('ctrl_l', 'ctrl_r', 'Key.ctrl_l', 'Key.ctrl_r'):
            self._ctrl = pressed
            return self.context
        if key_str in ('shift', 'shift_l', 'shift_r', 'Key.shift', 'Key.shift_l', 'Key.shift_r'):
            self._shift = pressed
            return self.context

        if not pressed:
            return self.context

        # Detect context switches via key combos
        if self._ctrl:
            if key_str == 'i' and self._shift:
                self.context = 'chat'       # Ctrl+Shift+I = Copilot Chat
            elif key_str == 'i' and not self._shift:
                self.context = 'chat'       # Ctrl+I = inline chat
            elif key_str == 'l':
                self.context = 'chat'       # Ctrl+L = Copilot Chat (new)
            elif key_str == 'p':
                self.context = 'palette'    # Ctrl+P = quick open
            elif key_str == 'f':
                self.context = 'search'     # Ctrl+F = find
            elif key_str == 'h' and self._shift:
                self.context = 'search'     # Ctrl+Shift+H = replace in files
            elif key_str == '`':
                self.context = 'terminal'   # Ctrl+` = terminal
            elif key_str == 'j':
                self.context = 'terminal'   # Ctrl+J = panel toggle

        # Escape returns to editor
        if key_str in ('Key.esc', 'esc'):
            self.context = 'editor'

        return self.context

    def set_context_from_vscdb(self, is_draft_active: bool):
        """Override context when vscdb shows active chat draft."""
        if is_draft_active:
            self.context = 'chat'
        elif self.context == 'chat':
            self.context = 'editor'


# ── Keystroke recorder ───────────────────────────────────────────────────────

class KeystrokeRecorder:
    def __init__(self, root: Path, mouse_tracker: MouseSelectionTracker):
        self._root = root
        self._log_path = root / 'logs' / 'os_keystrokes.jsonl'
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._buffer: list[dict] = []
        self._composition = ''  # Current typing buffer
        self._last_activity = time.time()
        self._ctx = ContextTracker()
        self._lock = threading.Lock()
        self._running = True
        # Selection tracking
        self._mouse = mouse_tracker
        self._all_selected = False   # True after Ctrl+A
        self._ctrl_held = False
        self._shift_held = False
        self._clipboard_snapshot = ''  # last known clipboard text on Ctrl+C

    def _key_to_str(self, key) -> str:
        try:
            return key.char if key.char else str(key)
        except AttributeError:
            return str(key)

    def on_press(self, key):
        if not self._running:
            return
        if not _is_vscode_focused():
            return

        now_ms = int(time.time() * 1000)
        key_str = self._key_to_str(key)
        ctx = self._ctx.on_key(key_str, True)
        self._last_activity = time.time()

        # ── Track modifier state ──
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_held = True
            return
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._shift_held = True
            return

        has_selection = self._all_selected or self._mouse.has_selection

        # ── Ctrl combos ──
        if self._ctrl_held:
            char = getattr(key, 'char', None)
            if char == 'a':
                # Ctrl+A — select all
                self._all_selected = True
                self._emit(now_ms, 'Ctrl+A', 'select_all', ctx)
                return
            if char == 'c':
                # Ctrl+C — copy selection to clipboard
                # Small delay so the OS clipboard is populated
                time.sleep(0.05)
                self._clipboard_snapshot = _read_clipboard()
                self._emit(now_ms, 'Ctrl+C', 'copy', ctx,
                           extra={'copied_text': self._clipboard_snapshot[:200]})
                return
            if char == 'x':
                # Ctrl+X — cut selection (= delete + copy)
                time.sleep(0.05)
                cut_text = _read_clipboard()
                old_buf = self._composition
                # Remove cut text from buffer (best-effort)
                if has_selection:
                    self._composition = ''
                elif cut_text and cut_text in self._composition:
                    self._composition = self._composition.replace(cut_text, '', 1)
                self._all_selected = False
                self._mouse.has_selection = False
                self._emit(now_ms, 'Ctrl+X', 'cut', ctx,
                           extra={'deleted_text': cut_text[:200],
                                  'old_buffer': old_buf[:200]})
                return
            if char == 'v':
                # Ctrl+V — paste (replaces selection if any)
                time.sleep(0.05)
                paste_text = _read_clipboard()
                old_buf = self._composition
                if has_selection:
                    # Paste replaces the entire selection
                    deleted = old_buf if self._all_selected else self._clipboard_snapshot
                    self._composition = paste_text
                    self._all_selected = False
                    self._mouse.has_selection = False
                    self._emit(now_ms, 'Ctrl+V', 'paste_replace', ctx,
                               extra={'deleted_text': deleted[:200],
                                      'pasted_text': paste_text[:200],
                                      'old_buffer': old_buf[:200]})
                else:
                    self._composition += paste_text
                    self._emit(now_ms, 'Ctrl+V', 'paste', ctx,
                               extra={'pasted_text': paste_text[:200]})
                if len(self._composition) > BUFFER_MAX_LEN:
                    self._composition = self._composition[-BUFFER_MAX_LEN:]
                return
            if char == 'z':
                # Ctrl+Z — undo. Buffer may drift, flag it.
                self._all_selected = False
                self._mouse.has_selection = False
                self._emit(now_ms, 'Ctrl+Z', 'undo', ctx,
                           extra={'buffer_drift': True})
                return
            # Other Ctrl combos — pass through
            self._emit(now_ms, f'Ctrl+{key_str}', 'shortcut', ctx)
            return

        # ── Selection-destroying actions ──
        # If text was selected (mouse drag or Ctrl+A), the next typed char
        # or delete key nukes the selection.

        if key == keyboard.Key.backspace:
            if has_selection:
                deleted = self._composition
                self._composition = ''
                self._all_selected = False
                self._mouse.has_selection = False
                self._emit(now_ms, 'Backspace', 'selection_delete', ctx,
                           extra={'deleted_text': deleted[:200]})
            else:
                if self._composition:
                    self._composition = self._composition[:-1]
                self._emit(now_ms, 'Backspace', 'backspace', ctx)
            return

        if key == keyboard.Key.delete:
            if has_selection:
                deleted = self._composition
                self._composition = ''
                self._all_selected = False
                self._mouse.has_selection = False
                self._emit(now_ms, 'Delete', 'selection_delete', ctx,
                           extra={'deleted_text': deleted[:200]})
            else:
                self._emit(now_ms, 'Delete', 'delete', ctx)
            return

        if key == keyboard.Key.enter:
            self._all_selected = False
            self._mouse.has_selection = False
            self._emit(now_ms, 'Enter', 'submit', ctx)
            self._composition = ''
            self.flush()
            self._analyze_composition()
            return

        if key == keyboard.Key.esc:
            self._all_selected = False
            self._mouse.has_selection = False
            self._emit(now_ms, 'Escape', 'discard', ctx)
            self._composition = ''
            return

        if key == keyboard.Key.space:
            if has_selection:
                deleted = self._composition
                self._composition = ' '
                self._all_selected = False
                self._mouse.has_selection = False
                self._emit(now_ms, ' ', 'selection_replace', ctx,
                           extra={'deleted_text': deleted[:200]})
            else:
                self._composition += ' '
                self._emit(now_ms, ' ', 'insert', ctx)
            return

        # ── Regular character ──
        char = getattr(key, 'char', None)
        if char:
            if has_selection:
                deleted = self._composition
                self._composition = char
                self._all_selected = False
                self._mouse.has_selection = False
                self._emit(now_ms, char, 'selection_replace', ctx,
                           extra={'deleted_text': deleted[:200]})
            else:
                self._composition += char
                if len(self._composition) > BUFFER_MAX_LEN:
                    self._composition = self._composition[-BUFFER_MAX_LEN:]
                self._emit(now_ms, char, 'insert', ctx)
            return

        # ── Arrow keys clear selection ──
        if key in (keyboard.Key.left, keyboard.Key.right,
                   keyboard.Key.up, keyboard.Key.down):
            if not self._shift_held:
                self._all_selected = False
                self._mouse.has_selection = False
            self._emit(now_ms, key_str, 'navigation', ctx)
            return

        # Other special keys
        self._emit(now_ms, key_str, 'special', ctx)

    def _emit(self, ts: int, key_display: str, evt_type: str, ctx: str,
              extra: dict | None = None):
        """Build event dict and append to buffer."""
        event = {
            'ts': ts,
            'key': key_display,
            'type': evt_type,
            'context': ctx,
            'buffer_len': len(self._composition),
            'source': 'os_hook',
            'buffer': self._composition,
        }
        if extra:
            event.update(extra)
        with self._lock:
            self._buffer.append(event)

    def _analyze_composition(self):
        """Run composition analysis + refresh copilot-instructions on submit.

        Runs SYNCHRONOUSLY so copilot-instructions.md is updated before
        Copilot reads the file for this prompt.
        """
        root = self._root
        _err_log = root / 'logs' / '_os_hook_errors.log'
        # 1. Log composition
        composition = None
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                'chat_composition_analyzer',
                str(root / 'client' / 'chat_composition_analyzer.py'))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            composition = mod.analyze_and_log(root)
        except Exception as e:
            _err_log.write_text(f'compose: {e}\n', encoding='utf-8')

        # 1.5 Populate prompt journal from composition (feeds push cycle)
        if composition:
            try:
                self._write_journal_entry(root, composition)
            except Exception as e:
                try:
                    with open(_err_log, 'a', encoding='utf-8') as ef:
                        ef.write(f'journal: {e}\n')
                except Exception:
                    pass

        # 2. Reconstruct unsaid intent if high deletion ratio
        if composition:
            try:
                from glob import glob as _g
                import importlib.util as _il
                recon_hits = sorted(_g(str(root / 'src' / 'unsaid_recon_seq024*.py')))
                if recon_hits:
                    sp = _il.spec_from_file_location('unsaid_recon', recon_hits[-1])
                    rm = _il.module_from_spec(sp)
                    sp.loader.exec_module(rm)
                    rm.reconstruct_if_needed(root, composition)
            except Exception as e:
                _err_log.write_text(f'recon: {e}\n', encoding='utf-8')
        # 3. Refresh copilot-instructions.md with latest prompt data
        try:
            from glob import glob as _glob
            import importlib.util as _ilu
            hits = sorted(_glob(str(root / 'src' / 'dynamic_prompt_seq017*.py')))
            if hits:
                sp = _ilu.spec_from_file_location('dynamic_prompt', hits[-1])
                dm = _ilu.module_from_spec(sp)
                sp.loader.exec_module(dm)
                if hasattr(dm, 'inject_task_context'):
                    dm.inject_task_context(root)
        except Exception as e:
            import traceback
            _err_log.write_text(f'inject: {e}\n{traceback.format_exc()}', encoding='utf-8')

    def _write_journal_entry(self, root: Path, composition: dict):
        """Write a prompt_journal entry directly from composition data.

        This ensures the journal is populated automatically on every Enter,
        without depending on the copilot prompt_journal command being run.
        The push cycle's backward pass reads from this journal.
        """
        import hashlib
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        final_text = composition.get('final_text', '')
        if not final_text.strip():
            return

        signals = {
            'wpm': composition.get('wpm', 0),
            'chars_per_sec': composition.get('chars_per_sec', 0),
            'deletion_ratio': composition.get('deletion_ratio', 0),
            'intent_deletion_ratio': composition.get('intent_deletion_ratio', 0),
            'hesitation_count': len(composition.get('hesitation_windows', [])),
            'rewrite_count': len(composition.get('rewrites', [])),
            'typo_corrections': composition.get('typo_corrections', 0),
            'intentional_deletions': composition.get('intentional_deletions', 0),
            'total_keystrokes': composition.get('total_keystrokes', 0),
            'duration_ms': composition.get('duration_ms', 0),
        }

        # Simple intent classification from text
        text_lower = final_text.lower()
        if any(w in text_lower for w in ('fix', 'bug', 'error', 'broken', 'wrong')):
            intent = 'debugging'
        elif any(w in text_lower for w in ('add', 'create', 'build', 'implement', 'wire', 'new')):
            intent = 'building'
        elif any(w in text_lower for w in ('refactor', 'rename', 'move', 'split', 'restructure')):
            intent = 'restructuring'
        elif any(w in text_lower for w in ('test', 'verify', 'check', 'run')):
            intent = 'testing'
        elif any(w in text_lower for w in ('why', 'how', 'what', 'explain', 'analyze')):
            intent = 'exploring'
        else:
            intent = 'unknown'

        # Cognitive state from signals
        del_ratio = signals['deletion_ratio']
        hes_count = signals['hesitation_count']
        wpm = signals['wpm']
        if del_ratio > 0.4 or hes_count > 5:
            cog_state = 'frustrated'
        elif del_ratio > 0.2 or hes_count > 2:
            cog_state = 'hesitant'
        elif wpm > 60 and del_ratio < 0.1:
            cog_state = 'focused'
        elif wpm > 0:
            cog_state = 'neutral'
        else:
            cog_state = 'unknown'

        # Extract deleted words
        deleted_words = []
        for dw in composition.get('deleted_words', []):
            if isinstance(dw, dict):
                deleted_words.append(dw.get('word', ''))
            elif isinstance(dw, str):
                deleted_words.append(dw)

        # Module references from text
        import re
        module_refs = re.findall(r'\b(\w+_seq\d+)\b', final_text)

        # Session tracking
        journal_path = root / 'logs' / 'prompt_journal.jsonl'
        session_n = 0
        if journal_path.exists():
            try:
                lines = journal_path.read_text('utf-8').strip().splitlines()
                if lines:
                    last = json.loads(lines[-1])
                    session_n = last.get('session_n', 0)
            except Exception:
                pass
        session_n += 1

        entry = {
            'ts': now.isoformat(),
            'session_n': session_n,
            'session_id': hashlib.md5(now.date().isoformat().encode()).hexdigest()[:12],
            'msg': final_text,
            'intent': intent,
            'cognitive_state': cog_state,
            'signals': signals,
            'deleted_words': deleted_words,
            'rewrites': [{'old': r.get('old', ''), 'new': r.get('new', '')}
                         for r in composition.get('rewrites', [])],
            'module_refs': module_refs,
            'source': 'os_hook_auto',
        }

        journal_path.parent.mkdir(parents=True, exist_ok=True)
        with open(journal_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')

    def on_release(self, key):
        if not self._running:
            return
        # Track modifier releases
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._ctrl_held = False
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._shift_held = False
        key_str = self._key_to_str(key)
        self._ctx.on_key(key_str, False)
        return

    def flush(self):
        with self._lock:
            if not self._buffer:
                return 0
            batch = self._buffer[:]
            self._buffer.clear()

        try:
            with open(self._log_path, 'a', encoding='utf-8') as f:
                for event in batch:
                    f.write(json.dumps(event) + '\n')
            return len(batch)
        except OSError:
            return 0

    def stop(self):
        self._running = False
        self.flush()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    global _WORKSPACE_NAME
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.')
    _WORKSPACE_NAME = root.name  # e.g. "keystroke-telemetry"

    mouse_tracker = MouseSelectionTracker()
    recorder = KeystrokeRecorder(root, mouse_tracker)

    # Start pynput listeners (keyboard + mouse)
    kb_listener = keyboard.Listener(
        on_press=recorder.on_press,
        on_release=recorder.on_release,
    )
    mouse_listener = pynput_mouse.Listener(
        on_click=mouse_tracker.on_click,
    )
    kb_listener.start()
    mouse_listener.start()

    print(json.dumps({"status": "started", "pid": os.getpid(), "log": str(recorder._log_path)}))
    sys.stdout.flush()

    # Periodic flush loop
    try:
        while kb_listener.is_alive():
            time.sleep(FLUSH_INTERVAL_S)
            n = recorder.flush()
            if n > 0:
                # Status heartbeat — extension reads these
                print(json.dumps({
                    "status": "flush",
                    "n": n,
                    "context": recorder._ctx.context,
                    "buffer_len": len(recorder._composition),
                    "focused": _is_vscode_focused(),
                }))
                sys.stdout.flush()

            # Idle detection
            if time.time() - recorder._last_activity > IDLE_TIMEOUT_S:
                print(json.dumps({"status": "idle"}))
                sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        recorder.stop()
        kb_listener.stop()
        mouse_listener.stop()
        print(json.dumps({"status": "stopped"}))
        sys.stdout.flush()


if __name__ == '__main__':
    main()
