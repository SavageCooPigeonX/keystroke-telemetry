"""codex_compat_log_edit_seq068_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_append_jsonl_seq005_v001 import _append_jsonl
from .codex_compat_bind_intent_loop_edit_seq048_v001 import _bind_intent_loop_edit
from .codex_compat_ensure_repo_on_path_seq009_v001 import _ensure_repo_on_path
from .codex_compat_git_changed_files_seq067_v001 import _git_changed_files
from .codex_compat_load_jsonl_tail_seq007_v001 import _load_jsonl_tail
from .codex_compat_refresh_state_seq057_v001 import refresh_state
from .codex_compat_train_numeric_surface_seq016_v001 import train_numeric_surface
from .codex_compat_utc_now_seq001_v001 import _utc_now
from pathlib import Path
from typing import Any
import json
import re

def log_edit(
    root: Path,
    file: str | None = None,
    why: str = "codex edit",
    prompt: str | None = None,
    ts: str | None = None,
    session_n: int | None = None,
) -> list[dict[str, Any]]:
    root = Path(root)
    journal_tail = _load_jsonl_tail(root / "logs" / "prompt_journal.jsonl", max_lines=1)
    latest_prompt = journal_tail[-1] if journal_tail else {}
    session_n = session_n or int(latest_prompt.get("session_n", 0) or 0)
    prompt = prompt if prompt is not None else str(latest_prompt.get("msg", ""))
    files = [file] if file else _git_changed_files(root)
    if not files:
        files = ["unknown"]

    now = ts or _utc_now()
    records = []
    for changed in files:
        entry = {
            "ts": now,
            "prompt_ts": latest_prompt.get("ts", now),
            "prompt_msg": prompt[:200],
            "file": changed,
            "edit_ts": now,
            "edit_why": why,
            "edit_hash": "codex",
            "latency_ms": 0,
            "state": latest_prompt.get("cognitive_state", "unknown"),
            "session_n": session_n,
            "source": "codex_explicit",
        }
        try:
            _ensure_repo_on_path(root)
            from src.file_email_plugin_seq001_v001 import emit_touch_email
            entry["file_email"] = emit_touch_email(root, changed, why=why, prompt=prompt)
        except Exception as exc:
            entry["file_email_error"] = str(exc)
        entry["intent_loop_binding"] = _bind_intent_loop_edit(root, entry)
        _append_jsonl(root / "logs" / "edit_pairs.jsonl", entry)
        records.append(entry)
    train_numeric_surface(root, prompt, files)
    refresh_state(root, f"logged {len(records)} edit(s)")
    return records
