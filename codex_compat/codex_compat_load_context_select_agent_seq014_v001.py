"""codex_compat_load_context_select_agent_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_repo_root_seq008_v001 import _repo_root
from typing import Any
import importlib.util
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
