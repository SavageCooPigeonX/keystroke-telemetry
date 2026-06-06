"""codex_compat_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _write_text_resilient
from .codex_compat_seq007_v001 import _replace_managed_block
from .codex_compat_seq011_v001 import _build_live_prompt_telemetry
from pathlib import Path
from typing import Any
import json
import re

def _render_prompt_telemetry_block(telemetry: dict[str, Any]) -> str:
    return "\n".join([
        "<!-- pigeon:prompt-telemetry -->",
        "## Live Prompt Telemetry",
        "",
        f"*Auto-updated {telemetry.get('updated_at', '')} - source: `logs/prompt_telemetry_latest.json`*",
        "",
        "Use this block as the highest-freshness prompt-level telemetry. It is generated from Codex live context, not the stale legacy daemon.",
        "",
        "```json",
        json.dumps(telemetry, indent=2, ensure_ascii=False),
        "```",
        "",
        "<!-- /pigeon:prompt-telemetry -->",
    ])


def _write_live_prompt_telemetry(root: Path, pack: dict[str, Any]) -> dict[str, Any]:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    telemetry = _build_live_prompt_telemetry(root, pack)
    (logs / "prompt_telemetry_latest.json").write_text(
        json.dumps(telemetry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    path = root / ".github" / "copilot-instructions.md"
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="ignore")
        updated = _replace_managed_block(
            text,
            "<!-- pigeon:prompt-telemetry -->",
            "<!-- /pigeon:prompt-telemetry -->",
            _render_prompt_telemetry_block(telemetry),
        )
        if updated != text:
            _write_text_resilient(path, updated)
    return telemetry
