"""codex_compat_load_intent_reconstructor_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_repo_root_seq008_v001 import _repo_root
from typing import Any
import importlib.util
import re

def _load_intent_reconstructor() -> Any | None:
    module_path = _repo_root() / "src" / "intent_reconstructor_seq001_v001.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("codex_intent_reconstructor", module_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
