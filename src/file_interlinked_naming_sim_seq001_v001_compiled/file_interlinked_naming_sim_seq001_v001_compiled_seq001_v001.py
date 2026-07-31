"""file_interlinked_naming_sim_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interlinked_naming_sim_seq001_v001_compiled_seq002_v001 import render_interlinked_naming_sim
from .file_interlinked_naming_sim_seq001_v001_compiled_seq002_v001 import send_naming_grader_email
from .file_interlinked_naming_sim_seq001_v001_compiled_seq003_v001 import _select_files
from .file_interlinked_naming_sim_seq001_v001_compiled_seq004_v001 import _queries
from .file_interlinked_naming_sim_seq001_v001_compiled_seq004_v001 import _query_file
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import HISTORY
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import LATEST
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import MARKDOWN
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import _append_jsonl
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import _write_json
from datetime import datetime, timezone
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
