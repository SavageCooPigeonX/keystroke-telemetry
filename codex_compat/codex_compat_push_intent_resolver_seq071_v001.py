"""codex_compat_push_intent_resolver_seq071_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_load_intent_reconstructor_seq013_v001 import _load_intent_reconstructor
from .codex_compat_refresh_state_seq057_v001 import refresh_state
from pathlib import Path
from typing import Any
import json
import re

def push_intent_resolver(root: Path, prompt_limit: int = 100) -> dict[str, Any]:
    root = Path(root)
    reconstructor = _load_intent_reconstructor()
    if reconstructor is None:
        result = {"status": "missing", "error": "intent_reconstructor_seq001_v001.py not found"}
    else:
        try:
            result = reconstructor.refresh_intent_backlog(root, prompt_limit)
            result["status"] = "ok"
        except Exception as exc:
            result = {"status": "error", "error": str(exc)}
    out = root / "logs" / "codex_intent_resolver.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    refresh_state(root, "pushed to intent resolver")
    return result
