"""管w_cpm_rmp_s016_v001.py — refresh orchestrator for copilot prompt manager.

Orchestrates all managed block refreshes in one call.
Imports inject functions directly from sub-files to avoid circular imports.
Self-contained: duplicates _run_refresher and path constants.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v001 | 230 lines | ~2,189 tokens
# DESC:   refresh_orchestrator_for_copilot_prompt
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

# ── duplicated constants ──────────────────────────────────────────────────────
_COPILOT_PATH = '.github/copilot-instructions.md'
_SNAPSHOT_PATH = 'logs/prompt_telemetry_latest.json'
_PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'
_PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'

# ── duplicated micro-utilities ────────────────────────────────────────────────

def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _latest_runtime_module(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None


def _run_refresher(root: Path, relative_path: str | None, function_name: str) -> bool:
    try:
        if relative_path is None:
            return False
        mod_path = root / relative_path
        if not mod_path.exists():
            latest = _latest_runtime_module(root, relative_path)
            if latest is None:
                return False
            mod_path = latest
        spec = importlib.util.spec_from_file_location(f'_rmp_refresh_{function_name}', mod_path)
        if spec is None or spec.loader is None:
            return False
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        func = getattr(mod, function_name, None)
        if not callable(func):
            return False
        return bool(func(root))
    except Exception:
        return False

# ── orchestrator ──────────────────────────────────────────────────────────────

def refresh_managed_prompt(
    root: Path,
    snapshot: dict | None = None,
    track_mutations: bool = True,
    registry: dict | None = None,
    processed: int = 0,
) -> dict:
    root = Path(root)

    # inject all managed blocks
    from src.管_cpm_s020.管w_cpm_idx_s012_v001 import _build_auto_index_block
    from src.管_cpm_s020.管w_cpm_bvx_s013_v001 import inject_bug_voices
    from src.管_cpm_s020.管w_cpm_ops_s014_v001 import inject_operator_state, inject_entropy_layers
    import re as _re

    # auto-index
    auto_index_refreshed = False
    if registry:
        try:
            cp_path = root / _COPILOT_PATH
            if cp_path.exists():
                block = _build_auto_index_block(root, registry, processed)
                text = cp_path.read_text(encoding='utf-8')
                pattern = _re.compile(r'(?ms)^\s*<!-- pigeon:auto-index -->\s*$\n.*?^\s*<!-- /pigeon:auto-index -->\s*$')
                new_text = pattern.sub(block, text) if pattern.search(text) else text.rstrip() + '\n\n' + block + '\n'
                if new_text != text:
                    cp_path.write_text(new_text, encoding='utf-8')
                auto_index_refreshed = True
        except Exception:
            pass

    bug_voices_refreshed = inject_bug_voices(root, registry=registry)

    # bug profiles — optional module
    try:
        from src.bug_profiles import generate_profiles
        generate_profiles(root)
    except Exception:
        pass

    # numeric surface — optional module
    try:
        from src.numeric_surface import generate_surface
        generate_surface(root)
    except Exception:
        pass

    task_context_refreshed = _run_refresher(root, 'src/推w_dp_s017*.py', 'inject_task_context')
    task_queue_refreshed = _run_refresher(root, 'src/队p_tq_s018*.py', 'inject_task_queue')
    operator_state_refreshed = inject_operator_state(root)
    entropy_refreshed = inject_entropy_layers(root)

    # inject_prompt_telemetry — inline to avoid importing from main
    injected = False
    try:
        _snapshot = snapshot or _load_json(root / _SNAPSHOT_PATH)
        if _snapshot:
            cp_path = root / _COPILOT_PATH
            if cp_path.exists():
                block = (
                    f'{_PROMPT_BLOCK_START}\n## Live Prompt Telemetry\n\n'
                    f'*Auto-updated per prompt · source: `{_SNAPSHOT_PATH}`*\n\n'
                    'Use this block as the highest-freshness prompt-level telemetry. '
                    'When it conflicts with older commit-time context, prefer this block.\n\n'
                    f'```json\n{json.dumps(_snapshot, ensure_ascii=False, indent=2)}\n```\n\n'
                    f'{_PROMPT_BLOCK_END}'
                )
                text = cp_path.read_text(encoding='utf-8')
                pattern = _re.compile(
                    rf'(?ms)^\s*{_re.escape(_PROMPT_BLOCK_START)}\s*$\n.*?^\s*{_re.escape(_PROMPT_BLOCK_END)}\s*$'
                )
                new_text = pattern.sub(block, text) if pattern.search(text) else text.rstrip() + '\n\n' + block + '\n'
                if new_text != text:
                    cp_path.write_text(new_text, encoding='utf-8')
                injected = True
    except Exception:
        pass

    # optional modules
    for mod_import, func_name, kwargs in [
        (lambda: __import__('src.engagement_hooks', fromlist=['inject_hooks']), 'inject_hooks', {}),
    ]:
        try:
            mod = mod_import()
            fn = getattr(mod, func_name, None)
            if callable(fn):
                fn(root, **kwargs)
        except Exception:
            pass

    try:
        from src.narrative_glove import inject_narrative
        inject_narrative(root)
    except Exception:
        pass
    try:
        from src.persona_intent_synthesizer import inject_into_copilot_instructions, write_intent_snapshot
        write_intent_snapshot(root)
        inject_into_copilot_instructions(root)
    except Exception:
        pass
    intent_backlog_refreshed = False
    try:
        from src.intent_reconstructor import refresh_intent_backlog
        intent_backlog_refreshed = bool(refresh_intent_backlog(root).get('injected'))
    except Exception:
        pass
    try:
        from src.operator_probes import inject_probes
        inject_probes(root)
    except Exception:
        pass

    _run_refresher(root, 'src/声w_vs_s028*.py', 'inject_voice_style')

    try:
        from src.template_selector import hydrate_templates, inject_active_template
        hydrate_templates(root)
        inject_active_template(root)
    except Exception:
        pass

    # probe resolution — harvest + resolve + inject block
    probe_resolved = False
    try:
        from src.probe_resolver import resolve_all_pending
        from src.probe_surface import build_resolution_block
        resolve_all_pending(root, auto_write=True)
        _probe_start = '<!-- pigeon:probe-resolutions -->'
        _probe_end = '<!-- /pigeon:probe-resolutions -->'
        cp_path = root / _COPILOT_PATH
        if cp_path.exists():
            block_content = build_resolution_block(root)
            block = f'{_probe_start}\n{block_content}\n{_probe_end}'
            text = cp_path.read_text(encoding='utf-8')
            pattern = _re.compile(
                rf'(?ms)^\s*{_re.escape(_probe_start)}\s*$\n.*?^\s*{_re.escape(_probe_end)}\s*$'
            )
            new_text = pattern.sub(block, text) if pattern.search(text) else text.rstrip() + '\n\n' + block + '\n'
            if new_text != text:
                cp_path.write_text(new_text, encoding='utf-8')
            probe_resolved = True
    except Exception:
        pass

    mutation_result = None
    if track_mutations:
        try:
            recon_path = root / 'src' / 'prompt_recon_seq016_v001.py'
            if recon_path.exists():
                spec = importlib.util.spec_from_file_location('_prompt_recon', recon_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    track_fn = getattr(mod, 'track_mutation', None)
                    if callable(track_fn):
                        mutation_result = track_fn(root)
        except Exception:
            pass

    return {
        'auto_index': auto_index_refreshed,
        'bug_voices': bug_voices_refreshed,
        'task_context': task_context_refreshed,
        'task_queue': task_queue_refreshed,
        'intent_backlog': intent_backlog_refreshed,
        'operator_state': operator_state_refreshed,
        'entropy': entropy_refreshed,
        'prompt_telemetry': injected,
        'probe_resolutions': probe_resolved,
        'mutations': mutation_result,
    }
