"""batch_rewrite_sim_seq001_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import os
import re

def _proposal_token_estimate(root: Path, proposal: dict[str, Any]) -> int:
    rel = str(proposal.get("path") or "")
    tokens = _estimate_file_tokens(root, rel)
    if tokens:
        return tokens
    lines = int((proposal.get("cross_file_validation") or {}).get("line_count") or 0)
    return max(1, lines * 8)


def _estimate_file_tokens(root: Path, rel: str) -> int:
    path = root / str(rel).replace("\\", "/")
    if not path.exists() or not path.is_file():
        return 0
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    return max(1, len(text) // 4)


def _dedupe_strings(values: Any) -> list[str]:
    seen = set()
    out = []
    for value in values or []:
        text = str(value or "").replace("\\", "/").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
