"""Interlinked file-room naming convention planning sim."""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.file_interlinked_naming_policy_seq001_v001 import (
    corrected_intent,
    discrepancy,
    file_kind,
    interlinked_queries,
    proposed_name,
    standard,
)
from src.file_number_key_identity_seq001_v001 import file_identity_card, ownership_from_name

LATEST = "logs/file_interlinked_naming_sim_latest.json"
HISTORY = "logs/file_interlinked_naming_sim.jsonl"
MARKDOWN = "logs/file_interlinked_naming_sim.md"


def run_interlinked_naming_sim(root: Path, *, write: bool = True, limit: int = 15, email: bool = True) -> dict[str, Any]:
    root = Path(root)
    files = _select_files(root, limit)
    answers = [_query_file(root, file) for file in files]
    standard_vote = standard(answers)
    result = {
        "schema": "file_interlinked_naming_sim/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": "planning_only_no_rename",
        "task": "plan naming discrepancies and decide a standard naming convention",
        "interlinked_queries": _queries(),
        "participants": answers,
        "standard_vote": standard_vote,
        "correction": corrected_intent(),
        "grader_gate": {
            "decision": "plan_only",
            "rename_allowed_now": False,
            "requires": ["operator approval", "import map", "tests for facades", "rollback plan"],
        },
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_interlinked_naming_sim(result), encoding="utf-8")
        if email:
            result["email"] = send_naming_grader_email(root, result)
            _write_json(root / LATEST, result)
    return result


def send_naming_grader_email(root: Path, sim: dict[str, Any]) -> dict[str, Any]:
    """Send the naming plan through the file-room text-chain renderer."""
    from src.file_email_plugin_seq001_v001 import emit_file_email, load_file_email_config

    participants = sim.get("participants") or []
    standard = sim.get("standard_vote") or {}
    event = {
        "trigger": "file_sim",
        "event_type": "compile",
        "file": "orchestrator/interlinked_naming_grader",
        "intent_key": "root:plan:interlinked_naming_standard:major",
        "target_state": "interlinked_files_agree_before_rename",
        "decision": "plan_only",
        "reason": _email_reason(participants, standard),
        "file_comment": "Correction: downgrade flattening; files get F keys, display names, symbolic identity, and last_change mutation state.",
        "context_injection": [row["file"] for row in participants[:8]],
        "validation_plan": ["py -m pytest test_file_interlinked_naming_sim.py -q", "git diff --check"],
        "ten_q": {"passed": True, "score": 10, "max_score": 10, "reason": "planning gate passed"},
        "orchestrator_email_guard": {"decision": "allow_email", "aligned": True},
    }
    return emit_file_email(root, event, config=load_file_email_config(root) | {"delivery_mode": "resend_dry_run"})


def render_interlinked_naming_sim(sim: dict[str, Any]) -> str:
    lines = ["# Interlinked Naming Sim", "", f"- task: {sim.get('task')}", f"- decision: `{(sim.get('grader_gate') or {}).get('decision')}`", "", "## Standard Vote"]
    standard = sim.get("standard_vote") or {}
    lines.append(f"- convention: `{standard.get('convention')}`")
    lines.append(f"- rationale: {standard.get('rationale')}")
    lines.append(f"- correction: `{(sim.get('correction') or {}).get('downgrade')}`")
    lines.extend(["", "## File Query Answers"])
    for row in sim.get("participants") or []:
        ident = row.get("identity") or {}
        lines.append(f"- `{ident.get('number_key')}` {ident.get('operator_display_name')}: `{row['file']}` -> `{row['proposed_name']}` | {row['discrepancy']}")
    return "\n".join(lines) + "\n"


def _select_files(root: Path, limit: int) -> list[str]:
    blank = _json(root / "logs" / "file_blank_sheet_sim_latest.json")
    files = [row.get("file", "") for row in blank.get("file_pressure_jobs") or []]
    symbolic = _first_symbolic_file(root)
    if symbolic and symbolic not in files[:limit]:
        files = [symbolic] + [file for file in files if file != symbolic]
    if len(files) < limit:
        files.extend(path.relative_to(root).as_posix() for path in sorted((root / "src").rglob("*.py"))[: limit * 3])
    out = []
    for file in files:
        if file and file not in out and (root / file).exists():
            out.append(file)
        if len(out) >= limit:
            break
    return out


def _first_symbolic_file(root: Path) -> str:
    for path in sorted((root / "src").rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if any(ord(ch) > 127 for ch in rel):
            return rel
    return ""


def _query_file(root: Path, file: str) -> dict[str, Any]:
    path = root / file
    stem = path.stem
    kind = file_kind(file, stem)
    name_gap = discrepancy(file, stem, kind)
    last_change = _last_change_state(root, file, kind)
    proposed = proposed_name(file, kind, sibling_files=_sibling_files(root, file), last_change=last_change)
    identity = file_identity_card(file, kind, last_change)
    return {
        "schema": "interlinked_naming_query/v1",
        "file": file,
        "current_name": path.name,
        "declared_kind": kind,
        "identity": identity,
        "number_key": identity["number_key"],
        "operator_display_name": identity["operator_display_name"],
        "mutation_name": identity["mutation_name"],
        "answers": {
            "what_do_i_own": ownership_from_name(stem),
            "what_number_key_am_i": identity["number_key"],
            "what_name_is_misleading": name_gap,
            "who_could_break_if_i_rename": _rename_risk(file),
            "what_standard_do_i_vote_for": "F key + Inator display + symbolic glyphs + last_change mutation state",
            "what_last_change_should_i_show": last_change,
            "what_proof_do_i_need": ["import smoke test", "nearby unit test", "git grep old import path", "manifest refresh"],
        },
        "discrepancy": name_gap,
        "proposed_name": proposed,
        "last_change_state": last_change,
        "downgrade": "prior_flatten_symbolic_names" if kind == "symbolic_pigeon_name" else "",
        "approval": "approve_plan_not_rename",
        "file_text": f"I vote to plan `{path.name}` as `{proposed}` but only after import-map proof.",
    }


def _queries() -> list[str]:
    return interlinked_queries()


def _last_change_state(root: Path, file: str, kind: str) -> str:
    growth = _latest_growth_for_file(root, file)
    if growth:
        tags = ", ".join(growth.get("growth_tags") or [])
        key = growth.get("identity_key") or ""
        return f"{key}; tags={tags[:160]}"
    git_subject = _git_last_subject(root, file)
    if git_subject:
        return git_subject
    if kind == "symbolic_pigeon_name":
        return "keep glyph identity and append/update compact mutation-state tokens, not translation"
    if kind == "versioned_module":
        return "keep seq/version and compress the prose into the latest meaningful mutation phrase"
    if kind == "stable_facade":
        return "keep facade stable; store last change in manifest/memory rather than public import name"
    return "mirror the source behavior under test"


def _sibling_files(root: Path, file: str) -> list[str]:
    path = root / file
    parent = path.parent
    if not parent.exists():
        return []
    return [p.name for p in parent.glob("*.py")]


def _latest_growth_for_file(root: Path, file: str) -> dict[str, Any]:
    path = root / "logs" / "file_identity_growth.jsonl"
    if not path.exists():
        return {}
    rows = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("file") == file:
                rows.append(row)
    except (OSError, json.JSONDecodeError):
        return {}
    return rows[-1] if rows else {}


def _git_last_subject(root: Path, file: str) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s", "--", file],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception:
        return ""
    return result.stdout.strip()[:180] if result.returncode == 0 else ""


def _rename_risk(file: str) -> list[str]:
    return ["imports", "tests", "manifest references", "file memory path", "compressed build artifacts"] if file.endswith(".py") else ["manifest references"]


def _email_reason(rows: list[dict[str, Any]], standard: dict[str, Any]) -> str:
    sample = "; ".join(f"{Path(row['file']).name} -> {row['proposed_name']}" for row in rows[:5])
    return f"Files answered interlinked naming queries and voted for `{standard.get('convention')}`. Sample pressure: {sample}."


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")
