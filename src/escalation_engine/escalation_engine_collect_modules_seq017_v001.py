"""escalation_engine_collect_modules_seq017_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v001 | 41 lines | ~355 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

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
