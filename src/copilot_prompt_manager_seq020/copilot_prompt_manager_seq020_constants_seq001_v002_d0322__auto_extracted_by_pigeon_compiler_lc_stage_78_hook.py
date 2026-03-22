"""copilot_prompt_manager_seq020_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 22 lines | ~200 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 1
# ──────────────────────────────────────────────
import json

COPILOT_PATH = '.github/copilot-instructions.md'

SNAPSHOT_PATH = 'logs/prompt_telemetry_latest.json'

AUDIT_PATH = 'logs/copilot_prompt_audit.json'


PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'

PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'


BLOCK_MARKERS = {
    'task_context': ('<!-- pigeon:task-context -->', '<!-- /pigeon:task-context -->'),
    'task_queue': ('<!-- pigeon:task-queue -->', '<!-- /pigeon:task-queue -->'),
    'operator_state': ('<!-- pigeon:operator-state -->', '<!-- /pigeon:operator-state -->'),
    'prompt_telemetry': (PROMPT_BLOCK_START, PROMPT_BLOCK_END),
    'auto_index': ('<!-- pigeon:auto-index -->', '<!-- /pigeon:auto-index -->'),
}
