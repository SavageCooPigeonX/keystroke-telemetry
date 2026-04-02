"""copilot_prompt_manager_seq020_index_injector_seq009b_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

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
