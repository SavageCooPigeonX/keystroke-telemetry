"""escalation_engine_data_loaders_seq003_v001_rollback_check_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 6 lines | ~82 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _has_rollback_version(entry: dict) -> bool:
    """Check if a module has a previous version to rollback to."""
    history = entry.get('history', [])
    return len(history) >= 1 and entry.get('ver', 1) > 1
