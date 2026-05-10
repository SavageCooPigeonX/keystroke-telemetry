"""codex_compat_log_response_seq066_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_append_jsonl_seq005_v001 import _append_jsonl
from .codex_compat_bind_intent_loop_response_seq047_v001 import _bind_intent_loop_response
from .codex_compat_ensure_repo_on_path_seq009_v001 import _ensure_repo_on_path
from .codex_compat_refresh_state_seq057_v001 import refresh_state
from .codex_compat_utc_now_seq001_v001 import _utc_now
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def log_response(
    root: Path,
    prompt: str,
    response: str,
    ts: str | None = None,
    response_id: str | None = None,
    style_arm: str | None = None,
    hook_ids: list[str] | None = None,
    intent_nodes: list[str] | None = None,
    context_window_files: list[str] | None = None,
    reward_features: dict[str, Any] | None = None,
    feedback_text: str = "",
) -> dict[str, Any]:
    root = Path(root)
    entry = {
        "ts": ts or _utc_now(),
        "prompt": prompt.strip(),
        "response": response.strip(),
        "response_id": response_id or f"codex:{datetime.now(timezone.utc).timestamp():.0f}",
        "capture_surface": "codex",
    }
    try:
        _ensure_repo_on_path(root)
        from src.operator_response_policy_seq001_v001 import (
            record_response_reward,
            response_log_defaults,
        )
        defaults = response_log_defaults(root, prompt, response)
        resolved_style_arm = style_arm or defaults.get("style_arm") or "probe_council"
        resolved_intent_nodes = intent_nodes if intent_nodes is not None else defaults.get("intent_nodes", [])
        resolved_hook_ids = hook_ids if hook_ids is not None else defaults.get("hook_ids", [])
        resolved_files = context_window_files if context_window_files is not None else defaults.get("context_window_files", [])
        resolved_features = reward_features if reward_features is not None else defaults.get("reward_features", {})
        entry["response_policy"] = {
            "style_arm": resolved_style_arm,
            "intent_nodes": resolved_intent_nodes,
            "hook_ids": resolved_hook_ids,
            "context_window_files": resolved_files,
            "reward_features": resolved_features,
        }
        reward_event = record_response_reward(
            root,
            {
                "ts": entry["ts"],
                "response_id": entry["response_id"],
                "prompt": entry["prompt"],
                "response": entry["response"],
                "style_arm": resolved_style_arm,
                "intent_nodes": resolved_intent_nodes,
                "hook_ids": resolved_hook_ids,
                "context_window_files": resolved_files,
                "reward_features": resolved_features,
                "feedback_text": feedback_text,
            },
            write=True,
        )
        entry["reward_event"] = {
            "score": reward_event.get("score"),
            "weighted_score": reward_event.get("weighted_score"),
            "dimension_scores": reward_event.get("dimension_scores", {}),
            "style_model": reward_event.get("style_model", {}),
        }
    except Exception as exc:
        entry["response_policy_error"] = str(exc)
    entry["intent_loop_binding"] = _bind_intent_loop_response(root, entry)
    _append_jsonl(root / "logs" / "ai_responses.jsonl", entry)
    refresh_state(root, "logged response")
    return entry
