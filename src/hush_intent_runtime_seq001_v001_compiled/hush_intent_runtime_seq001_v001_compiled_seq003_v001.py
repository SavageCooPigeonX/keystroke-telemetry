"""hush_intent_runtime_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq004_v001 import _candidate
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import LOCAL_REPO
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import LOCAL_TERMS
from typing import Any
import re

def render_hush_intent_runtime(runtime: dict[str, Any]) -> str:
    repo = runtime.get("repo_classification") or {}
    lines = [
        "# Hush Intent Runtime",
        "",
        f"- active repo: `{repo.get('active_repo')}`",
        f"- confidence: `{repo.get('repo_confidence')}`",
        f"- mutation fence: `{repo.get('mutation_fence')}`",
        f"- reason: {repo.get('reason')}",
        "",
        "## Intent Moves",
    ]
    for move in runtime.get("intent_moves") or []:
        lines.append(f"- `{move.get('intent_key')}` -> {move.get('summary')}")
    lines.extend(["", "## File Packets"])
    for packet in runtime.get("file_packets") or []:
        lines.append(
            f"- `{packet.get('file_identity')}` {packet.get('operator_display_name')}: "
            f"{packet.get('current_responsibility')} [{packet.get('wake_reason')}]"
        )
    lines.extend(["", "## Runtime Authority"])
    auth = runtime.get("runtime_authority") or {}
    lines.append(f"- source mutation allowed: `{auth.get('source_mutation_allowed')}`")
    lines.append(f"- blocked fallback: `{', '.join(auth.get('allowed_when_blocked') or [])}`")
    return "\n".join(lines) + "\n"


def _local_candidate(tokens: set[str], context: dict[str, Any]) -> dict[str, Any]:
    matched = sorted(tokens & LOCAL_TERMS)
    score = len(matched) / 8
    for item in context.get("files") or []:
        name = str(item.get("name") if isinstance(item, dict) else item).lower()
        if name.startswith(("src", "tc_", "file_", "opus_", "pigeon", "numeric")):
            score += 0.08
    return _candidate(LOCAL_REPO, min(score, 1.0), matched, "local telemetry repo")
