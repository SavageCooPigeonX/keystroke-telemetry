"""file_self_sim_learning_seq001_seq033_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import re

def _wake_role(index: int, rel: str, proposal: dict[str, Any], neighbors: list[str], tests: list[str]) -> str:
    if index == 0:
        return "top_waker"
    if rel.lower().endswith("manifest.md"):
        return "manifest_anchor"
    if Path(rel).name.startswith("test_") or "/test" in rel:
        return "validator"
    ten_q = proposal.get("ten_q") or {}
    if ten_q and not ten_q.get("passed", True):
        return "blocker"
    if tests:
        return "diagnoser"
    if neighbors:
        return "peer_context"
    return "learner"


def _next_question(role: str, learned: dict[str, Any], neighbors: list[str], tests: list[str]) -> str:
    if role == "top_waker":
        return "Which peer must wake next before I draft a rewrite?"
    if not tests:
        return "Which validation gate proves my rewrite survived?"
    if not learned.get("enough_for_self_rewrite"):
        return "What memory or history do I need before self-overwrite eligibility?"
    if neighbors:
        return f"Does {Path(neighbors[0]).name} conflict with my planned change?"
    return "Can I emit a bounded DeepSeek rewrite packet after approval?"


def _default_validation(root: Path, rel: str, tests: list[str]) -> list[str]:
    path = root / rel
    plan = []
    if path.suffix == ".py":
        plan.append(f"py -m py_compile {rel}")
    plan.extend(f"py -m pytest {test} -q" for test in tests[:3])
    if not plan:
        plan.append("git diff --check")
    return plan
