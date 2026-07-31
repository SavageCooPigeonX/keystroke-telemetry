"""opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _tokens
from pathlib import Path
from typing import Any
import json
import re

def _session_broker(classification: dict[str, Any], text: str) -> dict[str, Any]:
    cls = classification["prompt_class"]
    low = text.lower()
    if cls in {"conversation", "correction", "exploration"}:
        session = "opus_learning_only"
        reason = "prompt teaches operator/file intelligence without immediate executor mutation"
    elif re.search(r"\b(ui|frontend|design|css|jsx|screen|layout)\b", low):
        session = "copilot_ui_session"
        reason = "UI/design language favors visible iterative executor"
    elif cls in {"debug", "directive"}:
        session = "codex_execution_session"
        reason = "clear repair/build intent should become bounded diff"
    elif cls == "audit":
        session = "deepseek_audit_session"
        reason = "audit prompt should inspect and grade before mutation"
    else:
        session = "claude_code_architecture_session"
        reason = "architecture/planning prompt needs long-context orchestration"
    return {"executor_session": session, "reason": reason}


def _intent_keys(text: str, classification: dict[str, Any]) -> list[str]:
    tokens = _tokens(text)
    anchors = [tok for tok in tokens if tok in {
        "opus", "micro", "pulse", "file", "manifest", "prompt", "codex", "backward",
        "diff", "intent", "keys", "debug", "stale", "simulation", "folder", "deepseek",
        "gemini", "copilot", "executor", "runtime", "learning", "syntax",
    }]
    if not anchors:
        anchors = tokens[:4]
    keys = [f"{classification['prompt_class']}:{tok}" for tok in anchors[:10]]
    return list(dict.fromkeys(keys)) or [f"{classification['prompt_class']}:general"]


def _identity_from_path(rel: str) -> str:
    name = Path(rel.replace("\\", "/")).stem.replace("_", " ")
    if rel.endswith(".jsonl") or rel.endswith(".json"):
        return f"log/state artifact for {name}"
    if rel.endswith(".md"):
        return f"manifest/readable state document for {name}"
    return f"code module for {name}"


def _folder_for(rel: str) -> str:
    clean = rel.replace("\\", "/").strip("/")
    if not clean or "/" not in clean:
        return "."
    return str(Path(clean).parent).replace("\\", "/")
