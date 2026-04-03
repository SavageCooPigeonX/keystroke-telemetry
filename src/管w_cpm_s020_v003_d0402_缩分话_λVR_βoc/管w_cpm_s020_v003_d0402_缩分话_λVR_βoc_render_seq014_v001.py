"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_render_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
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


def _append_infra_index(lines: list[str], root: Path) -> None:
    infra_dirs = ['client', 'vscode-extension']
    infra_files: dict[str, list[str]] = {}
    for folder in infra_dirs:
        folder_path = root / folder
        if folder_path.is_dir():
            for py_file in sorted(folder_path.glob('*.py')):
                if py_file.name.startswith('__'):
                    continue
                infra_files.setdefault(folder, []).append(py_file.stem)
    root_py = sorted(
        p.stem for p in root.glob('*.py')
        if not p.name.startswith('__') and '_seq' not in p.name
    )
    if root_py:
        infra_files['(root)'] = root_py
    if not infra_files:
        return
    lines.append('**Infra**')
    for folder in sorted(infra_files):
        lines.append(f'{folder}: {", ".join(infra_files[folder])}')
