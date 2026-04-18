"""push_snapshot_seq001_v001_capture_decomposed_seq017_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v001 | 110 lines | ~1,013 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path

# Import helper functions from sibling modules
from .push_snapshot_seq001_v001_registry_seq002_v001 import _load_registry
from .push_snapshot_seq001_v001_self_fix_seq003_v001 import _load_self_fix_counts
from .push_snapshot_seq001_v001_heat_map_seq004_v001 import _load_heat_map
from .push_snapshot_seq001_v001_deaths_seq005_v001 import _load_deaths
from .push_snapshot_seq001_v001_operator_seq006_v001 import _load_operator_signal
from .push_snapshot_seq001_v001_cycle_state_seq007_v001 import _load_cycle_state
from .push_snapshot_seq001_v001_probe_state_seq008_v001 import _load_probe_state
from .push_snapshot_seq001_v001_file_stats_seq009_v001 import _compute_file_stats
from .push_snapshot_seq001_v001_coupling_seq010_v001 import _compute_coupling
from .push_snapshot_seq001_v001_persistence_seq011_v001 import _save_snapshot

def capture_snapshot(root: Path, commit_hash: str, intent: str,
                     changed_files: list[str]) -> dict:
    """Capture a full codebase health snapshot at this push.

    Reads all live data sources: registry, self-fix, heat map, deaths,
    operator profile, push cycle state, module state files.
    """
    ts = datetime.now(timezone.utc).isoformat()

    registry = _load_registry(root)
    self_fix = _load_self_fix_counts(root)
    heat = _load_heat_map(root)
    deaths = _load_deaths(root)
    operator = _load_operator_signal(root)
    cycle_state = _load_cycle_state(root)
    probe_state = _load_probe_state(root)
    file_stats = _compute_file_stats(root, registry)
    coupling = _compute_coupling(registry)

    snapshot = {
        'schema': 'push_snapshot_seq001_v001/v1',
        'ts': ts,
        'commit': commit_hash,
        'intent': intent,
        'changed_files': len(changed_files),
        'changed_py': len([f for f in changed_files if f.endswith('.py')]),

        # Module census
        'modules': {
            'total': len(registry),
            'with_bugs': sum(1 for m in registry.values() if m.get('bug_keys')),
            'over_cap': self_fix.get('over_hard_cap', 0),
            'compliant': file_stats['compliant'],
            'compliance_pct': round(file_stats['compliant'] / max(len(registry), 1) * 100, 1),
        },

        # Bug surface
        'bugs': {
            'total': self_fix.get('total', 0),
            'hardcoded_import': self_fix.get('hardcoded_import', 0),
            'over_hard_cap': self_fix.get('over_hard_cap', 0),
            'dead_export': self_fix.get('dead_export', 0),
            'high_coupling': self_fix.get('high_coupling', 0),
            'other': self_fix.get('other', 0),
        },

        # File size distribution
        'file_stats': {
            'avg_tokens': file_stats['avg_tokens'],
            'median_tokens': file_stats['median_tokens'],
            'max_tokens': file_stats['max_tokens'],
            'total_tokens': file_stats['total_tokens'],
            'files_under_50': file_stats['under_50'],
            'files_50_200': file_stats['range_50_200'],
            'files_over_200': file_stats['over_200'],
        },

        # Coupling health
        'coupling': {
            'high_coupling_pairs': coupling['high_pairs'],
            'avg_coupling': coupling['avg_coupling'],
            'max_coupling': coupling['max_coupling'],
        },

        # Execution health
        'deaths': {
            'total': deaths['total'],
            'by_cause': deaths['by_cause'],
        },

        # Heat map (cognitive load)
        'heat': {
            'modules_tracked': heat['count'],
            'avg_hesitation': heat['avg_hes'],
            'hottest': heat['hottest'][:5],
        },

        # Operator state
        'operator': {
            'prompts_since_last_push': operator.get('prompt_count', 0),
            'avg_wpm': operator.get('avg_wpm', 0),
            'avg_deletion': operator.get('avg_deletion', 0),
            'dominant_state': operator.get('dominant_state', 'unknown'),
            'dominant_intent': operator.get('dominant_intent', 'unknown'),
        },

        # Push cycle meta
        'cycle': {
            'number': cycle_state.get('total_cycles', 0),
            'sync_score': cycle_state.get('last_sync_score', 0),
            'predictions': cycle_state.get('last_prediction_count', 0),
        },

        # Probe intelligence
        'probes': {
            'modules_probed': probe_state['modules_probed'],
            'total_conversations': probe_state['total_convos'],
            'total_intents_extracted': probe_state['total_intents'],
            'total_pain_points': probe_state['total_pain'],
            'avg_engagement': probe_state['avg_engagement'],
        },
    }

    # Persist
    _save_snapshot(root, commit_hash, snapshot)
    return snapshot
