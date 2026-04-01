# ┌──────────────────────────────────────────────┐
# │  unified_signal — merges ALL edit/response     │
# │  sources into one canonical event stream.      │
# │  The single source of truth for "what          │
# │  actually happened" in this codebase.          │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-30T07:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  initial unified signal merger
# EDIT_STATE: harvested
# ── /pulse ──
"""
Unified Signal Merger — joins all telemetry into canonical edit events.

SIX input sources → ONE output stream:
  1. copilot_edits.jsonl   — real-time file mutations (chars, lines, source)
  2. edit_pairs.jsonl      — pulse-harvested prompt→file bindings
  3. ai_responses.jsonl    — prompt/response with AI cognition timing
  4. os_keystrokes.jsonl   — clipboard + context signals (for paste detection)
  5. rework_log.json       — was the AI output good? (ok/miss)
  6. git diff              — commit-level ground truth

Output: logs/unified_edits.jsonl — one event per file mutation with:
  - WHO caused it (copilot_inline, copilot_apply, copilot_edit, human, paste)
  - WHAT changed (file, chars, lines)
  - WHY (linked prompt, AI response timing, edit_why)
  - HOW WELL (rework verdict, latency)
"""

# ── pigeon ────────────────────────────────────
# SEQ: 026 | VER: v002 | 233 lines | ~2,074 tokens
# DESC:   joins_all_telemetry_into_canonical
# INTENT: gemini_flash_enricher
# LAST:   2026-03-30 @ 5018891
# SESSIONS: 1
# ──────────────────────────────────────────────

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UNIFIED_LOG = "logs/unified_edits.jsonl"
JOIN_WINDOW_MS = 15_000  # 15s window for correlating events across sources


def _parse_ts(ts_val: Any) -> float:
    """Convert any timestamp format to epoch ms."""
    if isinstance(ts_val, (int, float)):
        # Already epoch ms if > 1e12, epoch seconds if < 1e12
        return ts_val if ts_val > 1e12 else ts_val * 1000
    if isinstance(ts_val, str):
        try:
            dt = datetime.fromisoformat(ts_val)
            return dt.timestamp() * 1000
        except (ValueError, TypeError):
            return 0.0
    return 0.0


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("entries", data.get("events", []))


def _find_nearest(entries: list[dict[str, Any]], target_ms: float,
                   ts_key: str = "ts", window_ms: float = JOIN_WINDOW_MS
                   ) -> dict[str, Any] | None:
    """Find the entry closest to target_ms within window."""
    best = None
    best_delta = window_ms
    for e in entries:
        e_ms = _parse_ts(e.get(ts_key, 0))
        delta = abs(e_ms - target_ms)
        if delta < best_delta:
            best_delta = delta
            best = e
    return best


def merge_signals(root: Path, window_ms: float = JOIN_WINDOW_MS) -> list[dict[str, Any]]:
    """Merge all telemetry sources into canonical unified edit events.

    Returns list of unified events sorted by timestamp.
    """
    # Load all sources
    copilot_edits = _load_jsonl(root / "logs" / "copilot_edits.jsonl")
    edit_pairs = _load_jsonl(root / "logs" / "edit_pairs.jsonl")
    ai_responses = _load_jsonl(root / "logs" / "ai_responses.jsonl")
    rework_entries = _load_json(root / "rework_log.json")

    # Index AI responses by timestamp for fast lookup
    ai_by_ts = sorted(ai_responses, key=lambda r: _parse_ts(r.get("ts", 0)))

    # Index rework entries
    rework_by_ts = sorted(rework_entries, key=lambda r: _parse_ts(r.get("ts", 0)))

    unified: list[dict[str, Any]] = []

    # ── Source 1: copilot_edits (primary — real-time file mutations) ──
    for ce in copilot_edits:
        ts_ms = _parse_ts(ce.get("ts", 0))
        if ts_ms == 0:
            continue

        # Correlate with nearest AI response
        ai_match = _find_nearest(ai_by_ts, ts_ms, window_ms=window_ms)
        # Correlate with nearest rework verdict
        rework_match = _find_nearest(rework_by_ts, ts_ms, window_ms=60_000)

        event: dict[str, Any] = {
            "ts": ts_ms,
            "file": ce.get("file", ""),
            "chars_inserted": ce.get("chars_inserted", 0),
            "chars_replaced": ce.get("chars_replaced", 0),
            "lines_added": ce.get("lines_added", 0),
            "edit_source": ce.get("edit_source", "unknown"),
            "origin": "copilot_edits",
        }

        if ai_match:
            event["ai_prompt"] = (ai_match.get("prompt") or "")[:200]
            event["ai_response_len"] = len(ai_match.get("response") or "")
            event["ai_queue_latency_ms"] = ai_match.get("queue_latency_ms")
            event["ai_generation_time_ms"] = ai_match.get("generation_time_ms")
            event["ai_total_latency_ms"] = ai_match.get("total_latency_ms")
            event["ai_model"] = ai_match.get("model") or ai_match.get("source")

        if rework_match:
            event["rework_verdict"] = rework_match.get("verdict")
            event["rework_score"] = rework_match.get("rework_score")

        unified.append(event)

    # ── Source 2: edit_pairs not already covered by copilot_edits ──
    ce_files_at_ts = {(_parse_ts(ce.get("ts", 0)), ce.get("file", ""))
                      for ce in copilot_edits}

    for ep in edit_pairs:
        ts_ms = _parse_ts(ep.get("ts", 0))
        ep_file = ep.get("file", "")
        # Skip if already captured by copilot_edits (within window)
        already_covered = any(
            abs(ts_ms - ct) < window_ms and ep_file == cf
            for ct, cf in ce_files_at_ts
        )
        if already_covered:
            continue

        event = {
            "ts": ts_ms,
            "file": ep_file,
            "chars_inserted": 0,  # edit_pairs don't track this
            "chars_replaced": 0,
            "lines_added": 0,
            "edit_source": "pulse_harvest",
            "origin": "edit_pairs",
            "edit_why": ep.get("edit_why"),
            "prompt_msg": (ep.get("prompt_msg") or "")[:200],
            "latency_ms": ep.get("latency_ms"),
            "operator_state": ep.get("state"),
        }
        unified.append(event)

    unified.sort(key=lambda e: e.get("ts", 0))
    return unified


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


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = write_unified_log(root)
    print(json.dumps(result, indent=2))
