"""batch_rewrite_sim_seq001_seq033_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq034_v001 import STOP
from pathlib import Path
from typing import Any
import os
import re

def _choose_scope_from_manifests(root: Path, tokens: set[str]) -> dict[str, Any]:
    best = {"scope": "root", "manifest_path": "", "confidence": 0.0}
    src_best: dict[str, Any] | None = None
    if not tokens:
        return best
    for path in sorted(root.rglob("MANIFEST.md"))[:500]:
        try:
            rel = path.relative_to(root).as_posix()
            parent = path.parent.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8", errors="ignore")[:2500]
        except Exception:
            continue
        hay = _tokens(" ".join([rel, parent, text]))
        score = len(tokens & hay) / max(len(tokens), 1)
        if score > best["confidence"]:
            best = {
                "scope": "root" if parent == "." else parent,
                "manifest_path": rel,
                "confidence": round(score, 4),
            }
        if parent == "src" and (src_best is None or score > src_best["confidence"]):
            src_best = {"scope": "src", "manifest_path": rel, "confidence": round(score, 4)}
    coding_tokens = {"intent", "orchestrator", "context", "injection", "validation", "compile", "fixes", "file"}
    if src_best and tokens & coding_tokens and best["confidence"] - src_best["confidence"] <= 0.12:
        return src_best
    return best


def _stem_key(value: str) -> str:
    stem = Path(value).stem.lower()
    stem = re.sub(r"_s\d{3,4}_v\d{3,4}_.*$", "", stem)
    stem = re.sub(r"_seq\d+.*$", "", stem)
    return re.sub(r"[^a-z0-9_]+", "_", stem).strip("_")


def _tokens(text: str) -> set[str]:
    return set(_token_list(text))


def _token_list(text: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z][a-zA-Z0-9]+", str(text).lower().replace("_", " "))
    out = []
    for token in raw:
        clean = re.sub(r"_+", "_", token).strip("_")
        if len(clean) > 2 and clean not in STOP and clean not in out:
            out.append(clean)
    return out
