"""Repo plug-in encoder for the operator AI fingerprint.

Feeds an external repository into keystroke telemetry by turning each file into
prompt-like training text, binding that text to stable repo file identities,
and refreshing an operator fingerprint snapshot from local prompt/profile logs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ai_fingerprint_operator_seq001_v001 import build_operator_fingerprint
from src.ai_fingerprint_privacy_seq001_v001 import (
    hash_terms,
    path_hash,
    private_record_touch,
    redact_repo_artifacts,
    repo_ref,
)

TEXT_EXTS = {".py", ".md", ".txt", ".toml", ".json", ".yml", ".yaml"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", text)]


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


def _load_numeric(root: Path) -> Any | None:
    matches = sorted((root / "src").glob("intent_numeric_seq001*.py"), key=lambda p: p.name)
    for path in matches:
        spec = importlib.util.spec_from_file_location("ai_fingerprint_numeric", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.ROOT = root
            module.VOCAB_PATH = root / "logs" / "intent_vocab.json"
            module.MATRIX_PATH = root / "logs" / "intent_matrix.json"
            module.TOUCH_LOG_PATH = root / "logs" / "intent_touches.jsonl"
            return module
    return None


def _iter_repo_files(repo: Path, limit: int) -> list[Path]:
    out: list[Path] = []
    for path in sorted(repo.rglob("*")):
        if len(out) >= limit:
            break
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        out.append(path)
    return out


def _file_identity(label: str, rel: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9]+", "_", f"{label}_{Path(rel).with_suffix('')}".lower())
    return re.sub(r"_+", "_", raw).strip("_")


def _file_prompt(repo: Path, path: Path, label: str) -> dict[str, Any]:
    rel = path.relative_to(repo).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")[:12000]
    headings = " ".join(line.strip("# ").strip() for line in text.splitlines() if line.lstrip().startswith("#"))[:1200]
    defs = " ".join(re.findall(r"^\s*(?:class|def)\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.M))[:1200]
    prompt = " ".join([label, rel, headings, defs, text[:2500]])
    counts = Counter(_tokens(prompt))
    return {
        "path": rel,
        "identity": _file_identity(label, rel),
        "bytes": path.stat().st_size,
        "prompt": prompt,
        "top_terms": counts.most_common(16),
        "signature": _signature([label, rel, *[term for term, _ in counts.most_common(20)]]),
    }


def _safe_file_record(item: dict[str, Any], privacy: str) -> dict[str, Any]:
    if privacy == "open":
        return {k: item[k] for k in ("path", "identity", "bytes", "top_terms", "signature")}
    return {
        "identity": item["identity"],
        "bytes": item["bytes"],
        "path_hash": path_hash(item["path"]),
        "term_hashes": hash_terms(item["top_terms"]),
        "signature": item["signature"],
    }


def plug_repo(
    root: Path,
    repo: Path,
    label: str,
    limit: int = 120,
    train: bool = True,
    privacy: str = "closed",
) -> dict[str, Any]:
    root, repo = Path(root).resolve(), Path(repo).resolve()
    numeric = _load_numeric(root) if train else None
    redacted = redact_repo_artifacts(root, label) if privacy != "open" else {}
    files = [_file_prompt(repo, p, label) for p in _iter_repo_files(repo, limit)]
    trained = 0
    for item in files:
        if numeric is not None:
            if privacy == "open":
                numeric.record_touch(item["prompt"], [item["identity"]], learning_rate=0.18)
                trained += 1
            elif private_record_touch(root, numeric, item["prompt"], [item["identity"]]):
                trained += 1
    summary = {
        "schema": "repo_fingerprint/v1",
        "ts": _utc_now(),
        "label": label,
        "privacy": privacy,
        "repo": str(repo) if privacy == "open" else repo_ref(label, repo),
        "files_indexed": len(files),
        "trained_touches": trained,
        "redacted_previous": redacted,
        "files": [_safe_file_record(item, privacy) for item in files],
        "numeric_stats": numeric.get_stats() if numeric is not None else {},
    }
    logs = root / "logs"
    _write_json(logs / f"repo_fingerprint_{label}.json", summary)
    _append_jsonl(logs / "repo_fingerprint_history.jsonl", summary)
    probe = {k: summary[k] for k in ("schema", "ts", "label", "privacy", "repo", "files_indexed", "trained_touches", "numeric_stats")}
    summary["ai_fingerprint"] = build_operator_fingerprint(root, probe)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--label", default="")
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--privacy", choices=["closed", "open"], default="closed")
    parser.add_argument("--no-train", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo)
    label = args.label or re.sub(r"[^a-zA-Z0-9]+", "_", repo.name.lower()).strip("_")
    print(json.dumps(plug_repo(Path(args.root), repo, label, args.limit, train=not args.no_train, privacy=args.privacy), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
