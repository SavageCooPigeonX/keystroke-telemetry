"""hush_intent_runtime_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _json
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _tokens
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import MAIF_TERMS
from pathlib import Path
from typing import Any
import json
import re

def _fingerprint_candidates(root: Path, tokens: set[str], context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((root / "logs").glob("repo_fingerprint_*.json")):
        data = _json(path)
        label = str(data.get("label") or path.stem.replace("repo_fingerprint_", ""))
        identity_terms = set()
        for item in data.get("files") or []:
            identity_terms.update(_tokens(str(item.get("identity") or "")))
        domain_terms = set(MAIF_TERMS if label in {"maif_auditor", "linkrouter", "linkrouter_ai"} else [])
        label_terms = set(_tokens(label.replace("_", " ")))
        matched = sorted(tokens & (identity_terms | domain_terms | label_terms))
        score = len(matched) / 7
        for item in context.get("files") or []:
            name = str(item.get("name") if isinstance(item, dict) else item).lower()
            if name.startswith(label):
                score += 0.12
        rows.append(_candidate(label, min(score, 1.0), matched, f"repo fingerprint {path.name}"))
    if not rows and tokens & MAIF_TERMS:
        matched = sorted(tokens & MAIF_TERMS)
        rows.append(_candidate("maif_auditor", min(len(matched) / 7, 1.0), matched, "MAIF domain map"))
    return rows


def _candidate(repo: str, score: float, matched: list[str], source: str) -> dict[str, Any]:
    return {"repo": repo, "score": round(float(score), 4), "matched_terms": matched[:12], "source": source}
