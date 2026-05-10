"""codex_compat_write_live_prompt_telemetry_seq028_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_build_live_prompt_telemetry_seq026_v001 import _build_live_prompt_telemetry
from .codex_compat_render_prompt_telemetry_block_seq027_v001 import _render_prompt_telemetry_block
from .codex_compat_replace_managed_block_seq020_v001 import _replace_managed_block
from .codex_compat_write_text_resilient_seq006_v001 import _write_text_resilient
from pathlib import Path
from typing import Any
import json
import re

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
