"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_injectors_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def inject_prompt_telemetry(root: Path, snapshot: dict | None = None) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False
    if snapshot is None:
        snapshot = _load_json(root / SNAPSHOT_PATH)
    if not snapshot:
        return False

    text = cp_path.read_text(encoding='utf-8')
    block = _render_prompt_block(snapshot)
    new_text = _upsert_block(
        text,
        PROMPT_BLOCK_START,
        PROMPT_BLOCK_END,
        block,
        anchor='<!-- /pigeon:operator-state -->',
    )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def inject_auto_index(root: Path, registry: dict | None = None, processed: int = 0) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists() or not registry:
        return False
    text = cp_path.read_text(encoding='utf-8')
    block = _build_auto_index_block(root, registry, processed)
    new_text = _upsert_block(text, '<!-- pigeon:auto-index -->', '<!-- /pigeon:auto-index -->', block)
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def inject_bug_voices(root: Path, registry: dict | None = None) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False
    text = cp_path.read_text(encoding='utf-8')
    block = _build_bug_voices_block(root, registry)
    new_text = _upsert_block(
        text,
        '<!-- pigeon:bug-voices -->',
        '<!-- /pigeon:bug-voices -->',
        block,
        anchor='<!-- /pigeon:auto-index -->',
    )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def inject_operator_state(root: Path) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False
    block = _build_operator_state_block(root)
    if not block:
        return False
    text = cp_path.read_text(encoding='utf-8')
    new_text = _upsert_block(
        text,
        '<!-- pigeon:operator-state -->',
        '<!-- /pigeon:operator-state -->',
        block,
        anchor='<!-- /pigeon:task-queue -->',
    )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True
