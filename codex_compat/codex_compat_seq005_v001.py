"""codex_compat_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _repo_root
from pathlib import Path
from typing import Any
import importlib.util
import json
import re

def _load_context_select_agent() -> Any | None:
    src_dir = _repo_root() / "src"
    matches = sorted(src_dir.glob("context_select_agent_seq001*.py"), key=lambda item: item.name)
    for module_path in matches:
        spec = importlib.util.spec_from_file_location("codex_context_select_agent", module_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "run_assembly"):
            return module
    return None


def _load_intent_numeric(root: Path) -> Any | None:
    src_dir = _repo_root() / "src"
    matches = sorted(src_dir.glob("intent_numeric_seq001*.py"), key=lambda item: item.name)
    for module_path in matches:
        spec = importlib.util.spec_from_file_location("codex_intent_numeric", module_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ROOT = Path(root)
        module.VOCAB_PATH = Path(root) / "logs" / "intent_vocab.json"
        module.MATRIX_PATH = Path(root) / "logs" / "intent_matrix.json"
        module.TOUCH_LOG_PATH = Path(root) / "logs" / "intent_touches.jsonl"
        module._vocab = {}
        module._vocab_inverse = {}
        module._next_id = 1
        module._vocab_loaded = False
        module._matrix = {}
        module._touch_counts = {}
        module._matrix_loaded = False
        module._surface_healed = False
        module._lexicon_cache = None
        return module
    return None
