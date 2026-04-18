"""escalation_engine_seq001_v001_status_seq021_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 021 | VER: v001 | 23 lines | ~240 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def get_status(root: Path) -> dict:
    """Get current escalation status for all tracked modules."""
    state = _load_state(root)
    levels = {}
    for mod, ms in state.get('modules', {}).items():
        level = ms.get('level', 0)
        level_name = LEVEL_NAMES.get(level, f'L{level}')
        levels.setdefault(level_name, []).append({
            'module': mod,
            'bug_type': ms.get('bug_type'),
            'confidence': ms.get('confidence', 0),
            'passes': ms.get('passes_ignored', 0),
            'countdown': ms.get('countdown', WARN_COUNTDOWN) if level == 3 else None,
        })
    return {
        'levels': levels,
        'total_tracked': len(state.get('modules', {})),
        'total_autonomous_fixes': state.get('total_autonomous_fixes', 0),
        'audit_trail_size': len(state.get('audit_trail', [])),
    }
