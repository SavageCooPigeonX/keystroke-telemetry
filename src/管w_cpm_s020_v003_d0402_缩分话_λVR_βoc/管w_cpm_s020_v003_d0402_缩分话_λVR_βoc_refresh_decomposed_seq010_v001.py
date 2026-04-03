"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_refresh_decomposed_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
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
    bug_voices_refreshed = inject_bug_voices(root, registry=registry)
    task_context_refreshed = _run_refresher(
        root,
        'src/推w_dp_s017*.py',
        'inject_task_context',
    )
    task_queue_refreshed = _run_refresher(
        root,
        'src/队p_tq_s018*.py',
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
        'bug_voices_refreshed': bug_voices_refreshed,
        'task_context_refreshed': task_context_refreshed,
        'task_queue_refreshed': task_queue_refreshed,
        'operator_state_refreshed': operator_state_refreshed,
        'prompt_telemetry_injected': injected,
        'mutation_result': mutation_result,
        'audit': audit,
    }
