"""u_pj_s019_v003_d0404_λNU_βoc_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 55 lines | ~513 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json
import re

JOURNAL_PATH   = 'logs/prompt_journal.jsonl'

SNAPSHOT_PATH  = 'logs/prompt_telemetry_latest.json'

COMPS_PATH     = 'logs/chat_compositions.jsonl'

PROMPT_COMPS_PATH = 'logs/prompt_compositions.jsonl'

HEAT_PATH      = 'file_heat_map.json'

TASK_PATH      = 'task_queue.json'

PROFILE_PATH   = 'operator_profile.md'

EDIT_PAIRS     = 'logs/edit_pairs.jsonl'

MUTATIONS_PATH = 'logs/copilot_prompt_mutations.json'

COPILOT_PATH   = '.github/copilot-instructions.md'

MAX_COMP_AGE_MS = 120_000    # 2min window — compositions may lag behind prompt submission

TIGHT_WINDOW_MS = 500        # ±500ms for high-confidence direct binding

MIN_TEXT_MATCH_SCORE = 0.4   # lowered: partial prompt text often matches loosely


PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'

PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'

TASK_COMPLETE_HOOK_MARKERS = (
    'you were about to complete but a hook blocked you with the following message',
    'you have not yet marked the task as complete using the task_complete tool',
)


INTENT_MAP = {
    'fix':       'debugging',  'bug':     'debugging',  'error':  'debugging',
    'broke':     'debugging',  'wrong':   'debugging',  'fail':   'debugging',
    'implement': 'building',   'build':   'building',   'create': 'building',
    'add':       'building',   'wire':    'building',   'make':   'building',
    'refactor':  'restructuring', 'split': 'restructuring', 'rename': 'restructuring',
    'move':      'restructuring', 'clean': 'restructuring',
    'test':      'testing',    'run':     'testing',    'verify': 'testing',
    'what':      'exploring',  'how':     'exploring',  'why':    'exploring',
    'show':      'exploring',  'find':    'exploring',  'check':  'exploring',
    'push':      'shipping',   'commit':  'shipping',   'deploy': 'shipping',
    'update':    'documenting','readme':  'documenting','doc':    'documenting',
    'continu':   'continuing',
}
