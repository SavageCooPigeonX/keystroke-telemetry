"""codex_compat_refresh_entropy_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_load_entropy_module_seq010_v001 import _load_entropy_module
from pathlib import Path
from typing import Any
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
