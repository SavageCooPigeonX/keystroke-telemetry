"""Surface file and pipeline bug signals for the master manifest."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "file_bug_surface/v1"


def build_file_bug_surface(root: Path, *, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    stale = _load_json(root / "logs" / "pipeline_staleness_audit_latest.json") or {}
    compliance = _load_json(root / "logs" / "pigeon_compliance_push_latest.json") or {}
    dead = _load_json(root / "logs" / "dead_stale_code_audit_latest.json") or {}
    bugs = []
    bugs.extend(_pipeline_bugs(stale))
    bugs.extend(_file_opinion_bugs(stale))
    bugs.extend(_compliance_bugs(compliance))
    bugs.extend(_dead_stale_bugs(dead))
    bugs = _dedupe_bugs(bugs)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "bug_count": len(bugs),
        "bugs": bugs[:80],
        "most_logical_autonomous_action": _autonomous_action(bugs),
        "orchestrator_handoff": _orchestrator_handoff(bugs),
        "paths": {
            "latest": "logs/file_bug_surface_latest.json",
            "history": "logs/file_bug_surface.jsonl",
            "markdown": "logs/file_bug_surface.md",
        },
    }
    if write:
        logs = root / "logs"
        _write_json(logs / "file_bug_surface_latest.json", result)
        _append_jsonl(logs / "file_bug_surface.jsonl", result)
        (logs / "file_bug_surface.md").write_text(render_file_bug_surface(result), encoding="utf-8")
    return result


def render_file_bug_surface(surface: dict[str, Any]) -> str:
    lines = [
        "# File Bug Surface",
        "",
        f"- bugs: `{surface.get('bug_count', 0)}`",
        f"- autonomous_action: {surface.get('most_logical_autonomous_action', '')}",
        "",
        "## Bugs",
    ]
    for bug in surface.get("bugs") or []:
        lines.append(f"- `{bug.get('severity')}` `{bug.get('owner')}` {bug.get('title')} :: {bug.get('evidence')}")
    lines.extend(["", "## Orchestrator Handoff", surface.get("orchestrator_handoff", {}).get("markdown", "")])
    return "\n".join(lines) + "\n"


def _pipeline_bugs(stale: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in stale.get("stale") or []:
        rows.append({
            "bug_id": f"stale:{row.get('name')}",
            "source": "pipeline_staleness_audit",
            "owner": row.get("path", ""),
            "severity": "P1" if row.get("name") in {"deepseek_results", "code_completion_jobs"} else "P2",
            "title": f"stale pipeline lane: {row.get('name')}",
            "evidence": f"age={row.get('age_minutes')}m max={row.get('max_age_minutes')}m entries={row.get('entries')}",
            "next_action": _stale_action(str(row.get("name") or "")),
        })
    cog = stale.get("cognitive_probe_health") or {}
    if cog.get("status") == "weak":
        rows.append({
            "bug_id": "cognition:weak_probe",
            "source": "pipeline_staleness_audit",
            "owner": "logs/operator_intent_888.json",
            "severity": "P1",
            "title": "weak cognitive probe coverage",
            "evidence": f"unknown_ratio={cog.get('unknown_ratio')} coverage_gap={cog.get('coverage_gap')}",
            "next_action": "rebuild operator intent labels from prompt journal before trusting behavioral routing",
        })
    return rows


def _file_opinion_bugs(stale: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for opinion in stale.get("major_file_opinions") or []:
        deps = ", ".join(opinion.get("stale_dependencies") or [])
        rows.append({
            "bug_id": "file_opinion:" + str(opinion.get("file", "")),
            "source": "major_file_opinion",
            "owner": opinion.get("file", ""),
            "severity": "P2",
            "title": "file reports stale dependency pressure",
            "evidence": f"{opinion.get('stance', '')} deps={deps}",
            "next_action": "route file opinion into folder manifest and master bug queue",
        })
    return rows


def _compliance_bugs(compliance: dict[str, Any]) -> list[dict[str, Any]]:
    warning_count = int(compliance.get("warning_count") or 0)
    violation_count = int(compliance.get("violation_count") or 0)
    rows = []
    if warning_count:
        rows.append({
            "bug_id": "compliance:warnings",
            "source": "pigeon_compliance_push",
            "owner": "logs/pigeon_compliance_push_latest.json",
            "severity": "P2",
            "title": "compiler saw compliance warning pressure",
            "evidence": f"warnings={warning_count} violations={violation_count}",
            "next_action": "sample warning owners and schedule bounded split/cleanup jobs",
        })
    if violation_count:
        rows.append({
            "bug_id": "compliance:violations",
            "source": "pigeon_compliance_push",
            "owner": "logs/pigeon_compliance_push_latest.json",
            "severity": "P0",
            "title": "push compliance violations",
            "evidence": f"violations={violation_count}",
            "next_action": "block push until violations are closed",
        })
    return rows


def _dead_stale_bugs(dead: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    count = int(dead.get("findings_count") or 0)
    if count:
        rows.append({
            "bug_id": "dead_stale:findings",
            "source": "dead_stale_code_audit",
            "owner": "logs/dead_stale_code_audit_latest.json",
            "severity": "P2",
            "title": "dead/stale code audit has unresolved findings",
            "evidence": f"findings={count} categories={dead.get('category_counts', {})}",
            "next_action": "promote stale_suspect samples into file-chain debug jobs",
        })
    return rows


def _autonomous_action(bugs: list[dict[str, Any]]) -> str:
    ids = {bug.get("bug_id") for bug in bugs}
    if "stale:deepseek_results" in ids:
        return "repair DeepSeek result receipt lane, then rerun file-sim code job closure"
    if "stale:edit_pairs" in ids:
        return "refresh prompt-to-edit pair extraction so learning can trust recent work"
    if "cognition:weak_probe" in ids:
        return "recompile operator intent labels from prompt journal"
    return "run standard manifest refresh and keep bug queue visible"


def _orchestrator_handoff(bugs: list[dict[str, Any]]) -> dict[str, Any]:
    top = sorted(bugs, key=lambda row: row.get("severity", "P9"))[:8]
    lines = ["### Talk To Orchestrator", "", "Ask the orchestrator to pick one autonomous repair chain:", ""]
    for bug in top:
        lines.append(f"- `{bug.get('bug_id')}` {bug.get('next_action')}")
    lines.append("")
    lines.append("Debug route: file sim -> grader -> job -> Opus-selected file chain -> manifest writeback.")
    return {"top_bug_ids": [bug.get("bug_id") for bug in top], "markdown": "\n".join(lines)}


def _stale_action(name: str) -> str:
    return {
        "deepseek_results": "verify queued DeepSeek jobs have receipts or mark them expired",
        "code_completion_jobs": "close stale code job queue before creating more file jobs",
        "file_self_learning": "rerun file self-learning so manifests reflect recent prompt behavior",
        "edit_pairs": "regenerate prompt-to-edit pairs from git and prompt journal",
    }.get(name, "refresh stale lane and write receipt")


def _dedupe_bugs(bugs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = {}
    for bug in bugs:
        out.setdefault(str(bug.get("bug_id") or bug.get("title")), bug)
    return list(out.values())


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
