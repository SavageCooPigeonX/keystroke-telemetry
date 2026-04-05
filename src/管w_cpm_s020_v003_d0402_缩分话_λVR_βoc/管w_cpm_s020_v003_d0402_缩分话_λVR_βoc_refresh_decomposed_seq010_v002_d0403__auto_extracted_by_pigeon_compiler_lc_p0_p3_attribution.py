"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_refresh_decomposed_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v002 | 70 lines | ~701 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: p0_p3_attribution
# LAST:   2026-04-03 @ d7cbc14
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import re

from .管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors_telemetry_seq012_v001 import inject_auto_index, inject_prompt_telemetry
from .管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors_voices_state_seq013_v001 import inject_bug_voices, inject_operator_state
from .管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_audit_decomposed_seq009_v001 import audit_copilot_prompt
from .管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_file_utils_seq003_v001 import _run_refresher

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

    # Entropy shedding map + red layer — copilot self-reported uncertainty
    entropy_refreshed = False
    try:
        from src.entropy_shedding import build_entropy_block, build_red_layer_block

        cp_path = root / '.github' / 'copilot-instructions.md'
        if cp_path.exists():
            text = cp_path.read_text(encoding='utf-8')
            new_text = text

            def _upsert_block(current_text: str, block: str, start_tag: str, end_tag: str) -> str:
                if not block:
                    return current_text
                if start_tag in current_text:
                    import re as _re
                    pattern = _re.compile(
                        _re.escape(start_tag) + r'.*?' + _re.escape(end_tag),
                        _re.DOTALL,
                    )
                    return pattern.sub(block, current_text)
                anchor = '<!-- pigeon:bug-voices -->'
                if anchor in current_text:
                    return current_text.replace(anchor, block + '\n' + anchor)
                return current_text + '\n' + block + '\n'

            new_text = _upsert_block(
                new_text,
                build_entropy_block(root),
                '<!-- pigeon:entropy-map -->',
                '<!-- /pigeon:entropy-map -->',
            )
            new_text = _upsert_block(
                new_text,
                build_red_layer_block(root),
                '<!-- pigeon:entropy-red-layer -->',
                '<!-- /pigeon:entropy-red-layer -->',
            )

            if new_text != text:
                cp_path.write_text(new_text, encoding='utf-8')
                entropy_refreshed = True
    except Exception:
        pass

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

    # Template selector — hydrate .prompt.md files for /debug, /build, /review
    templates_result = None
    try:
        from src.template_selector import hydrate_templates
        templates_result = hydrate_templates(root)
    except Exception:
        pass

    return {
        'auto_index_refreshed': auto_index_refreshed,
        'bug_voices_refreshed': bug_voices_refreshed,
        'task_context_refreshed': task_context_refreshed,
        'task_queue_refreshed': task_queue_refreshed,
        'operator_state_refreshed': operator_state_refreshed,
        'entropy_refreshed': entropy_refreshed,
        'prompt_telemetry_injected': injected,
        'mutation_result': mutation_result,
        'templates': templates_result,
        'audit': audit,
    }
