"""codex_compat_write_unsaid_seq065_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_append_jsonl_seq005_v001 import _append_jsonl
from .codex_compat_parse_deleted_words_seq003_v001 import _parse_deleted_words
from pathlib import Path
from typing import Any
import json
import os
import re

def _write_unsaid(root: Path, composition: dict[str, Any]) -> None:
    deleted_words = _parse_deleted_words(
        composition.get("deleted_words") if isinstance(composition.get("deleted_words"), list) else [],
        str(composition.get("deleted_text") or ""),
    )
    if not deleted_words:
        return
    reconstructed = composition.get("unsaid_reconstruction", "")
    latest = {
        "ts": composition.get("ts"),
        "fragment": " ".join(deleted_words[:12]),
        "completed_intent": reconstructed,
        "deleted_words": deleted_words,
        "context": "codex",
        "source": "codex_composition",
    }
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "unsaid_latest.json").write_text(json.dumps(latest, indent=2, ensure_ascii=False), encoding="utf-8")
    _append_jsonl(logs / "unsaid_history.jsonl", latest)
    _append_jsonl(
        logs / "unsaid_reconstructions.jsonl",
        {
            "ts": composition.get("ts"),
            "deleted_words": deleted_words,
            "reconstructed_intent": reconstructed,
            "source": "codex_composition",
        },
    )
