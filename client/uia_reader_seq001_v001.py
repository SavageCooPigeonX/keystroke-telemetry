"""
uia_reader_seq001_v001.py — Windows UI Automation reader for live chat input capture.

Black hat approach: bypass VS Code's APIs entirely. Read the accessibility
tree that Chromium exposes to the OS. Every DOM element (including the
Copilot chat textarea) is an IAccessible/UIA element.

REQUIRES: editor.accessibilitySupport = "on" in VS Code settings.
Without it, all Monaco editors return "The editor is not accessible at
this time" instead of actual content. The extension enables this on activate.

This captures:
  - Exact live text in the focused text field via ValuePattern/TextPattern
  - Character-level diffs between polls (insertions AND deletions)
  - Context classification: chat vs editor vs terminal vs search
  - Composition buffer reconstruction with full deletion history

Architecture:
  - Polls GetFocusedElement() at 50ms (20 reads/sec)
  - Uses BoundingRectangle + ancestor tree walking for context detection
  - Diffs via prefix/suffix matching for O(1) change detection
  - Writes to logs/uia_live.jsonl

Usage: py client/uia_reader_seq001_v001.py <project_root>
       py client/uia_reader_seq001_v001.py <project_root> --diag   (diagnostic: log everything)
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── UIA bootstrap ────────────────────────────────────────────────────────────

def _init_uia():
    """Initialize COM + UI Automation. Returns (uia, consts dict)."""
    import comtypes
    import comtypes.client
    comtypes.CoInitialize()
    comtypes.client.GetModule('UIAutomationCore.dll')
    from comtypes.gen.UIAutomationClient import (
        CUIAutomation, IUIAutomation,
        IUIAutomationValuePattern,
        IUIAutomationTextPattern,
        IUIAutomationLegacyIAccessiblePattern,
    )
    uia = comtypes.CoCreateInstance(
        CUIAutomation._reg_clsid_,
        interface=IUIAutomation,
        clsctx=comtypes.CLSCTX_INPROC_SERVER,
    )
    return uia, {
        'IUIAutomationValuePattern': IUIAutomationValuePattern,
        'IUIAutomationTextPattern': IUIAutomationTextPattern,
        'IUIAutomationLegacyIAccessiblePattern': IUIAutomationLegacyIAccessiblePattern,
        'UIA_ValuePatternId': 10002,
        'UIA_TextPatternId': 10014,
        'UIA_LegacyIAccessiblePatternId': 10018,
    }


# ── Text extraction ─────────────────────────────────────────────────────────

ACCESSIBILITY_PLACEHOLDER = 'not accessible at this time'

def _get_text(element, consts) -> str:
    """Extract text from focused element via every available pattern."""
    # ValuePattern — textarea, input fields, Monaco with accessibility on
    try:
        pat = element.GetCurrentPattern(consts['UIA_ValuePatternId'])
        if pat:
            vp = pat.QueryInterface(consts['IUIAutomationValuePattern'])
            val = vp.CurrentValue
            if val and ACCESSIBILITY_PLACEHOLDER not in val:
                return val
    except Exception:
        pass

    # TextPattern — document/rich text controls
    try:
        pat = element.GetCurrentPattern(consts['UIA_TextPatternId'])
        if pat:
            tp = pat.QueryInterface(consts['IUIAutomationTextPattern'])
            text = tp.DocumentRange.GetText(10000)
            if text and ACCESSIBILITY_PLACEHOLDER not in text:
                return text
    except Exception:
        pass

    # LegacyIAccessiblePattern — older controls
    try:
        pat = element.GetCurrentPattern(consts['UIA_LegacyIAccessiblePatternId'])
        if pat:
            lap = pat.QueryInterface(consts['IUIAutomationLegacyIAccessiblePattern'])
            val = lap.CurrentValue
            if val and ACCESSIBILITY_PLACEHOLDER not in val:
                return val
    except Exception:
        pass

    return ''


# ── Context classification ───────────────────────────────────────────────────

def _classify(element, uia) -> tuple[str, dict]:
    """Classify focused element context: chat, editor, terminal, search, unknown.

    Strategy:
      1. Check element name/automationId for keywords
      2. Walk ancestor tree for panel identification
      3. Use BoundingRectangle as positional heuristic
    """
    try:
        name = element.CurrentName or ''
        cls = element.CurrentClassName or ''
        ctrl = element.CurrentControlType
        auto_id = element.CurrentAutomationId or ''
        rect = element.CurrentBoundingRectangle
    except Exception:
        return 'unknown', {}

    info = {
        'name': name[:80], 'class': cls[:40], 'ctrl_type': ctrl,
        'auto_id': auto_id[:80],
        'x': rect.left, 'y': rect.top,
        'w': rect.right - rect.left, 'h': rect.bottom - rect.top,
    }

    nl = name.lower()
    al = auto_id.lower()

    # Direct match on element
    if 'chat' in nl or 'chat' in al or 'copilot' in nl:
        return 'chat', info
    if 'terminal' in nl or 'terminal' in al or 'xterm' in nl:
        return 'terminal', info
    if 'search' in nl or 'find' in nl or 'search' in al:
        return 'search', info

    # Walk ancestors (up to 12 levels)
    try:
        walker = uia.ControlViewWalker
        parent = walker.GetParentElement(element)
        for _ in range(12):
            if not parent:
                break
            try:
                pn = (parent.CurrentName or '').lower()
                pa = (parent.CurrentAutomationId or '').lower()
            except Exception:
                break

            if 'chat' in pn or 'copilot' in pn or 'chat' in pa:
                return 'chat', info
            if 'terminal' in pn or 'xterm' in pn or 'terminal' in pa:
                return 'terminal', info
            if 'editor' in pn or 'editor' in pa:
                return 'editor', info
            if 'search' in pn or 'search' in pa:
                return 'search', info

            parent = walker.GetParentElement(parent)
    except Exception:
        pass

    # Heuristic: text-like controls default to 'editor'
    if ctrl in (50004, 50030):  # Edit or Document
        return 'editor', info

    return 'unknown', info


# ── Diff engine ──────────────────────────────────────────────────────────────

def _diff(old: str, new: str) -> dict | None:
    """Character-level diff. Returns None if no change."""
    if old == new:
        return None
    # Common prefix
    i = 0
    while i < len(old) and i < len(new) and old[i] == new[i]:
        i += 1
    # Common suffix
    jo, jn = len(old), len(new)
    while jo > i and jn > i and old[jo - 1] == new[jn - 1]:
        jo -= 1
        jn -= 1
    return {
        'pos': i,
        'deleted': old[i:jo],
        'inserted': new[i:jn],
        'del_len': jo - i,
        'ins_len': jn - i,
    }


# ── Main reader loop ────────────────────────────────────────────────────────

POLL_MS = 50

class UIAReader:
    def __init__(self, root: Path, diag: bool = False):
        self._root = root
        self._diag = diag
        self._log_path = root / 'logs' / 'uia_live.jsonl'
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._prev_text = ''
        self._prev_ctx = ''
        self._deletions: list[str] = []
        self._running = True

    def run(self):
        uia, consts = _init_uia()
        self._emit_status('started')

        while self._running:
            time.sleep(POLL_MS / 1000.0)
            try:
                el = uia.GetFocusedElement()
                if not el:
                    continue
            except Exception:
                continue

            ctx, info = _classify(el, uia)
            text = _get_text(el, consts)
            ts = datetime.now(timezone.utc).isoformat()

            # ── Diagnostic mode: log everything ──
            if self._diag:
                self._write({
                    'ts': ts, 'event': 'diag', 'context': ctx,
                    'text_len': len(text),
                    'text_preview': text[:200] if text else '',
                    **info,
                })
                print(json.dumps({
                    'ctx': ctx, 'ctrl': info.get('ctrl_type', 0),
                    'cls': info.get('class', ''), 'name': info.get('name', '')[:40],
                    'text': (text[:80] if text else ''), 'len': len(text),
                    'rect': f"{info.get('x',0)},{info.get('y',0)} {info.get('w',0)}x{info.get('h',0)}",
                }))
                sys.stdout.flush()
                continue

            # ── Context switch ──
            if ctx != self._prev_ctx:
                self._write({
                    'ts': ts, 'event': 'context_switch',
                    'from': self._prev_ctx, 'to': ctx, **info,
                })
                self._prev_ctx = ctx
                # Reset on non-text context
                if ctx not in ('chat', 'editor', 'text_input', 'search'):
                    self._prev_text = ''
                    self._deletions.clear()

            # ── Text diff (only on text-bearing contexts) ──
            if ctx in ('chat', 'editor', 'text_input', 'search'):
                d = _diff(self._prev_text, text)
                if d:
                    if d['deleted']:
                        self._deletions.append(d['deleted'])
                    entry = {
                        'ts': ts, 'event': 'text_changed', 'context': ctx,
                        'text': text, 'diff': d,
                        'deletions_total': len(self._deletions),
                    }
                    # Only include deletion history for chat (privacy)
                    if ctx == 'chat':
                        entry['deletion_history'] = self._deletions[-20:]
                    self._write(entry)

                    # Heartbeat for chat activity
                    if ctx == 'chat':
                        print(json.dumps({
                            'status': 'chat_active',
                            'text_len': len(text),
                            'del_count': len(self._deletions),
                        }))
                        sys.stdout.flush()

                self._prev_text = text

    def _write(self, entry: dict):
        try:
            with open(self._log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        except OSError:
            pass

    def _emit_status(self, status: str, **extra):
        msg = {'status': status, 'pid': os.getpid(), 'poll_ms': POLL_MS,
               'log': str(self._log_path), 'diag': self._diag, **extra}
        print(json.dumps(msg))
        sys.stdout.flush()

    def stop(self):
        self._running = False


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.')
    diag = '--diag' in sys.argv
    reader = UIAReader(root, diag=diag)
    try:
        reader.run()
    except KeyboardInterrupt:
        reader.stop()
        print(json.dumps({'status': 'stopped'}))
        sys.stdout.flush()


if __name__ == '__main__':
    main()
