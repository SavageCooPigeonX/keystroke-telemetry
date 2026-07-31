"""file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from src.file_interlinked_naming_policy_seq001_v001 import (
    corrected_intent,
    discrepancy,
    file_kind,
    interlinked_queries,
    proposed_name,
    standard,
)
from typing import Any
import json
import re
import subprocess

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

LATEST = "logs/file_interlinked_naming_sim_latest.json"

HISTORY = "logs/file_interlinked_naming_sim.jsonl"

MARKDOWN = "logs/file_interlinked_naming_sim.md"
