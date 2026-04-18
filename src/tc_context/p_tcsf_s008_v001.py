"""tc_context_seq001_v001_self_fix_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 14 lines | ~129 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _load_context_self_fix(ctx: dict, repo_root: Path) -> None:
    sf = repo_root / 'logs' / 'self_fix_report.md'
    if not sf.exists():
        return
    try:
        text = sf.read_text('utf-8', errors='ignore')
        crits = re.findall(r'\[CRITICAL\]\s+(\w+)\s+in\s+`([^`]+)`', text)
        ctx['critical_bugs'] = [{'type': t, 'file': f} for t, f in crits[:6]]
    except Exception:
        pass
