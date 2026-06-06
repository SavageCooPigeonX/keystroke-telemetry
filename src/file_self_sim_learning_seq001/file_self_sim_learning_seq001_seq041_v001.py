"""file_self_sim_learning_seq001_seq041_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _load_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            if isinstance(data, dict):
                rows.append(data)
    except Exception:
        return []
    return rows


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA = "file_self_sim_learning/v1"

PACKET_SCHEMA = "deepseek_file_learning_packet/v1"

OUTCOME_SCHEMA = "file_self_sim_learning_outcome/v1"


STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "should",
    "would", "could", "have", "make", "work", "working", "actual", "using",
    "based", "time", "over", "all", "about", "then", "than", "their",
    "there", "what", "when", "where", "which", "want", "need", "needs",
    "themselves",
}


ALIASES = {
    "sims": "sim",
    "simulation": "sim",
    "simulations": "sim",
    "simulated": "sim",
    "simulating": "sim",
    "neumeric": "numeric",
    "neumaric": "numeric",
    "deepseekk": "deepseek",
    "knowlege": "knowledge",
    "manofest": "manifest",
}


DEFAULT_CONFIG = {
    "mode": "learning_only_no_overwrite",
    "max_packets": 8,
    "token_budget": 24000,
    "soft_line_cap": 200,
    "warn_line_cap": 300,
    "hard_line_cap": 500,
    "split_plan_limit": 8,
    "overwrite_allowed": False,
    "target_state": "interlinked_source_state",
    "deepseek_packet_policy": "draft_only_until_operator_approval",
    "update_file_profiles": True,
}
