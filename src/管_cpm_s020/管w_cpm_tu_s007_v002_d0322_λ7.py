"""copilot_prompt_manager_seq020_telemetry_utils_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
import json
import re

def _render_prompt_block(snapshot: dict) -> str:
    return (
        f'{PROMPT_BLOCK_START}\n'
        '## Live Prompt Telemetry\n\n'
        f'*Auto-updated per prompt · source: `{SNAPSHOT_PATH}`*\n\n'
        'Use this block as the highest-freshness prompt-level telemetry. '
        'When it conflicts with older commit-time context, prefer this block.\n\n'
        '```json\n'
        f'{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n'
        '```\n\n'
        f'{PROMPT_BLOCK_END}'
    )


def _run_refresher(root: Path, relative_path: str, function_name: str) -> bool:
    try:
        import importlib.util

        mod_path = root / relative_path
        if not mod_path.exists():
            return False
        spec = importlib.util.spec_from_file_location(f'_prompt_refresh_{function_name}', mod_path)
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
