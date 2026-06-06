"""codex_compat_seq027_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _parse_deleted_words
from .codex_compat_seq007_v001 import _latest_json
from .codex_compat_seq026_v001 import _latest_log_ts
from .codex_compat_seq026_v001 import _parse_iso_ts
from .codex_compat_seq033_v001 import _load_json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re

def audit_stale_dates(root: Path, max_lag_minutes: int = 30) -> dict[str, Any]:
    root = Path(root)
    logs = root / "logs"
    now = datetime.now(timezone.utc)
    surfaces = {
        "prompt_journal": "logs/prompt_journal.jsonl",
        "chat_compositions": "logs/chat_compositions.jsonl",
        "pre_prompt_state": "logs/pre_prompt_state.json",
        "dynamic_context_pack": "logs/dynamic_context_pack.json",
        "batch_rewrite_sim": "logs/batch_rewrite_sim_latest.json",
        "intent_loop": "logs/intent_loop_latest.json",
        "file_email_outbox": "logs/file_email_outbox.jsonl",
        "resend_payload": "logs/resend_payload_latest.json",
        "deepseek_prompt": "logs/deepseek_prompt_latest.json",
    }
    rows = {}
    latest_prompt_ts = None
    for name, rel in surfaces.items():
        ts, data = _latest_log_ts(root, rel)
        if name == "prompt_journal":
            latest_prompt_ts = ts
        rows[name] = {
            "path": rel,
            "ts": ts.isoformat() if ts else "",
            "age_minutes": round((now - ts).total_seconds() / 60, 2) if ts else None,
            "status": data.get("status") if isinstance(data, dict) else None,
            "trigger": data.get("trigger") if isinstance(data, dict) else None,
        }
    baseline = latest_prompt_ts or now
    for row in rows.values():
        ts = _parse_iso_ts(row.get("ts"))
        row["lag_from_prompt_minutes"] = round((baseline - ts).total_seconds() / 60, 2) if ts else None
        row["stale"] = bool(ts and (baseline - ts).total_seconds() > max_lag_minutes * 60)

    latest_comp = _latest_json(logs / "chat_compositions.jsonl") or {}
    hidden_words = _parse_deleted_words(
        list(latest_comp.get("deleted_words") or []) + list(latest_comp.get("intent_deleted_words") or []),
        str(latest_comp.get("deleted_text") or ""),
    )
    file_sim_config = _load_json(logs / "file_sim_config.json") or {}
    pre_prompt = _load_json(logs / "pre_prompt_state.json") or {}
    trigger = str(pre_prompt.get("trigger") or "")
    fire_on = file_sim_config.get("fire_on") if isinstance(file_sim_config.get("fire_on"), list) else []
    result = {
        "schema": "stale_date_audit/v1",
        "ts": now.isoformat(),
        "max_lag_minutes": max_lag_minutes,
        "latest_prompt_ts": baseline.isoformat(),
        "hidden_words_latest": hidden_words,
        "trigger_audit": {
            "latest_pre_prompt_trigger": trigger,
            "file_sim_fire_on": fire_on,
            "trigger_allowed": (not trigger) or trigger in fire_on,
        },
        "surfaces": rows,
        "stale": [name for name, row in rows.items() if row.get("stale")],
    }
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "stale_date_audit_latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Stale Date Audit",
        "",
        f"- latest_prompt_ts: `{result['latest_prompt_ts']}`",
        f"- max_lag_minutes: `{max_lag_minutes}`",
        f"- hidden_words_latest: `{', '.join(hidden_words) or 'none'}`",
        f"- trigger_allowed: `{result['trigger_audit']['trigger_allowed']}`",
        "",
        "## Surfaces",
        "",
    ]
    for name, row in rows.items():
        lines.append(
            f"- `{name}` ts `{row.get('ts') or 'missing'}` lag `{row.get('lag_from_prompt_minutes')}` stale `{row.get('stale')}`"
        )
    (logs / "stale_date_audit_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result
