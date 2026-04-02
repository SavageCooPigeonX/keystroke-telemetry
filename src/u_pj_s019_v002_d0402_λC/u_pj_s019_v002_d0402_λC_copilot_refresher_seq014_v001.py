"""u_pj_s019_v002_d0402_λC_copilot_refresher_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _refresh_copilot_instructions(root: Path, snapshot: dict) -> None:
    try:
        import importlib.util

        manager_path = _latest_runtime_module(root, 'src/管w_cpm_s020*.py')
        if manager_path is not None:
            spec = importlib.util.spec_from_file_location('_copilot_prompt_manager_runtime', manager_path)
            if spec is not None and spec.loader is not None:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                refresh = getattr(mod, 'refresh_managed_prompt', None)
                if callable(refresh):
                    refresh(root, snapshot=snapshot)
                    return
    except Exception:
        pass

    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return

    text = cp_path.read_text(encoding='utf-8')
    pattern = re.compile(
        rf'{re.escape(PROMPT_BLOCK_START)}[\s\S]*?{re.escape(PROMPT_BLOCK_END)}',
        re.DOTALL,
    )
    block = (
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
    text_without_block = pattern.sub('', text).rstrip() + '\n'
    anchor = '<!-- /pigeon:operator-state -->'
    if anchor in text_without_block:
        new_text = text_without_block.replace(anchor, anchor + '\n\n' + block, 1)
    else:
        new_text = text_without_block.rstrip() + '\n\n' + block + '\n'

    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
