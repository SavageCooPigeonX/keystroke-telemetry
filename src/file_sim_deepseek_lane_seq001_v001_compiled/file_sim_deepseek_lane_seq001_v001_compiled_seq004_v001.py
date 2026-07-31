"""file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001 import _json
from pathlib import Path
from typing import Any
import json
import os

def _prompt(sim: dict[str, Any], action: dict[str, Any]) -> str:
    intent = sim.get("intent") or {}
    hush_note = ""
    if action.get("mode") == "hush_mutation_fence_plan_only":
        hush_note = "HUSH_FENCE: Mutation is blocked. Return a repo-lock/context plan only."
    return "\n".join([
        "You are DeepSeek running perpendicular to Copilot inside the file-sim loop.",
        "Your job is continuous safe maintenance: compress, split-plan, map validation, or simulate an alternate codebase state.",
        hush_note,
        "",
        f"INTENT_KEY: {intent.get('intent_key', '')}",
        f"TARGET_FILE: {action.get('target_file')}",
        f"MODE: {action.get('mode')}",
        f"BOUNDED_ACTION: {action.get('bounded_action')}",
        "",
        "CONTRACT:",
        "1. Return a concrete plan or surgical proposal artifact.",
        "2. Do not apply source changes.",
        "3. Name the exact context window and validation gates.",
        "4. Explain what backward learning should be stored in the folder manifest.",
        "5. Include an alternate-state simulation: what this file would look like after the rewrite, and what could break.",
    ])


def _highest_pressure(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(jobs, key=lambda row: (float(row.get("split_pressure") or 0), int(row.get("line_count") or 0)), reverse=True)[0]


def _dedupe(items: Any) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item))


def _hush_runtime(root: Path, sim: dict[str, Any]) -> dict[str, Any]:
    if isinstance(sim.get("hush_intent_runtime"), dict):
        return sim["hush_intent_runtime"]
    return _json(root / "logs" / "hush_intent_runtime_latest.json")


def _hush_blocks_mutation(hush: dict[str, Any] | None) -> bool:
    if not hush:
        return False
    repo = hush.get("repo_classification") or {}
    return repo.get("mutation_fence") == "blocked"


def _hush_summary(hush: dict[str, Any] | None) -> dict[str, Any]:
    repo = (hush or {}).get("repo_classification") or {}
    return {
        "active_repo": repo.get("active_repo", ""),
        "repo_confidence": repo.get("repo_confidence", 0),
        "mutation_fence": repo.get("mutation_fence", ""),
        "reason": repo.get("reason", ""),
    }
