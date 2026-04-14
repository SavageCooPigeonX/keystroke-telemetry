"""git_plugin_operator_profile_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 43 lines | ~433 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import os
import re

def _parse_operator_profile(root: Path) -> dict | None:
    """Parse operator_profile.md → metrics dict. Returns None if file missing."""
    prof_path = root / 'operator_profile.md'
    if not prof_path.exists():
        return None
    try:
        text = prof_path.read_text(encoding='utf-8')
    except Exception:
        return None

    def _re(pattern: str, default: str) -> str:
        m = re.search(pattern, text)
        return m.group(1) if m else default

    return {
        'messages':    int(_re(r'(\d+) messages ingested', '0') or '0'),
        'dominant':    _re(r'\*\*Dominant state:\s*(\w+)\*\*', 'neutral'),
        'submit_rate': int(_re(r'\*\*Submit rate:.*?\((\d+)%\)\*\*', '0') or '0'),
        'avg_wpm':     float(_re(r'\|\s*WPM\s*\|[^|]+\|[^|]+\|\s*([\d.]+)\s*\|', '0') or '0'),
        'avg_del':     float(_re(r'\|\s*Deletion\s*%\s*\|[^|]+\|[^|]+\|\s*([\d.]+)%', '0') or '0'),
        'avg_hes':     float(_re(r'\|\s*Hesitation\s*\|[^|]+\|[^|]+\|\s*([\d.]+)\s*\|', '0') or '0'),
        'active_hours': _re(r'\*\*Active hours:\*\*\s*(.+)', '').strip(),
    }


def _load_coaching_prose(root: Path) -> str | None:
    """Load LLM-generated coaching prose from operator_coaching.md if present."""
    coaching_path = root / 'operator_coaching.md'
    if not coaching_path.exists():
        return None
    try:
        text = coaching_path.read_text(encoding='utf-8')
        m = re.search(r'<!-- coaching:count=\d+ -->\n.*?\n(.*?)<!-- /coaching -->', text, re.DOTALL)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None
