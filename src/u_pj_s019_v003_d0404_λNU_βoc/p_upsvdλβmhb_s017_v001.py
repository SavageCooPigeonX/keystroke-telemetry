"""u_pj_s019_v003_d0404_λNU_βoc_meta_hook_builder_seq017_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v001 | 44 lines | ~388 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import re
from .p_upsvdλβrsd_s013_v001 import _running_stats
from .p_upsvdλβtl_s012_v001 import _active_tasks, _hot_modules, _mutation_count

def _build_meta_hook_entry(
    root: Path,
    now: datetime,
    msg: str,
    files_open: list[str],
    session_n: int,
    meta_prompt_kind: str,
) -> dict:
    return {
        'ts':               now.isoformat(),
        'session_n':        session_n,
        'msg':              msg,
        'msg_len':          len(msg),
        'files_open':       files_open,
        'prompt_kind':      'meta_hook',
        'intent':           'meta',
        'module_refs':      [],
        'cognitive_state':  'unknown',
        'signals':          {},
        'composition_binding': {
            'matched': False,
            'source': None,
            'age_ms': None,
            'key': None,
        },
        'deleted_words':    [],
        'rewrites':         [],
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
        'meta_prompt_kind': meta_prompt_kind,
    }
