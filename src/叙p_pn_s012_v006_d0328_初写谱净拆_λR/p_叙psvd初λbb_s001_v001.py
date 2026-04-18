"""叙p_pn_s012_v006_d0328_初写谱净拆_λR_build_briefs_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 26 lines | ~285 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _build_file_briefs(root: Path, changed_py: list[str], registry: dict) -> list[dict]:
    briefs = []
    for rel in changed_py:
        entry = registry.get(rel)
        if entry:
            briefs.append({
                'name': entry.get('name', Path(rel).stem),
                'path': rel,
                'seq': entry.get('seq', '?'),
                'ver': entry.get('ver', 0),
                'desc': entry.get('desc', ''),
                'intent': entry.get('intent', ''),
                'tokens': entry.get('tokens', 0),
                'history_len': len(entry.get('history', [])),
            })
        else:
            p = root / rel
            try: tokens = max(1, len(p.read_text(encoding='utf-8')) // 4) if p.exists() else 0
            except Exception: tokens = 0
            briefs.append({'name': Path(rel).stem, 'path': rel, 'seq': '-',
                           'ver': 0, 'desc': rel, 'intent': '',
                           'tokens': tokens, 'history_len': 0})
    return briefs
