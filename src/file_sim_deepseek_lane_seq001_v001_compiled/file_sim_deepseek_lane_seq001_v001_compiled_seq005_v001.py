"""file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def _blocked_delegates(hush: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "schema": "file_deepseek_delegate/v1",
        "status": "blocked_by_hush_mutation_fence",
        "jobs": [],
        "grader_contract": {
            "direct_overwrite_allowed": False,
            "source_mutation_allowed": False,
            "reason": ((hush or {}).get("repo_classification") or {}).get("reason", "Hush blocked mutation"),
        },
    }


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")

PROMPT_JOBS = "logs/deepseek_prompt_jobs.jsonl"

CONTEXT_PACK = "logs/file_sim_deepseek_context_pack.json"
