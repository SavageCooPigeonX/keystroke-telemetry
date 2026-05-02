"""Privacy helpers for closed-repo AI fingerprint indexing."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def repo_ref(label: str, repo: Path | str) -> str:
    raw = str(repo)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"closed:{label}:{digest}"


def hash_terms(top_terms: list[Any], limit: int = 16) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in top_terms[:limit]:
        term = item[0] if isinstance(item, (list, tuple)) and item else str(item)
        count = item[1] if isinstance(item, (list, tuple)) and len(item) > 1 else 1
        digest = hashlib.sha256(str(term).encode("utf-8")).hexdigest()[:16]
        out.append({"hash": digest, "count": count})
    return out


def path_hash(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]


def private_record_touch(
    root: Path,
    numeric: Any,
    prompt_text: str,
    files_touched: list[str],
    learning_rate: float = 0.18,
) -> bool:
    """Train the existing numeric matrix without writing raw prompt previews."""
    if not getattr(numeric, "_matrix_loaded", False):
        numeric._load_matrix()
    numeric._heal_surface()
    prompt_vec = numeric.prompt_to_vector(prompt_text)
    if not prompt_vec:
        return False
    for file_path in files_touched:
        file_key = numeric.canonicalize_file_key(file_path)
        if numeric._should_skip_file_key(file_key):
            continue
        if file_key not in numeric._matrix:
            numeric._matrix[file_key] = {}
            numeric._touch_counts[file_key] = 0
        numeric._touch_counts[file_key] += 1
        for wid, weight in prompt_vec.items():
            old = numeric._matrix[file_key].get(wid, 0.0)
            numeric._matrix[file_key][wid] = old * (1 - learning_rate) + weight * learning_rate
    numeric._save_matrix()
    _append_jsonl(root / "logs" / "private_numeric_training.jsonl", {
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt_hash": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:24],
        "files": [numeric.canonicalize_file_key(f) for f in files_touched],
        "vector_size": len(prompt_vec),
    })
    return True


def redact_repo_artifacts(root: Path, label: str) -> dict[str, Any]:
    logs = Path(root) / "logs"
    counts = {"intent_touches": 0, "repo_history": 0, "ai_history": 0}
    counts["intent_touches"] = _redact_jsonl(
        logs / "intent_touches.jsonl",
        lambda row: _redact_touch(row, label),
    )
    counts["repo_history"] = _redact_jsonl(
        logs / "repo_fingerprint_history.jsonl",
        lambda row: _redact_repo_summary(row, label),
    )
    counts["ai_history"] = _redact_jsonl(
        logs / "ai_fingerprint_history.jsonl",
        lambda row: _redact_ai_history(row, label),
    )
    fp = logs / f"repo_fingerprint_{label}.json"
    if fp.exists():
        try:
            data = json.loads(fp.read_text(encoding="utf-8", errors="replace"))
            changed = _redact_repo_summary(data, label)
            if changed:
                fp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            pass
    return counts


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _redact_jsonl(path: Path, mutator) -> int:
    if not path.exists():
        return 0
    out: list[str] = []
    changed = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            out.append(line)
            continue
        if mutator(row):
            changed += 1
        out.append(json.dumps(row, ensure_ascii=False))
    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def _redact_touch(row: dict[str, Any], label: str) -> bool:
    files = row.get("files") or []
    if not any(str(f).startswith(f"{label}_") for f in files):
        return False
    row["prompt_preview"] = f"[redacted:{label}]"
    row["privacy"] = "closed"
    return True


def _redact_repo_summary(row: dict[str, Any], label: str) -> bool:
    if row.get("label") != label:
        return False
    if row.get("repo"):
        row["repo"] = repo_ref(label, row["repo"])
    for item in row.get("files") or []:
        if "path" in item:
            item["path_hash"] = path_hash(str(item.pop("path")))
        if "top_terms" in item:
            item["term_hashes"] = hash_terms(item.pop("top_terms"))
    row["privacy"] = "closed"
    return True


def _redact_ai_history(row: dict[str, Any], label: str) -> bool:
    probe = row.get("repo_probe") or {}
    if probe.get("label") != label:
        return False
    if probe.get("repo"):
        probe["repo"] = repo_ref(label, probe["repo"])
    probe["privacy"] = "closed"
    return True
