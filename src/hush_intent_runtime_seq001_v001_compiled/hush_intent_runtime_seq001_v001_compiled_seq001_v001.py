"""hush_intent_runtime_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq003_v001 import _local_candidate
from .hush_intent_runtime_seq001_v001_compiled_seq004_v001 import _candidate
from .hush_intent_runtime_seq001_v001_compiled_seq004_v001 import _fingerprint_candidates
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _tokens
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import CROSS_REPO_MARGIN
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import LOW_CONFIDENCE
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import _now
from pathlib import Path
from typing import Any
import re

def classify_active_repo(
    root: Path,
    prompt: str,
    deleted_words: list[str] | None = None,
    context_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify the active repo before any mutation-capable routing."""
    root = Path(root)
    tokens = set(_tokens(" ".join([prompt or "", *(deleted_words or [])])))
    candidates = [_local_candidate(tokens, context_selection or {})]
    candidates.extend(_fingerprint_candidates(root, tokens, context_selection or {}))
    candidates = sorted(candidates, key=lambda row: (-row["score"], row["repo"]))
    top = candidates[0] if candidates else _candidate("unknown", 0, [], "none")
    second = candidates[1] if len(candidates) > 1 else _candidate("none", 0, [], "none")
    confidence = round(float(top.get("score") or 0), 4)
    cross_repo = second["score"] >= LOW_CONFIDENCE and (confidence - second["score"]) <= CROSS_REPO_MARGIN
    low = confidence < LOW_CONFIDENCE
    active_repo = "ambiguous" if cross_repo or low else top["repo"]
    fence = "blocked" if active_repo == "ambiguous" else "open"
    if low:
        reason = "repo confidence below mutation threshold"
    elif cross_repo:
        reason = "multiple repo rooms are plausible; mutation requires an explicit repo lock"
    else:
        reason = f"{top['repo']} matched {', '.join(top.get('matched_terms') or ['repo signals'])}"
    return {
        "schema": "hush_repo_classification/v1",
        "ts": _now(),
        "active_repo": active_repo,
        "repo_confidence": confidence,
        "repo_candidates": candidates[:5],
        "mutation_fence": fence,
        "reason": reason,
    }
