"""copilot_prompt_manager_seq020_state_injector_seq009c_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

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
