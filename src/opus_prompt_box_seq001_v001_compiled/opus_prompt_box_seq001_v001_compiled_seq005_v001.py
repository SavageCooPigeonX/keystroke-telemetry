"""opus_prompt_box_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import DONE_STATUSES
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import TAX_HALF_LIFE_HOURS
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _parse_ts
from typing import Any
import math
import re

def _upsert(existing: dict[str, Any] | None, incoming: dict[str, Any], now: str) -> dict[str, Any]:
    if not existing:
        incoming.setdefault("created_ts", now)
        incoming.setdefault("last_refined_ts", now)
        incoming.setdefault("prompt_hits", 0)
        incoming.setdefault("status", "open")
        incoming.setdefault("writer", "claude-opus")
        return incoming
    if existing.get("status") in DONE_STATUSES:
        return existing
    existing["last_refined_ts"] = now
    existing["priority_score"] = max(
        float(existing.get("priority_score") or 0),
        float(incoming.get("priority_score") or 0),
    )
    existing["confidence"] = max(float(existing.get("confidence") or 0), float(incoming.get("confidence") or 0))
    for field in ("title", "scope", "manifest_path", "domain_id", "focus_files", "source"):
        if incoming.get(field) and not existing.get(field):
            existing[field] = incoming[field]
    files = list(dict.fromkeys([*(existing.get("focus_files") or []), *(incoming.get("focus_files") or [])]))
    existing["focus_files"] = files[:8]
    return existing


def _apply_tax(rows: list[dict[str, Any]], now: str) -> list[dict[str, Any]]:
    now_dt = _parse_ts(now)
    for row in rows:
        if row.get("status") in DONE_STATUSES:
            continue
        last = _parse_ts(str(row.get("last_refined_ts") or row.get("created_ts") or now))
        hours = max(0.0, (now_dt - last).total_seconds() / 3600.0)
        tax = math.pow(0.5, hours / TAX_HALF_LIFE_HOURS)
        row["tax_factor"] = round(tax, 4)
        base = float(row.get("priority_score") or 0.1)
        row["effective_score"] = round(base * tax, 4)
    return rows
