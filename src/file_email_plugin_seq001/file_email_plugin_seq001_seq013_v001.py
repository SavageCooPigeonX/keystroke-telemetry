"""file_email_plugin_seq001_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _lifecycle_guard(ten_q: dict[str, Any], phase: str) -> dict[str, Any]:
    aligned = bool(ten_q.get("passed"))
    return {
        "schema": "orchestrator_email_guard/v1",
        "aligned": aligned,
        "decision": "allow_email" if aligned else "local_only",
        "policy": "prompt_lifecycle_local_first",
        "reason": f"{phase} lifecycle 10Q {'passed' if aligned else 'failed'}",
    }
