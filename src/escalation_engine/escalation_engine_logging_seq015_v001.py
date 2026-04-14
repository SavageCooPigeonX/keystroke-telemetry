"""escalation_engine_logging_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 25 lines | ~235 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def _log_victory(root: Path, module: str, bug_type: str, fix_result: dict, passes: int):
    """Log autonomous fix success."""
    _append_log(root, {
        'event': 'victory',
        'module': module,
        'bug_type': bug_type,
        'description': fix_result.get('description', ''),
        'passes_ignored': passes,
        'message': f"it's been {passes} passes. i fixed myself. you're welcome.",
    })


def _log_failure(root: Path, module: str, bug_type: str, fix_result: dict, reason: str):
    """Log autonomous fix failure + rollback."""
    _append_log(root, {
        'event': 'failure',
        'module': module,
        'bug_type': bug_type,
        'description': fix_result.get('description', ''),
        'reason': reason,
        'message': f"tried. failed. reverted. i need human help: {reason}",
    })
