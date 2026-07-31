"""opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import re

def _numeric(tokens: list[str]) -> dict[str, Any]:
    bins = [0] * 16
    for tok in tokens:
        bins[int(hashlib.sha256(tok.encode("utf-8")).hexdigest()[:2], 16) % len(bins)] += 1
    return {"bins": bins, "token_count": len(tokens)}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


SCHEMA = "opus_micro_pulse_runtime/v1"

LATEST = "logs/opus_micro_pulse_latest.json"

HISTORY = "logs/opus_micro_pulse.jsonl"

MARKDOWN = "logs/opus_micro_pulse.md"

EXECUTOR_PROMPT = "logs/opus_executor_prompt_latest.md"


PROMPT_CLASSES = {
    "conversation": {
        "policy": "learning_packet_only",
        "mutates": False,
        "tokens": {"take", "what", "think", "idea", "maybe", "opinion", "talk", "why"},
    },
    "exploration": {
        "policy": "hypothesis_packet",
        "mutates": False,
        "tokens": {"what", "if", "could", "maybe", "imagine", "theory", "explore"},
    },
    "directive": {
        "policy": "standard_file_sim",
        "mutates": True,
        "tokens": {"build", "implement", "make", "wire", "add", "fix", "execute", "do"},
    },
    "debug": {
        "policy": "debug_chain",
        "mutates": True,
        "tokens": {"debug", "bug", "broken", "stale", "wrong", "cutoff", "failing", "test"},
    },
    "audit": {
        "policy": "audit_chain",
        "mutates": False,
        "tokens": {"audit", "assess", "review", "weakness", "risk", "grade"},
    },
    "correction": {
        "policy": "operator_contract_learning",
        "mutates": False,
        "tokens": {"wrong", "hate", "stupid", "not", "closer", "frustration", "opposite"},
    },
    "planning": {
        "policy": "architecture_packet",
        "mutates": False,
        "tokens": {"plan", "architecture", "workflow", "strategy", "system", "contract"},
    },
}
