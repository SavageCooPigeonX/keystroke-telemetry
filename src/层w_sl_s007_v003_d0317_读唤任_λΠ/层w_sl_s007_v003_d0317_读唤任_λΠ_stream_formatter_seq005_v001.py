"""层w_sl_s007_v003_d0317_读唤任_λΠ_stream_formatter_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 57 lines | ~488 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json
import os
import time

class StreamFormatter:
    """Formats telemetry events into different output formats."""

    @staticmethod
    def to_json(event: dict) -> str:
        return json.dumps(event)

    @staticmethod
    def to_json_pretty(event: dict) -> str:
        return json.dumps(event, indent=2)

    @staticmethod
    def to_csv(event: dict, headers: bool = False) -> str:
        keys = ["seq", "timestamp_ms", "delta_ms", "event_type", "key",
                "cursor_pos", "buffer_len", "message_id", "session_id"]
        if headers:
            header_line = CSV_SEPARATOR.join(keys) + "\n"
        else:
            header_line = ""
        values = [str(event.get(k, "")) for k in keys]
        return header_line + CSV_SEPARATOR.join(values)

    @staticmethod
    def to_compact(event: dict) -> str:
        """Ultra-compact format: seq|ts|delta|type|key|pos|buflen"""
        return COMPACT_SEPARATOR.join([
            str(event.get("seq", 0)),
            str(event.get("timestamp_ms", 0)),
            str(event.get("delta_ms", 0)),
            event.get("event_type", "?"),
            event.get("key", "?")[:1],
            str(event.get("cursor_pos", 0)),
            str(event.get("buffer_len", 0)),
        ])

    @staticmethod
    def to_sse(event: dict, event_name: str = "keystroke") -> str:
        """Server-Sent Events format."""
        data = json.dumps(event)
        return f"event: {event_name}\ndata: {data}\n\n"

    @classmethod
    def format_event(cls, event: dict, fmt: str = "json") -> str:
        formatters = {
            "json": cls.to_json,
            "json_pretty": cls.to_json_pretty,
            "csv": cls.to_csv,
            "compact": cls.to_compact,
            "sse": cls.to_sse,
        }
        formatter = formatters.get(fmt, cls.to_json)
        return formatter(event)
