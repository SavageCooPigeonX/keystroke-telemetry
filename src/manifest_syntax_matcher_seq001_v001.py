"""Numeric syntax matching for folder and master manifests."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STOP = {"the", "and", "for", "with", "that", "this", "from", "into", "have", "what", "when", "they"}


def match_manifest_syntax(
    root: Path,
    text: str,
    *,
    limit: int = 8,
    candidate_manifests: list[str] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Select manifests by folder/module/system syntax plus numeric bins."""
    root = Path(root)
    query = _tokens(text)
    profiles = _manifest_profiles(root, candidate_manifests)
    rows = []
    for profile in profiles:
        tokens = set(profile.get("tokens") or [])
        overlap = sorted(tokens & set(query))
        if not overlap:
            continue
        score = len(overlap) * 1.0
        score += len(set(overlap) & set(profile.get("folder_tokens") or [])) * 0.7
        score += len(set(overlap) & set(profile.get("system_tokens") or [])) * 1.2
        rows.append({
            "manifest": profile["manifest"],
            "folder": profile["folder"],
            "score": round(score, 4),
            "matched_tokens": overlap[:16],
            "numeric": _numeric(overlap),
            "profile_numeric": profile["numeric"],
            "classification": profile["classification"],
        })
    rows.sort(key=lambda row: row["score"], reverse=True)
    result = {
        "schema": "manifest_syntax_match/v1",
        "ts": _now(),
        "query_numeric": _numeric(query),
        "selected_manifests": rows[: max(1, int(limit or 8))],
        "profile_count": len(profiles),
        "read": "manifests self-select by folder path, heading text, file/module words, and recurring operator syntax",
    }
    if write:
        _write_json(root / "logs" / "manifest_syntax_match_latest.json", result)
        _append_jsonl(root / "logs" / "manifest_syntax_match.jsonl", result)
    return result


def _manifest_profiles(root: Path, candidates: list[str] | None = None) -> list[dict[str, Any]]:
    profiles = []
    paths = [root / rel for rel in candidates] if candidates else list(root.rglob("MANIFEST.md"))
    for path in paths:
        if ".git" in path.parts:
            continue
        if not path.exists() or path.name != "MANIFEST.md":
            continue
        rel = path.relative_to(root).as_posix()
        folder = "." if path.parent == root else path.parent.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")[:24000]
        folder_tokens = _tokens(folder)
        heading_tokens = _tokens("\n".join(line for line in text.splitlines()[:80] if line.startswith(("#", "|", "-"))))
        system_tokens = _classification_tokens(folder, text)
        tokens = sorted(set([*folder_tokens, *heading_tokens, *system_tokens]))
        profiles.append({
            "manifest": rel,
            "folder": folder,
            "classification": _classification(folder, text),
            "folder_tokens": folder_tokens,
            "system_tokens": system_tokens,
            "tokens": tokens[:500],
            "numeric": _numeric(tokens),
        })
    return profiles


def _classification(folder: str, text: str) -> str:
    low = f"{folder}\n{text[:4000]}".lower()
    if "test" in low:
        return "test_validation"
    if "manifest" in low or "compiler" in low:
        return "manifest_compiler"
    if "context" in low or "prompt" in low:
        return "prompt_context"
    if "sim" in low or "orchestr" in low:
        return "simulation_orchestration"
    if "ui" in low or "jsx" in low or "css" in low:
        return "frontend_ui"
    return "code_module"


def _classification_tokens(folder: str, text: str) -> list[str]:
    return _tokens(" ".join([folder, _classification(folder, text)]))


def _tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z0-9]+", str(text).replace("_", " ").lower())
    return [tok for tok in raw if len(tok) > 2 and tok not in STOP]


def _numeric(tokens: list[str]) -> dict[str, Any]:
    bins = [0] * 16
    for tok in tokens:
        bins[int(hashlib.sha256(tok.encode("utf-8")).hexdigest()[:2], 16) % len(bins)] += 1
    return {"bins": bins, "token_count": len(tokens)}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["match_manifest_syntax"]
