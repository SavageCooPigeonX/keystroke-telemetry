"""codex_compat_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _repo_root
from .codex_compat_seq003_v001 import _load_entropy_module
from pathlib import Path
from typing import Any
import importlib.util
import re

def _refresh_entropy(root: Path) -> dict[str, Any]:
    entropy = _load_entropy_module()
    if entropy is None:
        return {"status": "missing"}
    try:
        data = entropy.accumulate_entropy(root)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    if isinstance(data, dict) and "error" in data:
        return {"status": "unavailable", "error": data.get("error")}
    try:
        block = entropy.build_entropy_block(root)
    except Exception as exc:
        block = f"<!-- entropy unavailable: {exc} -->"
    block_path = root / "logs" / "codex_entropy_block.md"
    block_path.parent.mkdir(parents=True, exist_ok=True)
    block_path.write_text(block or "<!-- pigeon:entropy-map -->\nNo entropy data yet.\n<!-- /pigeon:entropy-map -->\n", encoding="utf-8")
    return {
        "status": "ok",
        "block_path": str(block_path),
        "global_avg_entropy": data.get("global_avg_entropy"),
        "tracked_modules": data.get("tracked_modules"),
        "top_entropy_modules": data.get("top_entropy_modules", [])[:5],
    }


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
