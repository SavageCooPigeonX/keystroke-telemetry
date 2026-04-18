"""u_pj_s019_v003_d0404_λNU_βoc_skip_duplicate_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 17 lines | ~149 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re
from .p_u_pj_s001_v001 import JOURNAL_PATH
from .p_u_pj_s002_v001 import _read_jsonl
from .p_upsvdλβmh_s005_v001 import _is_meta_hook_message

def _should_skip_duplicate_meta_prompt(root: Path, msg: str, meta_prompt_kind: str | None) -> bool:
    if not meta_prompt_kind:
        return False
    entries = _read_jsonl(root / JOURNAL_PATH)
    if not entries:
        return False
    last = entries[-1]
    if last.get('msg') != msg:
        return False
    if last.get('meta_prompt_kind') == meta_prompt_kind:
        return True
    return _is_meta_hook_message(str(last.get('msg', '')))
