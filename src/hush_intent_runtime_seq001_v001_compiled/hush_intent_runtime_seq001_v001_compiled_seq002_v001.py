"""hush_intent_runtime_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq001_v001 import classify_active_repo
from .hush_intent_runtime_seq001_v001_compiled_seq003_v001 import render_hush_intent_runtime
from .hush_intent_runtime_seq001_v001_compiled_seq005_v001 import _intent_moves
from .hush_intent_runtime_seq001_v001_compiled_seq006_v001 import _file_packets
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _intent_map
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _json
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _recent_outcome
from .hush_intent_runtime_seq001_v001_compiled_seq009_v001 import _repo_room_context
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import HISTORY
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import LATEST
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import MARKDOWN
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import SCHEMA
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import _append_jsonl
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import _jsonl_tail
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import _now
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import re

def build_hush_intent_runtime(root: Path, prompt: str = "", *, write: bool = True) -> dict[str, Any]:
    """Build the persistent Hush intent-map packet for orchestration."""
    root = Path(root)
    journal = _jsonl_tail(root / "logs" / "prompt_journal.jsonl", 8)
    latest_prompt = journal[-1] if journal else {}
    current_prompt = str(prompt or latest_prompt.get("msg") or "")
    deleted = list(latest_prompt.get("deleted_words") or [])
    context_pack = _json(root / "logs" / "dynamic_context_pack.json")
    context_selection = context_pack.get("context_selection") if isinstance(context_pack.get("context_selection"), dict) else {}
    repo = classify_active_repo(root, current_prompt, deleted, context_selection)
    semantic = _json(root / "logs" / "semantic_profile_latest.json")
    intent_graph = _json(root / "logs" / "intent_graph_latest.json")
    sim = _json(root / "logs" / "file_self_sim_learning_latest.json")
    outcome = _json(root / "logs" / "codex_edit_outcome_latest.json")
    intent_moves = _intent_moves(current_prompt, intent_graph)
    packets = _file_packets(root, repo, sim, current_prompt)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "name": "Hush",
        "role": "persistent_intent_reconstruction_agent",
        "operator_prompt": current_prompt,
        "deleted_words": deleted,
        "repo_classification": repo,
        "intent_map": _intent_map(journal, semantic, intent_moves),
        "intent_moves": intent_moves,
        "file_packets": packets,
        "workflow": [
            "operator signal",
            "Hush intent map",
            "active repo",
            "intent moves",
            "wake order",
            "file packets",
            "sim/delegate jobs",
            "validation gate",
            "memory update",
        ],
        "runtime_authority": {
            "mutation_fence": repo["mutation_fence"],
            "allowed_when_blocked": ["read", "plan", "artifact_only", "ask_for_repo_lock"],
            "source_mutation_allowed": repo["mutation_fence"] == "open",
        },
        "repo_room_context": _repo_room_context(root, repo),
        "recent_outcome": _recent_outcome(outcome),
        "whisper_irt": {
            "status": "modeled_future_layer",
            "capability": "live field intent whispering is memory-hooked here, not deployed in v1",
        },
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_hush_intent_runtime(result), encoding="utf-8")
    return result
