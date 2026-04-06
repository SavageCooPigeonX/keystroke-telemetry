"""backward_seq007_tokenize_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

from typing import Any
import re

def _tokenize(text: str) -> set[str]:
    """Extract lowercase word tokens from text."""
    raw = re.findall(r"[a-z_]{3,}", text.lower())
    tokens: set[str] = set()
    for tok in raw:
        tokens.add(tok)
        for part in tok.split("_"):
            if len(part) >= 3:
                tokens.add(part)
    return tokens


def _compute_credit(
    node_intel: dict[str, Any], position: int,
    path_length: int, fix_tokens: set[str],
) -> float:
    """Weighted credit attribution for a single node. Returns 0.0–1.0."""
    node_name = node_intel.get("node", "")
    fears = node_intel.get("fears", [])
    node_tokens = _tokenize(f"{node_name} {' '.join(fears)}")
    overlap = (len(fix_tokens & node_tokens) / max(len(fix_tokens), 1)
               if fix_tokens and node_tokens else 0.2)
    position_factor = 1.0 - (position / max(path_length, 1)) * 0.5
    relevance = node_intel.get("relevance", 0.5)
    downstream = min(node_intel.get("dual_score", 0.0) * 1.5, 1.0)
    credit = overlap * 0.35 + position_factor * 0.25 + relevance * 0.25 + downstream * 0.15
    return min(max(credit, 0.0), 1.0)
