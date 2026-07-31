"""opus_prompt_box_seq001_v001_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _tokens
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import DONE_STATUSES
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import DROP_STATUS
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import OPEN_STATUSES
from typing import Any
import re

def _boost_for_prompt(
    rows: list[dict[str, Any]],
    prompt: str,
    intent_graph: dict[str, Any],
) -> list[dict[str, Any]]:
    tokens = _tokens(prompt)
    active_keys = {str(i.get("intent_key") or "") for i in intent_graph.get("intents") or []}
    for row in rows:
        if row.get("status") in DONE_STATUSES:
            continue
        overlap = len(tokens & _tokens(" ".join([row.get("title", ""), row.get("intent_key", ""), row.get("prompt", "")])))
        if row.get("intent_key") in active_keys:
            overlap += 3
        if overlap:
            row["prompt_hits"] = int(row.get("prompt_hits") or 0) + 1
            row["priority_score"] = round(min(0.99, float(row.get("priority_score") or 0.1) + overlap * 0.04), 4)
        row["effective_score"] = round(float(row.get("priority_score") or 0.1) * float(row.get("tax_factor") or 1), 4)
    return rows


def _cap_open(rows: list[dict[str, Any]], *, max_open: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    open_rows = [row for row in rows if row.get("status") in OPEN_STATUSES or row.get("status") == "pending"]
    done_rows = [row for row in rows if row.get("status") in DONE_STATUSES]
    open_rows.sort(key=lambda row: float(row.get("effective_score") or 0), reverse=True)
    kept = open_rows[:max_open]
    dropped = []
    for row in open_rows[max_open:]:
        row = dict(row)
        row["status"] = DROP_STATUS
        row["drop_reason"] = "over_cap"
        dropped.append(row)
    for row in kept:
        row["status"] = "open"
        row["writer"] = "claude-opus"
    return kept, dropped
