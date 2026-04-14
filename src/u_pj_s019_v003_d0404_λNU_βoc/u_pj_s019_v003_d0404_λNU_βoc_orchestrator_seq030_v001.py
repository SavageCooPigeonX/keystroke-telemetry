"""u_pj_s019_v003_d0404_λNU_βoc_orchestrator_seq030_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 030 | VER: v001 | 45 lines | ~491 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json
import re

def log_enriched_entry(root: Path, msg: str, files_open: list[str], session_n: int) -> dict:
    """Build and append one fully-enriched journal entry. Returns the entry.

    Signal/narrative separation:
    1. Write raw measured signal to prompt_signal_raw.jsonl (ground truth)
    2. Build enriched entry with interpretation (intent, state, predictions)
    3. Enriched entry is tagged with provenance markers
    """
    now = datetime.now(timezone.utc)
    meta_prompt_kind = 'task_complete_hook' if _is_meta_hook_message(msg) else None
    if meta_prompt_kind:
        entry = _log_enriched_entry_build_meta_hook(root, now, msg, files_open, session_n, meta_prompt_kind)
        if _should_skip_duplicate_meta_prompt(root, msg, meta_prompt_kind):
            return entry
        _log_enriched_entry_append_to_journal(root, entry)
        return entry

    _force_fresh_composition(root)
    _refresh_prompt_compositions(root)
    comp_match = _select_composition(root, now, msg, session_n=session_n)
    comp = comp_match['entry'] if comp_match else None

    signals, deleted_words, rewrites, cog_state, binding = _log_enriched_entry_extract_from_composition(comp_match, comp)

    _log_enriched_entry_write_raw_signal(root, msg, files_open, session_n, signals, deleted_words, rewrites, binding)

    entry = _log_enriched_entry_build_enriched_entry(now, session_n, msg, files_open, meta_prompt_kind, cog_state, signals, binding, deleted_words, rewrites, root)

    if _should_skip_duplicate_meta_prompt(root, msg, meta_prompt_kind):
        return entry

    _log_enriched_entry_append_to_journal(root, entry)

    if meta_prompt_kind:
        return entry

    _log_enriched_entry_handle_post_append(root, entry, cog_state, signals, deleted_words, msg)

    return entry
