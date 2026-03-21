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
except ImportError:
    print(json.dumps({"status": "error", "msg": "pynput not installed"}))
    sys.exit(1)

# ── Configuration ────────────────────────────────────────────────────────────

FLUSH_INTERVAL_S = 5       # Write to disk every 5 seconds
IDLE_TIMEOUT_S = 300       # 5 min idle → pause recording
BUFFER_MAX_LEN = 500       # Max composition buffer size
VSCODE_WINDOW_MATCH = 'Visual Studio Code'

# ── Windows API for foreground window ────────────────────────────────────────

user32 = ctypes.windll.user32


def _get_foreground_title() -> str:
    hwnd = user32.GetForegroundWindow()
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value


def _is_vscode_focused() -> bool:
    try:
        return VSCODE_WINDOW_MATCH in _get_foreground_title()
    except Exception:
        return False


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
            elif key_str == 'l' and self._shift:
                self.context = 'chat'       # Ctrl+Shift+L = Copilot Chat (new)
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
    def __init__(self, root: Path):
        self._root = root
        self._log_path = root / 'logs' / 'os_keystrokes.jsonl'
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._buffer: list[dict] = []
        self._composition = ''  # Current typing buffer
        self._last_activity = time.time()
        self._ctx = ContextTracker()
        self._lock = threading.Lock()
        self._running = True

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

        # Update composition buffer
        if key == keyboard.Key.backspace:
            if self._composition:
                self._composition = self._composition[:-1]
            evt_type = 'backspace'
            key_display = 'Backspace'
        elif key == keyboard.Key.enter:
            evt_type = 'submit'
            key_display = 'Enter'
            self._composition = ''
        elif key == keyboard.Key.esc:
            evt_type = 'discard'
            key_display = 'Escape'
            self._composition = ''
        elif key == keyboard.Key.space:
            self._composition += ' '
            evt_type = 'insert'
            key_display = ' '
        elif hasattr(key, 'char') and key.char:
            self._composition += key.char
            if len(self._composition) > BUFFER_MAX_LEN:
                self._composition = self._composition[-BUFFER_MAX_LEN:]
            evt_type = 'insert'
            key_display = key.char
        else:
            evt_type = 'special'
            key_display = key_str

        event = {
            'ts': now_ms,
            'key': key_display,
            'type': evt_type,
            'context': ctx,
            'buffer_len': len(self._composition),
            'source': 'os_hook',
        }

        # Only include buffer content for chat context (privacy: don't log editor code)
        if ctx == 'chat':
            event['buffer'] = self._composition

        with self._lock:
            self._buffer.append(event)
        return

    def on_release(self, key):
        if not self._running:
            return
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
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.')
    recorder = KeystrokeRecorder(root)

    # Start pynput listener
    listener = keyboard.Listener(
        on_press=recorder.on_press,
        on_release=recorder.on_release,
    )
    listener.start()

    print(json.dumps({"status": "started", "pid": os.getpid(), "log": str(recorder._log_path)}))
    sys.stdout.flush()

    # Periodic flush loop
    try:
        while listener.is_alive():
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
        listener.stop()
        print(json.dumps({"status": "stopped"}))
        sys.stdout.flush()


if __name__ == '__main__':
    main()
