"""batch_rewrite_sim_seq001_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq014_v001 import _fallback_prompt_sim_targets
from .batch_rewrite_sim_seq001_seq015_v001 import _proposal
from .batch_rewrite_sim_seq001_seq026_v001 import _add_candidate
from .batch_rewrite_sim_seq001_seq026_v001 import _seed_paths
from .batch_rewrite_sim_seq001_seq027_v001 import _add_candidate_with_aliases
from .batch_rewrite_sim_seq001_seq027_v001 import _candidate_sort_score
from .batch_rewrite_sim_seq001_seq027_v001 import _history_points
from .batch_rewrite_sim_seq001_seq028_v001 import _resolve_alias_targets
from .batch_rewrite_sim_seq001_seq028_v001 import _source_candidate
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import os
import re

def _rank_candidates(
    root: Path,
    compiled: dict[str, Any],
    history: list[dict[str, Any]],
    dead_summary: dict[str, Any],
    failure: dict[str, Any],
    dirty: set[str],
    limit: int,
    config: dict[str, Any],
    context_selection: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    bucket: dict[str, dict[str, Any]] = defaultdict(lambda: {"score": 0.0, "events": Counter(), "evidence": []})
    tokens = set(compiled.get("tokens") or [])
    scope = str(compiled.get("scope") or "")

    for path, points, reason in _seed_paths(root, compiled, dead_summary, context_selection):
        _add_candidate_with_aliases(root, bucket, path, points, reason)
    for pair in history:
        path = pair.get("new_path") or pair.get("old_path") or ""
        points = _history_points(pair, tokens, scope)
        if path and points > 0:
            for resolved in _resolve_alias_targets(root, path) or [str(path).replace("\\", "/")]:
                row = bucket[resolved]
                row["score"] += points
                row["events"][str(pair.get("event_type") or "touch")] += 1
                if resolved != str(path).replace("\\", "/"):
                    row["evidence"].append(f"identity_alias:{path}")
                if len(row["evidence"]) < 5:
                    row["evidence"].append(str(pair.get("subject") or pair.get("prompt") or "")[:140])
    if not bucket:
        for path, points, reason in _fallback_prompt_sim_targets(root):
            _add_candidate(bucket, path, points, reason)

    ranked_all = sorted(
        bucket.items(),
        key=lambda kv: _candidate_sort_score(root, kv[0], kv[1], set(compiled.get("tokens") or [])),
        reverse=True,
    )
    ranked_source = [(p, d) for p, d in ranked_all if _source_candidate(p)]
    ranked_other = [(p, d) for p, d in ranked_all if not _source_candidate(p)]
    ranked = ranked_source + ranked_other
    proposals = []
    source_only = bool(config.get("source_only", True))
    min_interlink = float(config.get("min_interlink_score") or 0)
    for path, data in ranked[: max(limit * 3, limit)]:
        proposal = _proposal(root, path, data, compiled, failure, dirty, config)
        if source_only and proposal["rewrite_target_type"] != "source":
            continue
        if proposal["interlink_score"] < min_interlink:
            continue
        proposals.append(proposal)
        if len(proposals) >= limit:
            break
    return proposals
