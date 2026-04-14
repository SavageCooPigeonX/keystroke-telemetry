"""escalation_engine_check_helpers_b_seq018_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 018 | VER: v001 | 33 lines | ~344 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

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
