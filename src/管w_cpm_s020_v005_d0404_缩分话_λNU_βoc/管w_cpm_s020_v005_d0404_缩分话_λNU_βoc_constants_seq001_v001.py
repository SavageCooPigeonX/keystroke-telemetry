"""管w_cpm_s020_v005_d0404_缩分话_λNU_βoc_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 27 lines | ~319 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json
import re

COPILOT_PATH = '.github/copilot-instructions.md'

SNAPSHOT_PATH = 'logs/prompt_telemetry_latest.json'

AUDIT_PATH = 'logs/copilot_prompt_audit.json'

PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'

PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'


BLOCK_MARKERS = {
    'task_context': ('<!-- pigeon:task-context -->', '<!-- /pigeon:task-context -->'),
    'intent_backlog': ('<!-- pigeon:intent-backlog -->', '<!-- /pigeon:intent-backlog -->'),
    'task_queue': ('<!-- pigeon:task-queue -->', '<!-- /pigeon:task-queue -->'),
    'operator_state': ('<!-- pigeon:operator-state -->', '<!-- /pigeon:operator-state -->'),
    'prompt_telemetry': (PROMPT_BLOCK_START, PROMPT_BLOCK_END),
    'entropy_map': ('<!-- pigeon:entropy-map -->', '<!-- /pigeon:entropy-map -->'),
    'entropy_red_layer': ('<!-- pigeon:entropy-red-layer -->', '<!-- /pigeon:entropy-red-layer -->'),
    'auto_index': ('<!-- pigeon:auto-index -->', '<!-- /pigeon:auto-index -->'),
    'bug_voices': ('<!-- pigeon:bug-voices -->', '<!-- /pigeon:bug-voices -->'),
    'probe_resolutions': ('<!-- pigeon:probe-resolutions -->', '<!-- /pigeon:probe-resolutions -->'),
}
