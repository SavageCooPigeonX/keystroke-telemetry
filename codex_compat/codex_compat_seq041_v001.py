"""codex_compat_seq041_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq004_v001 import _load_intent_reconstructor
from .codex_compat_seq031_v001 import refresh_state
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


def _text_from_event(event: dict[str, Any]) -> str:
    for key in ("content", "text", "message", "prompt", "response"):
        value = event.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict):
                    parts.append(str(item.get("text") or item.get("content") or ""))
                else:
                    parts.append(str(item))
            return "\n".join(part for part in parts if part)
    return ""
