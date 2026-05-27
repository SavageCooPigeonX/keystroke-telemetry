"""Fail-closed guard that blocks executor work until a cannon packet exists."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "cannon_execution_gate/v1"
LATEST = "logs/cannon_execution_gate_latest.json"
MARKDOWN = "logs/cannon_execution_gate.md"


def build_cannon_execution_gate(
    root: Path,
    prompt: str = "",
    *,
    write: bool = True,
    require_prompt_hash: bool = True,
) -> dict[str, Any]:
    """Validate that Opus fired a cannon packet before Codex/Copilot work."""
    root = Path(root)
    prompt = prompt.strip()
    cannon_path = root / "logs" / "prompt_cannon_job_latest.json"
    pulse_path = root / "logs" / "opus_micro_pulse_latest.json"
    cannon = _load_json(cannon_path)
    pulse = _load_json(pulse_path)
    blockers: list[str] = []
    warnings: list[str] = []

    if not isinstance(cannon, dict):
        blockers.append("missing_or_unreadable:logs/prompt_cannon_job_latest.json")
        cannon = {}
    if not isinstance(pulse, dict):
        blockers.append("missing_or_unreadable:logs/opus_micro_pulse_latest.json")
        pulse = {}

    if cannon.get("schema") != "prompt_cannon_job/v1":
        blockers.append("invalid_cannon_schema")
    if pulse.get("schema") != "opus_micro_pulse_runtime/v1":
        blockers.append("invalid_opus_pulse_schema")

    prompt_hash = _sha(prompt) if prompt else ""
    cannon_hash = str(cannon.get("prompt_hash") or "")
    pulse_hash = str(pulse.get("prompt_hash") or "")
    if not cannon_hash:
        blockers.append("missing_cannon_prompt_hash")
    if pulse_hash and cannon_hash and pulse_hash != cannon_hash:
        blockers.append("opus_pulse_hash_mismatch")
    if require_prompt_hash and prompt_hash and cannon_hash != prompt_hash:
        blockers.append("cannon_prompt_hash_does_not_match_current_prompt")

    for key in ("prompt_class", "sim_policy", "executor_session"):
        if not cannon.get(key):
            blockers.append(f"missing_cannon_{key}")
    if not cannon.get("sealed_intent_keys"):
        blockers.append("missing_sealed_intent_keys")
    if not str(cannon.get("expanded_task") or "").strip():
        blockers.append("missing_expanded_task_payload")
    elif len(str(cannon.get("expanded_task") or "")) < 120:
        warnings.append("expanded_task_payload_is_thin")
    executor_prompt_path = str(cannon.get("executor_prompt_path") or "")
    if not executor_prompt_path:
        blockers.append("missing_executor_prompt_path")
    elif not (root / executor_prompt_path).exists():
        blockers.append("missing_executor_prompt_file")
    if not str(cannon.get("executor_prompt") or "").strip():
        blockers.append("missing_executor_prompt_payload")

    predicted = cannon.get("predicted_files") or []
    mutation_allowed = bool(cannon.get("mutation_allowed"))
    if mutation_allowed and not predicted:
        blockers.append("mutation_cannon_has_no_predicted_files")
    if cannon.get("executor_session") in {"codex_execution_session", "copilot_ui_session"} and not predicted:
        blockers.append("executor_cannon_has_no_predicted_files")

    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "status": "cleared" if not blockers else "blocked",
        "cleared": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "prompt_hash": cannon_hash,
        "current_prompt_hash": prompt_hash,
        "executor_session": cannon.get("executor_session", ""),
        "prompt_class": cannon.get("prompt_class", ""),
        "sim_policy": cannon.get("sim_policy", ""),
        "predicted_file_count": len(predicted),
        "payload_ready": bool(str(cannon.get("expanded_task") or "").strip()),
        "executor_prompt_path": executor_prompt_path,
        "executor_prompt_ready": bool(executor_prompt_path and (root / executor_prompt_path).exists()),
        "repo_wide_rule": "Codex/Copilot code work is blocked until this gate is cleared.",
        "required_files": [
            "logs/opus_micro_pulse_latest.json",
            "logs/prompt_cannon_job_latest.json",
            "logs/cannon_execution_gate_latest.json",
        ],
    }
    if write:
        _write_json(root / LATEST, result)
        (root / MARKDOWN).write_text(render_cannon_execution_gate(result), encoding="utf-8")
    return result


def assert_cannon_execution_gate(root: Path, prompt: str = "") -> dict[str, Any]:
    result = build_cannon_execution_gate(root, prompt, write=True)
    if not result["cleared"]:
        raise RuntimeError("Cannon execution gate blocked: " + ", ".join(result["blockers"]))
    return result


def render_cannon_execution_gate(result: dict[str, Any]) -> str:
    lines = [
        "# Cannon Execution Gate",
        "",
        f"- status: `{result.get('status')}`",
        f"- executor_session: `{result.get('executor_session')}`",
        f"- prompt_class: `{result.get('prompt_class')}`",
        f"- predicted_file_count: `{result.get('predicted_file_count')}`",
        f"- payload_ready: `{str(result.get('payload_ready')).lower()}`",
        f"- executor_prompt: `{result.get('executor_prompt_path')}`",
        f"- executor_prompt_ready: `{str(result.get('executor_prompt_ready')).lower()}`",
        "",
        "## Repo-Wide Rule",
        "",
        result.get("repo_wide_rule", ""),
        "",
        "## Blockers",
        "",
    ]
    blockers = result.get("blockers") or []
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- `none`")
    warnings = result.get("warnings") or []
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- `{item}`" for item in warnings)
    else:
        lines.append("- `none`")
    return "\n".join(lines) + "\n"


def _sha(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8", errors="replace")).hexdigest()[:16]


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["build_cannon_execution_gate", "assert_cannon_execution_gate", "render_cannon_execution_gate"]
