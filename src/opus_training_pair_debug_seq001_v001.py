"""Multi-step Opus diagnosis for stale training-pair telemetry."""
from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LATEST = "logs/opus_training_pair_debug_latest.json"
MARKDOWN = "logs/opus_training_pair_debug.md"


def debug_training_pairs(root: Path, *, write: bool = True) -> dict[str, Any]:
    """Explain why training_pairs.jsonl is stale without mutating it."""
    root = Path(root)
    logs = root / "logs"
    prompt = _latest_jsonl(logs / "prompt_journal.jsonl")
    edit = _latest_jsonl(logs / "edit_pairs.jsonl")
    pair = _latest_jsonl(logs / "training_pairs.jsonl")
    deepseek = _json(logs / "deepseek_prompt_latest.json")
    telemetry = _json(logs / "prompt_telemetry_latest.json")
    writer = _writer_status()
    ages = {
        "prompt_journal_min": _age_min(prompt.get("ts")),
        "edit_pairs_min": _age_min(edit.get("ts")),
        "training_pairs_min": _age_min(pair.get("ts")),
        "deepseek_prompt_min": _age_min(deepseek.get("ts")),
        "prompt_telemetry_min": _age_min(telemetry.get("updated_at")),
    }
    steps = _reason_steps(root, ages, writer)
    result = {
        "schema": "opus_training_pair_debug/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": steps[-1]["status"],
        "ages": ages,
        "latest": {
            "prompt_session": prompt.get("session_n"),
            "edit_file": edit.get("file"),
            "training_session": pair.get("session_n"),
            "deepseek_job": deepseek.get("job_id"),
        },
        "writer": writer,
        "multi_step_reasoning": steps,
        "failed_steps": [step for step in steps if not step.get("ok")],
        "recommended_fix": _recommended_fix(steps),
        "source_paths": {
            "prompt_journal": "logs/prompt_journal.jsonl",
            "edit_pairs": "logs/edit_pairs.jsonl",
            "training_pairs": "logs/training_pairs.jsonl",
            "deepseek_prompt": "logs/deepseek_prompt_latest.json",
            "pulse_watcher": "vscode-extension/pulse_watcher.py",
            "codex_edit_outcome_binder": "src/codex_edit_outcome_binder_seq001_v001.py",
        },
    }
    if write:
        _write_json(root / LATEST, result)
        (root / MARKDOWN).write_text(render_training_pair_debug(result), encoding="utf-8")
    return result


def render_training_pair_debug(debug: dict[str, Any]) -> str:
    lines = ["# Opus Training Pair Debug", "", f"- status: `{debug.get('status')}`"]
    ages = debug.get("ages") or {}
    for name in ("prompt_journal_min", "edit_pairs_min", "training_pairs_min", "deepseek_prompt_min"):
        lines.append(f"- {name}: `{ages.get(name)}`")
    lines.extend(["", "## Multi-Step Reasoning"])
    for step in debug.get("multi_step_reasoning") or []:
        lines.append(f"{step['step']}. {step['claim']} -> `{step['status']}`")
    lines.extend(["", "## Recommended Fix", debug.get("recommended_fix", "")])
    return "\n".join(lines) + "\n"


def _reason_steps(root: Path, ages: dict[str, float | None], writer: dict[str, Any]) -> list[dict[str, Any]]:
    steps = []
    steps.append(_step(1, "prompt capture is fresh enough to train from", _fresh(ages["prompt_journal_min"])))
    steps.append(_step(2, "DeepSeek/probe prompt is fresh enough to pair with operator intent", _fresh(ages["deepseek_prompt_min"])))
    steps.append(_step(3, "edit pair capture is fresh enough to anchor file outcome", _fresh(ages["edit_pairs_min"])))
    steps.append(_step(4, "training-pair writer can be imported", bool(writer.get("importable"))))
    steps.append(_step(5, "training-pair output is fresh", _fresh(ages["training_pairs_min"])))
    if not steps[2]["ok"]:
        status = "blocked_upstream_edit_pairs_stale"
    elif not steps[3]["ok"]:
        status = "blocked_writer_import"
    elif not steps[4]["ok"]:
        status = "blocked_training_append_not_called"
    else:
        status = "healthy"
    steps.append({"step": 6, "claim": _hook_claim(root), "ok": status == "healthy", "status": status})
    return steps


def _recommended_fix(steps: list[dict[str, Any]]) -> str:
    status = steps[-1]["status"]
    if status == "blocked_upstream_edit_pairs_stale":
        return "Wake or replace edit-pair harvesting for Codex edits, then call capture_training_pair only after a fresh edit pair exists."
    if status == "blocked_writer_import":
        return "Fix the decomposed training-pair package import before appending telemetry."
    if status == "blocked_training_append_not_called":
        return "Add a bounded runtime/hook call that appends one training pair after each accepted edit outcome."
    return "Keep monitoring freshness and avoid duplicate appends for the same session/file."


def _hook_claim(root: Path) -> str:
    binder = root / "src" / "codex_edit_outcome_binder_seq001_v001.py"
    if binder.exists():
        return "Codex edit-outcome binder can refresh edit_pairs and training_pairs after accepted edits"
    watcher = _read(root / "vscode-extension" / "pulse_watcher.py")
    if "capture_training_pair" in watcher:
        return "save-time pulse watcher knows how to call training capture, but Codex edits need a fresh edit-pair route too"
    return "no hook path references training capture"


def _writer_status() -> dict[str, Any]:
    try:
        module = importlib.import_module("src.对p_tp_s027_v003_d0402_缩分话_λVR_βoc")
        return {"importable": hasattr(module, "capture_training_pair"), "module": module.__name__}
    except Exception as exc:
        return {"importable": False, "error": str(exc)[:200]}


def _step(n: int, claim: str, ok: bool) -> dict[str, Any]:
    return {"step": n, "claim": claim, "ok": ok, "status": "pass" if ok else "fail"}


def _fresh(age: float | None, limit: float = 90) -> bool:
    return age is not None and age <= limit


def _latest_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    for line in reversed(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return {}


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _age_min(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return round((datetime.now(timezone.utc) - dt).total_seconds() / 60, 2)
    except ValueError:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
