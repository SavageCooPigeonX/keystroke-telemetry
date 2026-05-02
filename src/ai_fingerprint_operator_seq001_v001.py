"""Operator AI fingerprint snapshot from local prompt/profile logs."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", text)]


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _signature(parts: list[str], width: int = 16) -> dict[str, Any]:
    seed = "|".join(parts)
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    vector = [int.from_bytes(digest[i:i + 2], "big") for i in range(0, width * 2, 2)]
    return {"algorithm": "sha256_u16_v1", "hex": hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32], "vector": vector}


def _tail_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def build_operator_fingerprint(root: Path, repo_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    logs = Path(root) / "logs"
    profile = _read_json(logs / "semantic_profile.json", {})
    terms: Counter[str] = Counter()
    for row in _tail_jsonl(logs / "prompt_journal.jsonl", 200) + _tail_jsonl(logs / "prompt_brain_history.jsonl", 80):
        terms.update(_tokens(str(row.get("msg") or row.get("prompt") or row.get("final_text") or "")))
    facts = profile.get("facts", {}) if isinstance(profile, dict) else {}
    intents = profile.get("intents", {}) if isinstance(profile, dict) else {}
    seed_parts = [f"{k}={v.get('value')}" for k, v in sorted(facts.items()) if isinstance(v, dict)]
    seed_parts += [f"{k}:{v}" for k, v in sorted(intents.items())]
    seed_parts += [term for term, _ in terms.most_common(80)]
    out = {
        "schema": "ai_fingerprint/v1",
        "ts": _utc_now(),
        "facts": facts,
        "semantic_intents": intents,
        "top_prompt_terms": terms.most_common(50),
        "numeric_signature": _signature(seed_parts),
        "repo_probe": repo_summary or {},
    }
    _write_json(logs / "ai_fingerprint.json", out)
    _append_jsonl(logs / "ai_fingerprint_history.jsonl", out)
    return out
