"""escalation_engine_seq001_v001_zombies_seq016_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v001 | 22 lines | ~262 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _check_and_escalate_clear_zombies(root, state, persistence, dossier):
    """Re-verify modules whose bugs may have been fixed."""
    cleared = []
    for mod_name in list(state['modules'].keys()):
        mod_st = state['modules'][mod_name]
        bt = mod_st.get('bug_type', '')
        if mod_st.get('level', 0) >= 4 and mod_st.get('fix_result'):
            fr = mod_st['fix_result']
            if not fr.get('success'):
                still_buggy = (mod_name in persistence or mod_name in dossier)
                if not still_buggy:
                    cleared.append(mod_name)
                    _append_log(root, {
                        'event': 'zombie_cleared', 'module': mod_name,
                        'bug_type': bt, 'old_level': mod_st['level'],
                        'reason': 'bug no longer appears in any scan',
                    })
                    del state['modules'][mod_name]
    if cleared:
        _save_state(root, state)
