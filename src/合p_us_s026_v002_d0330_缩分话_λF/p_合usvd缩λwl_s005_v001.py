"""合p_us_s026_v002_d0330_缩分话_λF_write_log_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 47 lines | ~395 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import json

def write_unified_log(root: Path) -> dict[str, Any]:
    """Merge all signals and write to unified_edits.jsonl.

    Returns summary stats.
    """
    events = merge_signals(root)
    if not events:
        return {"status": "no_events", "total": 0}

    out_path = root / UNIFIED_LOG
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [json.dumps(e, default=str) for e in events]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Compute stats
    sources = {}
    for e in events:
        src = e.get("edit_source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    ai_latencies = [e["ai_total_latency_ms"] for e in events
                    if e.get("ai_total_latency_ms")]
    avg_ai_latency = (sum(ai_latencies) / len(ai_latencies)
                      if ai_latencies else 0)

    rework_verdicts = [e["rework_verdict"] for e in events
                       if e.get("rework_verdict")]
    miss_rate = (sum(1 for v in rework_verdicts if v == "miss")
                 / len(rework_verdicts) if rework_verdicts else 0)

    return {
        "status": "merged",
        "total_events": len(events),
        "source_breakdown": sources,
        "avg_ai_latency_ms": round(avg_ai_latency),
        "rework_miss_rate": round(miss_rate, 3),
        "unique_files": len({e["file"] for e in events if e.get("file")}),
    }


UNIFIED_LOG = "logs/unified_edits.jsonl"
