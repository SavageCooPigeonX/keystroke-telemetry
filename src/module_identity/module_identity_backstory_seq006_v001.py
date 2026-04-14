"""module_identity_backstory_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 23 lines | ~224 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _extract_backstory(root: Path, name: str) -> list[str]:
    """Extract per-module narrative fragments from push_narratives."""
    narr_dir = root / 'docs' / 'push_narratives'
    if not narr_dir.exists():
        return []
    fragments = []
    pattern = re.compile(rf'\b{re.escape(name)}\b', re.IGNORECASE)
    for f in sorted(narr_dir.glob('*.md'), reverse=True)[:20]:
        try:
            text = f.read_text('utf-8', errors='replace')
        except Exception:
            continue
        for para in text.split('\n\n'):
            if pattern.search(para) and len(para) > 40:
                cleaned = para.strip()[:500]
                fragments.append(cleaned)
                if len(fragments) >= 5:
                    return fragments
    return fragments
