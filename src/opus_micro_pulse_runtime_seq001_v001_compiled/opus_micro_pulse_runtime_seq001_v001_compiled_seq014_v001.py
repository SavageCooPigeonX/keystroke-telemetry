"""opus_micro_pulse_runtime_seq001_v001_compiled_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import json
import re

def _write_copilot_bootstrap(root: Path, result: dict[str, Any]) -> None:
    path = root / ".github" / "copilot-instructions.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    start = "<!-- codex:opus-cannon-bootstrap -->"
    end = "<!-- /codex:opus-cannon-bootstrap -->"
    cannon = result.get("cannon_job") or {}
    block = "\n".join([
        start,
        "## Opus Cannon Bootstrap",
        "",
        "This file is only the bootstrap contract. The generated Opus cannon is the current executor prompt.",
        "",
        "- primary_executor_prompt: `logs/opus_executor_prompt_latest.md`",
        "- cannon_packet: `logs/prompt_cannon_job_latest.json`",
        "- pulse_packet: `logs/opus_micro_pulse_latest.json`",
        "- gate_packet: `logs/cannon_execution_gate_latest.json`",
        f"- current_prompt_hash: `{result.get('prompt_hash')}`",
        f"- current_executor_session: `{cannon.get('executor_session')}`",
        f"- current_prompt_class: `{cannon.get('prompt_class')}`",
        "",
        "Executor rule: read the primary executor prompt first; use the operator prompt only as fallback evidence.",
        end,
    ])
    if start in old and end in old:
        new = re.sub(rf"{re.escape(start)}.*?{re.escape(end)}", block, old, flags=re.S)
    else:
        new = old.rstrip() + "\n\n" + block + "\n"
    if new != old:
        path.write_text(new, encoding="utf-8")
