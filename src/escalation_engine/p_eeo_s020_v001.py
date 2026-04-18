"""escalation_engine_seq001_v001_orchestrator_seq020_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 020 | VER: v001 | 60 lines | ~609 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path

def check_and_escalate(root: Path, registry: dict = None, changed_py: list = None,
                       cross_context: dict = None) -> dict:
    """Main entry point. Called from git_plugin post-commit.

    Returns: {escalated: bool, actions: [...], warnings: [...]}
    """
    root = Path(root)
    state = _load_state(root)
    now = datetime.now(timezone.utc).isoformat()

    persistence = _load_bug_persistence(root)
    dossier = _load_dossier(root)
    entropy_conf = _load_entropy_confidence(root)
    reg_files = _load_registry_files(root)

    actions = []
    warnings_issued = []

    _check_and_escalate_clear_zombies(root, state, persistence, dossier)
    all_modules = _check_and_escalate_collect_modules(persistence, dossier)

    for module in sorted(all_modules):
        mod_state = _check_and_escalate_init_module_state(state, module, now)
        bug_types = _check_and_escalate_get_bug_types(module, persistence, dossier)
        if not bug_types:
            continue

        bug_type = _check_and_escalate_pick_bug_type(bug_types)
        mod_state['bug_type'] = bug_type
        _check_and_escalate_update_counts(module, mod_state, persistence, dossier)
        confidence = compute_module_confidence(module, entropy_conf, dossier, persistence)
        mod_state['confidence'] = confidence

        if not _check_and_escalate_pass_gates(mod_state, confidence, reg_files.get(module)):
            mod_state['last_updated'] = now
            continue

        current_level = mod_state.get('level', 0)
        result = _check_and_escalate_handle_level(root, state, module, mod_state, bug_type,
                                                  confidence, reg_files.get(module), current_level,
                                                  now, actions, warnings_issued)
        if result:
            actions, warnings_issued = result

    _save_state(root, state)
    if warnings_issued or actions:
        inject_warnings(root, state)

    summary = {
        'escalated': len(actions) > 0 or len(warnings_issued) > 0,
        'actions': actions,
        'warnings': warnings_issued,
        'total_modules_tracked': len(state.get('modules', {})),
        'total_autonomous_fixes': state.get('total_autonomous_fixes', 0),
    }
    return summary
