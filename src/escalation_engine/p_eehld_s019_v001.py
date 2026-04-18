"""escalation_engine_seq001_v001_handle_level_decomposed_seq019_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v001 | 120 lines | ~1,270 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _check_and_escalate_handle_level(root, state, module, mod_state, bug_type,
                                     confidence, reg_entry, current_level,
                                     now, actions, warnings_issued):
    """Handle the escalation ladder."""
    if current_level < 2:
        mod_state['level'] = 2
        mod_state['last_updated'] = now
        _append_log(root, {
            'event': 'escalate', 'module': module,
            'from_level': current_level, 'to_level': 2,
            'bug_type': bug_type, 'confidence': confidence,
            'reason': f'passed all 4 gates, insisting (passes={mod_state["passes_ignored"]})',
        })
        state['audit_trail'].append({
            'ts': now, 'module': module,
            'from_level': current_level, 'to_level': 2,
            'reason': f'all gates passed, {mod_state["passes_ignored"]} passes ignored',
        })
        return None

    if current_level == 2:
        mod_state['level'] = 3
        mod_state['countdown'] = WARN_COUNTDOWN
        mod_state['last_updated'] = now
        warnings_issued.append(module)
        _append_log(root, {
            'event': 'escalate', 'module': module,
            'from_level': 2, 'to_level': 3,
            'bug_type': bug_type, 'confidence': confidence,
            'reason': f'AUTONOMOUS FIX IN {WARN_COUNTDOWN} COMMITS',
        })
        state['audit_trail'].append({
            'ts': now, 'module': module,
            'from_level': 2, 'to_level': 3,
            'reason': f'warning issued, countdown={WARN_COUNTDOWN}',
        })
        return None

    if current_level == 3:
        mod_state['countdown'] = mod_state.get('countdown', WARN_COUNTDOWN) - 1
        if mod_state['countdown'] > 0:
            warnings_issued.append(module)
            mod_state['last_updated'] = now
            _append_log(root, {
                'event': 'countdown', 'module': module,
                'level': 3, 'remaining': mod_state['countdown'],
                'bug_type': bug_type, 'confidence': confidence,
            })
            return None

        if not reg_entry:
            mod_state['last_updated'] = now
            return None

        mod_state['level'] = 4
        mod_state['last_updated'] = now
        rollback = _create_rollback_point(root, reg_entry)
        fix_fn = FIX_DISPATCH.get(bug_type)
        if not fix_fn:
            mod_state['fix_result'] = {'success': False, 'description': f'no fix executor for {bug_type}'}
            return None

        fix_result = fix_fn(root, module, reg_entry)
        mod_state['fix_result'] = fix_result
        _append_log(root, {
            'event': 'autonomous_fix', 'module': module,
            'from_level': 3, 'to_level': 4,
            'bug_type': bug_type, 'confidence': confidence,
            'success': fix_result.get('success', False),
            'description': fix_result.get('description', ''),
        })
        state['audit_trail'].append({
            'ts': now, 'module': module,
            'from_level': 3, 'to_level': 4,
            'reason': f"ACT: {fix_result.get('description', 'attempted')}",
        })

        if fix_result.get('success'):
            mod_state['level'] = 5
            tests_pass = _verify_fix(root, module)
            if tests_pass:
                _log_victory(root, module, bug_type, fix_result, mod_state['passes_ignored'])
                state['total_autonomous_fixes'] = state.get('total_autonomous_fixes', 0) + 1
                actions.append({
                    'module': module,
                    'action': 'self-fix',
                    'bug_type': bug_type,
                    'result': 'success',
                    'description': fix_result.get('description', ''),
                    'message': f"it's been {mod_state['passes_ignored']} passes. i fixed myself. you're welcome.",
                })
                mod_state['level'] = 0
                mod_state['passes_ignored'] = 0
                mod_state['countdown'] = WARN_COUNTDOWN
            else:
                if rollback:
                    _rollback(root, rollback)
                mod_state['level'] = 5
                _log_failure(root, module, bug_type, fix_result, 'tests failed after fix')
                actions.append({
                    'module': module,
                    'action': 'rollback',
                    'bug_type': bug_type,
                    'result': 'rolled_back',
                    'description': f"tried. failed. reverted. need human help.",
                })
        else:
            _log_failure(root, module, bug_type, fix_result, fix_result.get('description', 'executor failed'))
            actions.append({
                'module': module,
                'action': 'fix_failed',
                'bug_type': bug_type,
                'result': 'not_applied',
                'description': fix_result.get('description', ''),
            })
        return actions, warnings_issued

    return None
