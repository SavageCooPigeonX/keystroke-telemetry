"""tc_context_bugs_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 18 lines | ~148 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _load_context_bug_voices(ctx: dict, repo_root: Path) -> None:
    bp = repo_root / 'docs' / 'BUG_PROFILES.md'
    if not bp.exists():
        return
    try:
        text = bp.read_text('utf-8', errors='ignore')
        demons = re.findall(r'\*Demon name: (.+?)\*', text)
        hosts = re.findall(r'### (\S+)\n', text)
        ctx['bug_demons'] = [
            {'host': h, 'demon': d}
            for h, d in zip(hosts, demons)
        ][:8]
    except Exception:
        pass
