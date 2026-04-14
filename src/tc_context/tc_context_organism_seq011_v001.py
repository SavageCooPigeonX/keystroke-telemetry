"""tc_context_organism_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 18 lines | ~172 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _load_context_organism_narrative(ctx: dict, repo_root: Path) -> None:
    ci_path = repo_root / '.github' / 'copilot-instructions.md'
    if not ci_path.exists():
        return
    try:
        ci_text = ci_path.read_text('utf-8', errors='ignore')
        m = re.search(r'> (the organism .+?)$', ci_text, re.MULTILINE)
        if m:
            ctx['organism_narrative'] = m.group(1)[:300]
        m2 = re.search(r'INTERPRETED INTENT: (.+?)$', ci_text, re.MULTILINE)
        if m2:
            ctx['copilot_intent'] = m2.group(1)[:200]
    except Exception:
        pass
