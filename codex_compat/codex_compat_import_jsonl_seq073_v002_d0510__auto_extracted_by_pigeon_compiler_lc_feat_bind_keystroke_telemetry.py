"""codex_compat_import_jsonl_seq073_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 073 | VER: v002 | 61 lines | ~878 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_capture_pair_seq069_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import capture_pair
from .codex_compat_log_composition_seq063_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import log_composition
from .codex_compat_log_edit_seq068_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import log_edit
from .codex_compat_log_prompt_seq062_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import log_prompt
from .codex_compat_log_response_seq066_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import log_response
from .codex_compat_text_from_event_seq072_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _text_from_event
from pathlib import Path
import json
import os
import re

def import_jsonl(root: Path, source: Path, capture: bool = True) -> dict[str, int]:
    root = Path(root)
    counts = {"prompts": 0, "responses": 0, "edits": 0, "pairs": 0}
    last_prompt = ""

    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue

        event_type = str(event.get("type") or event.get("event") or "").lower()
        role = str(event.get("role") or "").lower()
        text = _text_from_event(event)
        ts = event.get("ts") or event.get("timestamp") or event.get("time")

        if role == "user" or event_type in {"user", "user_message", "prompt"}:
            if text.strip():
                deleted_text = str(event.get("deleted_text") or "")
                deleted_words = event.get("deleted_words") if isinstance(event.get("deleted_words"), list) else []
                entry = log_prompt(root, text, ts=ts, deleted_words=deleted_words, deleted_text=deleted_text)
                last_prompt = entry["msg"]
                counts["prompts"] += 1
        elif event_type in {"composition", "chat_composition"}:
            if text.strip():
                deleted_text = str(event.get("deleted_text") or "")
                deleted_words = event.get("deleted_words") if isinstance(event.get("deleted_words"), list) else []
                log_composition(root, text, deleted_text=deleted_text, deleted_words=deleted_words)
                last_prompt = text
                counts["prompts"] += 1
        elif role == "assistant" or event_type in {"assistant", "assistant_message", "response"}:
            if text.strip():
                prompt = str(event.get("prompt") or last_prompt)
                log_response(root, prompt, text, ts=ts)
                counts["responses"] += 1
        elif event_type in {"edit", "file_change", "file_edit", "tool_edit"}:
            changed = event.get("file") or event.get("path") or event.get("target")
            why = str(event.get("why") or event.get("summary") or event.get("message") or "codex edit")
            records = log_edit(root, file=str(changed) if changed else None, why=why, prompt=last_prompt, ts=ts)
            counts["edits"] += len(records)
            if capture:
                pair = capture_pair(root)
                if pair:
                    counts["pairs"] += 1
    return counts
