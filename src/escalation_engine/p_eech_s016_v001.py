"""escalation_engine_seq001_v001_check_helpers_seq016_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v001 | 96 lines | ~919 tokens
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


def _check_and_escalate_collect_modules(persistence, dossier):
    """Build the set of modules with known persistent bugs."""
    all_modules = set()
    for mod in persistence:
        all_modules.add(mod)
    for mod in dossier:
        all_modules.add(mod)
    return all_modules


def _check_and_escalate_init_module_state(state, module, now):
    """Get or create state for a module."""
    mod_state = state['modules'].setdefault(module, {
        'level': 0,
        'passes_ignored': 0,
        'bug_type': None,
        'confidence': 0.0,
        'countdown': WARN_COUNTDOWN,
        'last_updated': now,
        'fix_result': None,
    })
    return mod_state


def _check_and_escalate_get_bug_types(module, persistence, dossier):
    """Determine fixable bug type(s) for this module."""
    p_entries = persistence.get(module, [])
    d_entry = dossier.get(module, {})
    bug_types = set()
    for p in p_entries:
        bt = p.get('type', '')
        if bt in KNOWN_FIXABLE:
            bug_types.add(bt)
    for bk in d_entry.get('bugs', []):
        abbrev_map = {'oc': 'over_hard_cap', 'de': 'dead_export', 'hi': 'hardcoded_import',
                      'dd': 'duplicate_docstring'}
        if bk in abbrev_map and abbrev_map[bk] in KNOWN_FIXABLE:
            bug_types.add(abbrev_map[bk])
    return bug_types


def _check_and_escalate_pick_bug_type(bug_types):
    """Pick the highest-priority bug."""
    priority_order = ['hardcoded_import', 'over_hard_cap', 'dead_export', 'duplicate_docstring']
    bug_type = next((bt for bt in priority_order if bt in bug_types), list(bug_types)[0])
    return bug_type


def _check_and_escalate_update_counts(module, mod_state, persistence, dossier):
    """Compute passes ignored."""
    p_entries = persistence.get(module, [])
    d_entry = dossier.get(module, {})
    max_appearances = 0
    for p in p_entries:
        max_appearances = max(max_appearances, p.get('appearances', 0))
    recur = d_entry.get('recur', 0)
    passes = max(max_appearances, recur, mod_state.get('passes_ignored', 0))
    mod_state['passes_ignored'] = passes


def _check_and_escalate_pass_gates(mod_state, confidence, reg_entry):
    """Check the four escalation gates."""
    if confidence < HIGH_CONFIDENCE:
        mod_state['level'] = max(mod_state['level'], 1)
        return False
    if mod_state['passes_ignored'] < THRESHOLD_PASSES:
        mod_state['level'] = max(mod_state['level'], 1)
        return False
    if not reg_entry or not _has_rollback_version(reg_entry):
        mod_state['level'] = max(mod_state['level'], 2)
        return False
    return True
