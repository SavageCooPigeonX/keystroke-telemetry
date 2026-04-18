"""u_pj_s019_v003_d0404_λNU_βoc_post_append_seq026_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 026 | VER: v001 | 13 lines | ~163 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _log_enriched_entry_handle_post_append(root: Path, entry: dict, cog_state: str, signals: dict, deleted_words: list, msg: str) -> None:
    entry['_root'] = root
    snapshot = _build_snapshot(entry)
    entry.pop('_root', None)
    _write_latest_snapshot(root, snapshot)
    _refresh_copilot_instructions(root, snapshot)
    _log_enriched_entry_run_gemini_enricher(root, msg, deleted_words, cog_state, signals)
    _log_enriched_entry_write_training_pair(root, msg)
    _log_enriched_entry_run_staleness_alert(root)
