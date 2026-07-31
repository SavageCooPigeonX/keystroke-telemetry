"""root_sim_key_file_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any

def _attention_plan(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    quotas = [
        ("prompt_intent", 6),
        ("manifest_shard", 3),
        ("bug_chat", 4),
        ("opus_pulse", 4),
        ("probe_wake", 3),
        ("low_touch", 2),
    ]
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for slot, quota in quotas:
        pool = _slot_pool(rows, slot)
        for row in pool:
            if len([r for r in selected if r["attention_slot"] == slot]) >= quota:
                break
            if row["file"] in seen:
                continue
            selected.append({**row, "attention_slot": slot})
            seen.add(row["file"])
    for row in rows:
        if len(selected) >= limit:
            break
        if row["file"] not in seen:
            selected.append({**row, "attention_slot": "fill"})
            seen.add(row["file"])
    return selected[:limit]

def _slot_pool(rows: list[dict[str, Any]], slot: str) -> list[dict[str, Any]]:
    if slot == "low_touch":
        return [row for row in rows if not row.get("operator_comment") and "probe_wake" not in row.get("kind", "")]
    return [row for row in rows if slot in row.get("kind", "")]
