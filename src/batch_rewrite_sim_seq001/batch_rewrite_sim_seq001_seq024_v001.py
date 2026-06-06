"""batch_rewrite_sim_seq001_seq024_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _render_orchestrator_oath(result: dict[str, Any]) -> str:
    oath = result.get("orchestrator_oath") or {}
    lines = [
        "# Orchestrator Dev Oath",
        "",
        f"- ts: `{result.get('ts')}`",
        f"- intent_key: `{(result.get('intent') or {}).get('intent_key', '')}`",
        "",
    ]
    for line in oath.get("lines", []):
        lines.append(f"- {line}")
    lines.extend([
        "",
        "Comic clause: files may have beef, but validation has the gavel.",
        "",
    ])
    return "\n".join(lines)
