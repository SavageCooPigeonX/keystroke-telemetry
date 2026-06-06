"""file_self_sim_learning_seq001_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq034_v001 import _context_pack_files
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import re

def _interlink_plan(
    root: Path,
    wake_order: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    intent_model: dict[str, Any],
    settings: dict[str, Any],
    split_jobs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifests: dict[str, list[str]] = defaultdict(list)
    for node in wake_order:
        manifest = node.get("manifest") or "root"
        manifests[manifest].append(node["file"])
    missing_tests = [
        node["file"] for node in wake_order
        if node["file"].endswith(".py") and not node.get("tests")
    ]
    return {
        "goal": settings["target_state"],
        "intent_key": intent_model.get("intent_key", ""),
        "manifest_chains": [
            {"manifest": manifest, "files": files[:12], "action": "keep responsibilities explicit before rewrite"}
            for manifest, files in sorted(manifests.items())
        ],
        "near_term_jobs": [
            {
                "job": "build_learning_profiles",
                "files": [packet["file"] for packet in packets[:6]],
                "action": "accumulate enough profile, memory, and test evidence before self-overwrite",
            },
            {
                "job": "close_validation_gaps",
                "files": missing_tests[:8],
                "action": "add or map compile/test gates before autonomous patch eligibility",
            },
            {
                "job": "prepare_deepseek_context_pack",
                "files": _context_pack_files(root, wake_order),
                "action": "load top waker, manifest, tests, and highest-friction peers",
            },
            {
                "job": "draft_overcap_split_plans",
                "files": [job.get("file") for job in (split_jobs or [])[:8]],
                "action": "ask DeepSeek for split plans only; keep source writes approval-gated",
            },
        ],
        "overwrite_gate": {
            "allowed_now": False,
            "future_requirements": [
                "operator approval",
                "DeepSeek packet generated",
                "context veins fulfilled",
                "10Q/validation packet passed",
                "compile/test result recorded through backward learning",
            ],
        },
    }
