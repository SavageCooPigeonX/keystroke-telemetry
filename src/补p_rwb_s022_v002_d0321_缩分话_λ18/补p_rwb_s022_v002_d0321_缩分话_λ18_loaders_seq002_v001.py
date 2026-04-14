"""补p_rwb_s022_v002_d0321_缩分话_λ18_loaders_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 51 lines | ~403 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import glob as _glob
import importlib.util
import json

def _load_src(pattern: str, *symbols):
    matches = sorted(_glob.glob(f'src/{pattern}'))
    if not matches:
        return None
    spec = importlib.util.spec_from_file_location('_dyn', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if len(symbols) == 1:
        return getattr(mod, symbols[0], None)
    return tuple(getattr(mod, s, None) for s in symbols)


def _load_ai_responses(root: Path) -> list[dict]:
    """Load ai_responses.jsonl — each line is a JSON record with ts, prompt, response."""
    p = root / 'logs' / 'ai_responses.jsonl'
    if not p.exists():
        return []
    entries = []
    for line in p.read_text('utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries


def _load_os_keystrokes(root: Path) -> list[dict]:
    """Load os_keystrokes.jsonl sorted by ts (ms epoch)."""
    p = root / 'logs' / 'os_keystrokes.jsonl'
    if not p.exists():
        return []
    events = []
    for line in p.read_text('utf-8', errors='replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    events.sort(key=lambda e: e.get('ts', 0))
    return events
