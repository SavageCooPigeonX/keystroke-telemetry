"""batch_rewrite_sim_seq001_seq034_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re

def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _load_jsonl(path: Path, max_rows: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[:max_rows]:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

SCHEMA = "batch_rewrite_sim/v1"

STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "should",
    "would", "could", "have", "make", "work", "working", "actual", "using",
    "based", "time", "over", "all", "about", "then", "than",
}

VERBS = {
    "patch": {"fix", "patch", "bug", "repair", "self", "healing"},
    "build": {"build", "add", "wire", "implement", "create", "ship"},
    "refactor": {"rewrite", "rewrites", "refactor", "split", "migrate"},
    "validate": {"test", "validate", "check", "verify", "compile"},
    "route": {"intent", "orchestrator", "context", "inject", "routing"},
}

RISKY_SUFFIXES = {".json", ".jsonl", ".db", ".sqlite", ".pgd"}

RISKY_BITS = ("pigeon_brain/", "node_memory", "registry", "copilot-instructions")

SOURCE_SUFFIXES = {".py", ".ps1", ".js", ".jsx", ".ts", ".tsx", ".css", ".html"}

DEFAULT_CONFIG = {
    "enabled": True,
    "fire_on": ["manual", "pre_prompt", "composition", "composition_submit", "log_prompt", "os_hook_auto"],
    "max_proposals": 6,
    "history_limit": 10000,
    "source_only": True,
    "target_state": "interlinked_source_state",
    "min_chars": 8,
    "min_interlink_score": 0.0,
    "auto_apply": False,
    "orchestrator_oath": True,
    "push_narrative_file_comedy": True,
    "orchestrator_policy": {
        "orchestrator_only": True,
        "monitor_per_prompt": True,
        "email_per_prompt": True,
        "approval_required": True,
        "auto_write_allowed": False,
    },
    "consensus_guard": {
        "enabled": True,
        "min_score": 7,
        "required_passes": [
            "intent_alignment",
            "context_available",
            "validation_plan",
            "source_target",
            "operator_approval",
        ],
        "email_send_policy": "block_resend_when_failed",
        "deepseek_queue_policy": "only_when_passed",
    },
    "rewrite_orchestration": {
        "proposal_model": "gemini_quick",
        "grader_model": "gemini_quick_grader",
        "context_injector": "manifest_prompt_brain_context_pack",
        "deep_rewrite_model": "deepseek_deep_path",
        "reasoning_policy": {
            "proposal": "low_latency",
            "grader": "focused",
            "overwrite": "deep_only_after_approval",
            "compile": "strict_validation",
        },
    },
    "compiler_layers": {
        "file_history": True,
        "distributed_intent_encoding": True,
        "self_monitoring": True,
        "file_identity_dynamic_growth": True,
        "file_self_learning": True,
    },
}
