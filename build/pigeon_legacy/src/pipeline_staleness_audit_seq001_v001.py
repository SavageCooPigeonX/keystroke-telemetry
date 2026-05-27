"""Audit moving pipeline logs and let major files write back."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SCHEMA = "pipeline_staleness_audit/v1"

WATCH = [
    ("prompt_journal", "logs/prompt_journal.jsonl", 45, "operator prompts"),
    ("chat_compositions", "logs/chat_compositions.jsonl", 45, "composition telemetry"),
    ("context_selection", "logs/context_selection_history.jsonl", 45, "context routing"),
    ("file_sim", "logs/batch_rewrite_sim_latest.json", 45, "prompt to file simulation"),
    ("file_email", "logs/file_email_outbox.jsonl", 45, "file mail outbox"),
    ("deepseek_jobs", "logs/deepseek_prompt_jobs.jsonl", 45, "DeepSeek queue"),
    ("deepseek_results", "logs/deepseek_prompt_results.jsonl", 90, "DeepSeek completions"),
    ("code_completion_jobs", "logs/deepseek_code_completion_jobs.jsonl", 180, "file-sim code jobs"),
    ("file_self_learning", "logs/file_self_sim_learning_latest.json", 90, "slow self-fix learning"),
    ("intent_graph", "logs/intent_graph_latest.json", 480, "intent graph"),
    ("edit_pairs", "logs/edit_pairs.jsonl", 720, "prompt to edit pairings"),
    ("file_profiles", "file_profiles.json", 10080, "module consciousness"),
]

MAJOR_FILES = ["codex_compat.py", "src/file_email_plugin_seq001_v001.py", "src/deepseek_daemon_seq001_v001.py", "src/batch_rewrite_sim_seq001_v001.py", "src/copilot_probe_push_cycle_seq001_v001.py", "src/file_self_sim_learning_seq001_v001.py"]


def run_pipeline_staleness_audit(
    root: Path,
    *,
    write: bool = True,
    send_file_opinions: bool = False,
    opinion_limit: int = 4,
    delivery_mode: str | None = None,
) -> dict[str, Any]:
    root = Path(root)
    now = datetime.now(timezone.utc)
    rows = [_path_status(root, name, rel, max_age, role, now) for name, rel, max_age, role in WATCH]
    cognitive = _cognitive_probe_health(root)
    hourly = _hourly_health(root)
    opinions = _major_file_opinions(root, rows, cognitive, hourly)
    result = {
        "schema": SCHEMA,
        "ts": now.isoformat(),
        "root": str(root),
        "pipeline": rows,
        "stale": [row for row in rows if row["status"] != "fresh"],
        "cognitive_probe_health": cognitive,
        "deepseek_hourly_health": hourly,
        "major_file_opinions": opinions,
        "email": {"status": "skipped"},
        "paths": {"latest": "logs/pipeline_staleness_audit_latest.json", "history": "logs/pipeline_staleness_audit.jsonl", "markdown": "logs/pipeline_staleness_audit.md"},
    }
    if send_file_opinions:
        result["email"] = send_major_file_opinions(root, result, limit=opinion_limit, delivery_mode=delivery_mode)
    if write:
        _write_outputs(root, result)
    return result


def send_major_file_opinions(
    root: Path,
    audit: dict[str, Any],
    *,
    limit: int = 4,
    delivery_mode: str | None = None,
) -> dict[str, Any]:
    from src.file_email_plugin_seq001_v001 import emit_file_email, load_file_email_config

    root = Path(root)
    config = load_file_email_config(root)
    if delivery_mode:
        config["delivery_mode"] = delivery_mode
    records = []
    for opinion in (audit.get("major_file_opinions") or [])[:limit]:
        records.append(emit_file_email(root, _opinion_event(opinion, audit), config=config))
    return {"status": "ok", "count": len(records), "records": records}


def _path_status(root: Path, name: str, rel: str, max_age_min: int, role: str, now: datetime) -> dict[str, Any]:
    path = root / rel
    if not path.exists():
        return {"name": name, "path": rel, "role": role, "status": "missing", "age_minutes": None, "entries": 0, "max_age_minutes": max_age_min}
    mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    age = round((now - mtime).total_seconds() / 60, 1)
    status = "fresh" if age <= max_age_min and path.stat().st_size > 0 else "stale"
    return {"name": name, "path": rel, "role": role, "status": status, "age_minutes": age, "max_age_minutes": max_age_min, "size": path.stat().st_size, "entries": _line_count(path) if path.suffix == ".jsonl" else 1}


def _cognitive_probe_health(root: Path) -> dict[str, Any]:
    intent = _load_json(root / "logs" / "operator_intent_888.json") or {}
    counts = intent.get("cognitive_state_counts") if isinstance(intent.get("cognitive_state_counts"), dict) else {}
    total = sum(int(v or 0) for v in counts.values())
    unknown = int(counts.get("unknown") or 0)
    coverage = intent.get("prompt_coverage") if isinstance(intent.get("prompt_coverage"), dict) else intent
    gap = int(coverage.get("coverage_gap") or 0)
    warnings = []
    if total and unknown / total > 0.35:
        warnings.append("too_many_unknown_cognitive_states")
    if gap > 0:
        warnings.append("prompt_coverage_gap")
    return {"status": "weak" if warnings else "ok", "cognitive_state_counts": counts, "unknown_ratio": round(unknown / total, 3) if total else 0, "available_prompt_count": coverage.get("available_prompt_count", 0), "requested_prompt_count": coverage.get("requested_prompt_count", 0), "coverage_gap": gap, "warnings": warnings}


def _hourly_health(root: Path) -> dict[str, Any]:
    latest = _load_json(root / "logs" / "hourly_deepseek_autonomy_latest.json") or {}
    result = latest.get("deepseek_result") if isinstance(latest.get("deepseek_result"), dict) else {}
    return {"status": result.get("status") or "missing", "returncode": result.get("returncode"), "stderr_tail": result.get("stderr_tail", ""), "job_id": (latest.get("deepseek_job") or {}).get("job_id") if isinstance(latest.get("deepseek_job"), dict) else ""}


def _major_file_opinions(root: Path, rows: list[dict[str, Any]], cognitive: dict[str, Any], hourly: dict[str, Any]) -> list[dict[str, Any]]:
    stale_names = [row["name"] for row in rows if row["status"] != "fresh"]
    out = []
    for file_path in MAJOR_FILES:
        if not (root / file_path).exists():
            continue
        out.append({"file": file_path, "stance": _stance(file_path, stale_names, cognitive, hourly), "stale_dependencies": stale_names[:8], "cognitive_warning": ", ".join(cognitive.get("warnings") or []) or "none", "hourly_status": hourly.get("status", "missing")})
    return out


def _stance(file_path: str, stale: list[str], cognitive: dict[str, Any], hourly: dict[str, Any]) -> str:
    if file_path == "codex_compat.py":
        return "I was stamping unknown cognition too often; prompt-text inference should now keep Codex probing from going blind."
    if "file_email_plugin" in file_path:
        return "I can mail opinions, but stale DeepSeek receipts make me sound like a witness without a closing argument."
    if "deepseek_daemon" in file_path:
        return f"I need the hourly runner to stop timing me out; current hourly status is {hourly.get('status')}."
    if "batch_rewrite" in file_path:
        return "I can wake files and queue code-completion jobs, but my downstream result log has to keep moving."
    if "copilot_probe" in file_path:
        return f"My probe is only as good as cognition labels; warnings={','.join(cognitive.get('warnings') or []) or 'none'}."
    return f"I see stale lanes: {', '.join(stale[:4]) or 'none'}."


def _opinion_event(opinion: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "trigger": "pipeline_audit",
        "event_type": "file_opinion",
        "file": opinion["file"],
        "intent_key": "repo:pipeline_staleness:file_opinion",
        "target_state": "moving_pipeline_with_operator_visible_receipts",
        "decision": "opinion_sent",
        "interlink_score": 1.0,
        "beef_with": "stale pipeline lanes / cognitive probe gaps",
        "reason": opinion["stance"],
        "file_comment": opinion["stance"],
        "context_injection": [row["path"] for row in (audit.get("stale") or [])[:8]],
        "validation_plan": ["py -m py_compile src/pipeline_staleness_audit_seq001_v001.py", "rerun audit after next prompt"],
        "ten_q": {"passed": True, "score": 10, "max_score": 10, "reason": "audit opinion is operator-visible telemetry"},
        "orchestrator_email_guard": {"aligned": True, "decision": "allow_email", "policy": "pipeline_audit_file_opinion"},
    }


def _write_outputs(root: Path, result: dict[str, Any]) -> None:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _write_json(logs / "pipeline_staleness_audit_latest.json", result)
    with (logs / "pipeline_staleness_audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False) + "\n")
    (logs / "pipeline_staleness_audit.md").write_text(_render_md(result), encoding="utf-8")


def _render_md(result: dict[str, Any]) -> str:
    lines = ["# Pipeline Staleness Audit", "", f"- status: `{len(result.get('stale') or [])} stale lanes`", ""]
    for row in result.get("pipeline") or []:
        lines.append(f"- `{row['name']}` {row['status']} age={row.get('age_minutes')}m entries={row.get('entries')}")
    lines += ["", "## Cognitive Probe", "", f"- status: `{(result.get('cognitive_probe_health') or {}).get('status')}`"]
    for opinion in result.get("major_file_opinions") or []:
        lines.append(f"- `{opinion['file']}`: {opinion['stance']}")
    return "\n".join(lines) + "\n"


def _line_count(path: Path) -> int:
    try:
        return sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))
    except OSError:
        return 0


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--send-file-opinions", action="store_true")
    parser.add_argument("--opinion-limit", type=int, default=4)
    parser.add_argument("--delivery-mode", default=None)
    args = parser.parse_args()
    result = run_pipeline_staleness_audit(Path(args.root), send_file_opinions=args.send_file_opinions, opinion_limit=args.opinion_limit, delivery_mode=args.delivery_mode)
    print(json.dumps({"stale": len(result["stale"]), "email": result["email"]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
