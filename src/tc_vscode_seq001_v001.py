"""VS Code window detection via Windows API."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import ctypes

user32 = ctypes.windll.user32

_WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))


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
