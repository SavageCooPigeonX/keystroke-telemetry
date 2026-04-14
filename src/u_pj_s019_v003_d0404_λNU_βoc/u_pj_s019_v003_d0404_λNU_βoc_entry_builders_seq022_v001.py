"""u_pj_s019_v003_d0404_λNU_βoc_entry_builders_seq022_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 022 | VER: v001 | 39 lines | ~494 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import re

def _log_enriched_entry_build_enriched_entry(now: datetime, session_n: int, msg: str, files_open: list[str], meta_prompt_kind: str, cog_state: str, signals: dict, binding: dict, deleted_words: list, rewrites: list, root: Path) -> dict:
    entry = {
        'ts':               now.isoformat(),
        'session_n':        session_n,
        'msg':              msg,
        'msg_len':          len(msg),
        'files_open':       files_open,
        'prompt_kind':      'meta_hook' if meta_prompt_kind else 'operator',
        'intent':           'meta' if meta_prompt_kind else _classify_intent(msg),
        'module_refs':      [] if meta_prompt_kind else _extract_module_refs(msg),
        'cognitive_state':  cog_state,
        'signals':          signals,
        'composition_binding': binding,
        'deleted_words':    deleted_words,
        'rewrites':         rewrites,
        'task_queue':       _active_tasks(root),
        'hot_modules':      _hot_modules(root),
        'prompt_mutations': _mutation_count(root),
        'running':          _running_stats(root),
        'provenance': {
            'measured': ['ts', 'session_n', 'msg', 'msg_len', 'files_open',
                         'signals', 'deleted_words', 'rewrites', 'composition_binding'],
            'derived':  ['intent', 'module_refs', 'cognitive_state',
                         'task_queue', 'hot_modules', 'prompt_mutations', 'running'],
        },
    }
    if meta_prompt_kind:
        entry['meta_prompt_kind'] = meta_prompt_kind
    return entry


def _log_enriched_entry_build_meta_hook(root: Path, now: datetime, msg: str, files_open: list[str], session_n: int, meta_prompt_kind: str) -> dict:
    entry = _build_meta_hook_entry(root, now, msg, files_open, session_n, meta_prompt_kind)
    return entry
