"""合p_us_s026_v002_d0330_缩分话_λF_merge_signals_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 91 lines | ~895 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import json

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
