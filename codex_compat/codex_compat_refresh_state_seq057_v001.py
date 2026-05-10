"""codex_compat_refresh_state_seq057_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_git_status_seq011_v001 import _git_status
from .codex_compat_load_json_seq059_v001 import _load_json
from .codex_compat_load_jsonl_tail_seq007_v001 import _load_jsonl_tail
from .codex_compat_refresh_entropy_seq012_v001 import _refresh_entropy
from .codex_compat_render_state_markdown_seq058_v001 import _render_state_markdown
from .codex_compat_utc_now_seq001_v001 import _utc_now
from pathlib import Path
from typing import Any
import json
import os
import re

def refresh_state(root: Path, note: str = "") -> dict[str, Any]:
    """Write browseable Codex loop state for humans and automation."""
    root = Path(root)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    prompts = _load_jsonl_tail(logs / "prompt_journal.jsonl", max_lines=5)
    responses = _load_jsonl_tail(logs / "ai_responses.jsonl", max_lines=5)
    edits = _load_jsonl_tail(logs / "edit_pairs.jsonl", max_lines=12)
    pairs = _load_jsonl_tail(logs / "training_pairs.jsonl", max_lines=5)
    compositions = _load_jsonl_tail(logs / "chat_compositions.jsonl", max_lines=5)
    context_history = _load_jsonl_tail(logs / "context_selection_history.jsonl", max_lines=5)
    numeric_training = _load_jsonl_tail(logs / "numeric_training_history.jsonl", max_lines=5)
    intent_resolver = _load_json(root / "logs" / "codex_intent_resolver.json") or {}
    entropy = _refresh_entropy(root)

    state = {
        "ts": _utc_now(),
        "status": "active",
        "note": note,
        "latest_prompt": prompts[-1] if prompts else None,
        "latest_response": responses[-1] if responses else None,
        "recent_edits": edits,
        "recent_training_pairs": pairs,
        "latest_composition": compositions[-1] if compositions else None,
        "latest_context_selection": context_history[-1] if context_history else None,
        "latest_numeric_training": numeric_training[-1] if numeric_training else None,
        "intent_resolver": intent_resolver,
        "git_status": _git_status(root),
        "entropy": entropy,
        "paths": {
            "human_state": "logs/codex_state.md",
            "machine_state": "logs/codex_state.json",
            "entropy_block": "logs/codex_entropy_block.md",
            "prompt_journal": "logs/prompt_journal.jsonl",
            "edit_pairs": "logs/edit_pairs.jsonl",
            "training_pairs": "logs/training_pairs.jsonl",
            "chat_compositions": "logs/chat_compositions.jsonl",
            "context_selection": "logs/context_selection.json",
            "context_selection_history": "logs/context_selection_history.jsonl",
            "numeric_training_history": "logs/numeric_training_history.jsonl",
            "pre_prompt_state": "logs/pre_prompt_state.json",
            "dynamic_context_pack": "logs/dynamic_context_pack.json",
            "deepseek_prompt_jobs": "logs/deepseek_prompt_jobs.jsonl",
            "deepseek_prompt_results": "logs/deepseek_prompt_results.jsonl",
            "intent_resolver": "logs/codex_intent_resolver.json",
        },
    }

    (logs / "codex_state.json").write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    (logs / "codex_state.md").write_text(_render_state_markdown(state), encoding="utf-8")
    return state
