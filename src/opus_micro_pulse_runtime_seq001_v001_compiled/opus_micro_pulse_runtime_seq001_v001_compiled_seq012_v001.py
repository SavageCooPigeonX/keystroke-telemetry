"""opus_micro_pulse_runtime_seq001_v001_compiled_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _git_changed_files
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _now
from pathlib import Path
from typing import Any
import re

def _quick_fix_queue(interrogations: list[dict[str, Any]], stale: list[dict[str, Any]]) -> list[str]:
    rows = []
    for item in interrogations:
        mismatch = str(item.get("mismatch") or "")
        if "flattening" in mismatch:
            rows.append(f"`{item.get('file')}` update syntax/numeric triggers if Codex actually touches this file")
        faults = str(item.get("persistent_faults") or "")
        if faults and "low-touch" not in faults and "observations=" not in faults:
            rows.append(f"`{item.get('file')}` verify persistent fault: {faults}")
    for item in stale:
        rows.append(f"`{item.get('owner')}` stale pressure: {item.get('title')} -> {item.get('next_action')}")
    return _dedupe(rows)


def _dedupe(rows: list[str]) -> list[str]:
    return list(dict.fromkeys(row for row in rows if row))


def _pending_backward_packet(root: Path, prompt_hash: str, predicted_files: list[str], cannon: dict[str, Any]) -> dict[str, Any]:
    touched = _git_changed_files(root)
    predicted = list(dict.fromkeys(predicted_files[:18]))
    touched_set = set(touched)
    predicted_set = set(predicted)
    return {
        "schema": "backward_file_intelligence_learning_pending/v1",
        "ts": _now(),
        "prompt_hash": prompt_hash,
        "status": "pending_until_executor_diff_or_next_file_call",
        "executor_session": cannon.get("executor_session"),
        "metric": "opus_dynamic_file_intelligence_prediction_vs_codex_execution_diff",
        "predicted_files": predicted,
        "currently_touched_files": touched[:40],
        "true_positive_now": sorted(predicted_set & touched_set),
        "missed_by_opus_now": sorted(touched_set - predicted_set)[:40],
        "dead_weight_now": sorted(predicted_set - touched_set)[:40],
        "learning_rule": (
            "Touched+predicted raises trigger confidence; touched+not-predicted adds syntax/numeric triggers; "
            "predicted+untouched waits pending until that file is called again."
        ),
    }
