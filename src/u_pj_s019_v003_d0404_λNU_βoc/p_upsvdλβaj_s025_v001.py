"""u_pj_s019_v003_d0404_λNU_βoc_append_journal_seq025_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 025 | VER: v001 | 10 lines | ~110 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re
from .p_u_pj_s001_v001 import JOURNAL_PATH

def _log_enriched_entry_append_to_journal(root: Path, entry: dict) -> None:
    journal_path = root / JOURNAL_PATH
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with open(journal_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
