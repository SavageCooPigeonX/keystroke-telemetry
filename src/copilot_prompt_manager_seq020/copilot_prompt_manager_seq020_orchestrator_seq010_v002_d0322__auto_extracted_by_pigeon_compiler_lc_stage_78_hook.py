"""copilot_prompt_manager_seq020_orchestrator_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v002 | 53 lines | ~521 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import re

def refresh_managed_prompt(
    root: Path,
    snapshot: dict | None = None,
    track_mutations: bool = True,
    registry: dict | None = None,
    processed: int = 0,
) -> dict:
    root = Path(root)
    auto_index_refreshed = inject_auto_index(root, registry=registry, processed=processed)
    dictionary_refreshed = _run_refresher(
        root,
        'src/symbol_dictionary_seq031_v001.py',
        'inject_dictionary_block',
    )
    task_context_refreshed = _run_refresher(
        root,
        'src/dynamic_prompt_seq017_v003_d0317__steers_copilot_cot_from_live_lc_wire_narratives_self.py',
        'inject_task_context',
    )
    task_queue_refreshed = _run_refresher(
        root,
        'src/task_queue_seq018_v002_d0317__copilot_driven_task_tracking_linked_lc_task_queue_system.py',
        'inject_task_queue',
    )
    operator_state_refreshed = inject_operator_state(root)
    injected = inject_prompt_telemetry(root, snapshot=snapshot)

    mutation_result = None
    if track_mutations:
        try:
            import importlib.util

            recon_path = root / 'src' / 'prompt_recon_seq016_v001.py'
            if recon_path.exists():
                spec = importlib.util.spec_from_file_location('_prompt_recon_runtime_manager', recon_path)
                if spec is not None and spec.loader is not None:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    tracker = getattr(mod, 'track_copilot_prompt_mutations', None)
                    if callable(tracker):
                        mutation_result = tracker(root)
        except Exception:
            mutation_result = None

    audit = audit_copilot_prompt(root)
    return {
        'auto_index_refreshed': auto_index_refreshed,
        'dictionary_refreshed': dictionary_refreshed,
        'task_context_refreshed': task_context_refreshed,
        'task_queue_refreshed': task_queue_refreshed,
        'operator_state_refreshed': operator_state_refreshed,
        'prompt_telemetry_injected': injected,
        'mutation_result': mutation_result,
        'audit': audit,
    }
