"""codex_compat_seq022_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _parse_deleted_words
from .codex_compat_seq001_v001 import _utc_now
from .codex_compat_seq002_v001 import _ensure_repo_on_path
from .codex_compat_seq009_v001 import _inject_dynamic_context_pack
from .codex_compat_seq012_v001 import _write_live_prompt_telemetry
from .codex_compat_seq014_v001 import _write_copilot_live_query_blocks
from .codex_compat_seq015_v001 import _surface_activity
from .codex_compat_seq016_v001 import _log_counts
from .codex_compat_seq018_v001 import enqueue_deepseek_prompt_job
from .codex_compat_seq019_v001 import _build_focus_files
from .codex_compat_seq020_v001 import _build_opus_instruction_layer
from .codex_compat_seq021_v001 import _add_file_sim_focus_files
from .codex_compat_seq023_v001 import _render_dynamic_context_pack
from .codex_compat_seq030_v001 import select_context
from .codex_compat_seq031_v001 import refresh_state
from .codex_compat_seq033_v001 import _load_json
from pathlib import Path
from src._resolve import src_import
from typing import Any
import json
import os
import re

def build_dynamic_context_pack(
    root: Path,
    prompt: str = "",
    deleted_words: list[Any] | None = None,
    surface: str = "codex",
    context_selection: dict[str, Any] | None = None,
    inject: bool = True,
) -> dict[str, Any]:
    """Write the compact context bundle that Codex/Copilot should read next."""
    root = Path(root)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    state = refresh_state(root, "dynamic context pack refreshed")
    latest_prompt = state.get("latest_prompt") or {}
    latest_composition = state.get("latest_composition") or {}
    prompt_text = (
        prompt.strip()
        or str(latest_prompt.get("msg") or "").strip()
        or str(latest_composition.get("final_text") or "").strip()
    )
    parsed_deleted = _parse_deleted_words(
        deleted_words if deleted_words is not None else latest_composition.get("deleted_words", []),
        "",
    )
    if context_selection is None:
        context_selection = (
            select_context(root, prompt_text, parsed_deleted)
            if prompt_text
            else state.get("latest_context_selection") or {}
        )

    intent_resolver = state.get("intent_resolver") or {}
    unresolved = []
    for item in (intent_resolver.get("intents") or [])[:5]:
        unresolved.append({
            "task": item.get("source_key") or item.get("ts"),
            "status": item.get("status"),
            "state": item.get("state"),
            "confidence": item.get("confidence"),
            "text": item.get("reconstructed") or item.get("msg"),
            "deleted_words": item.get("deleted_words", [])[:8],
        })

    signals = {
        "deletion_ratio": latest_composition.get("deletion_ratio", latest_prompt.get("signals", {}).get("deletion_ratio", 0)),
        "intent_deletion_ratio": latest_composition.get(
            "intent_deletion_ratio",
            latest_prompt.get("signals", {}).get("intent_deletion_ratio", 0),
        ),
        "hesitation_count": len(latest_composition.get("hesitation_windows", []))
        if isinstance(latest_composition.get("hesitation_windows"), list)
        else latest_prompt.get("signals", {}).get("hesitation_count", 0),
        "duration_ms": latest_composition.get("duration_ms", latest_prompt.get("signals", {}).get("duration_ms", 0)),
        "cognitive_state": latest_prompt.get("cognitive_state") or latest_composition.get("chat_state", {}).get("state"),
        "deleted_words": parsed_deleted,
    }

    capture_boundaries = {
        "composer": "pre-submit and blocking; pause and submit can inject before handoff",
        "copilot_vscode": "best with VS Code hook/composer; native chat submit needs a wrapper to guarantee pre-send injection",
        "codex_native_chat": "composition can be logged by external watcher, but this API path cannot block the already-sent Codex prompt",
        "screenshot_context": "not wired yet; UIA context switches are available now, screenshot/OCR can be layered next",
    }

    pack = {
        "ts": _utc_now(),
        "surface": surface,
        "prompt": prompt_text,
        "signals": signals,
        "context_selection": context_selection,
        "prompt_brain": _load_json(logs / "prompt_brain_latest.json") or {},
        "file_sim": _load_json(logs / "batch_rewrite_sim_latest.json") or {},
        "intent_loop": _load_json(logs / "intent_loop_latest.json") or {},
        "focus_files": _build_focus_files(context_selection or {}, state, root),
        "unresolved_intents": unresolved,
        "recent_training_pairs": state.get("recent_training_pairs") or [],
        "entropy": state.get("entropy") or {},
        "surface_activity": _surface_activity(root),
        "capture_boundaries": capture_boundaries,
        "log_counts": _log_counts(root),
        "paths": {
            "dynamic_context_pack_json": "logs/dynamic_context_pack.json",
            "dynamic_context_pack_md": "logs/dynamic_context_pack.md",
            "pre_prompt_state": "logs/pre_prompt_state.json",
            "codex_state": "logs/codex_state.json",
            "copilot_instructions": ".github/copilot-instructions.md",
        },
    }
    _add_file_sim_focus_files(pack)
    pack["opus_instruction_layer"] = _build_opus_instruction_layer(
        prompt_text,
        pack.get("focus_files") or [],
        context_selection or {},
        signals,
    )

    try:
        _ensure_repo_on_path(root)
        build_file_self_knowledge = src_import("file_self_knowledge_seq001", "build_file_self_knowledge")
        pack["file_self_knowledge"] = build_file_self_knowledge(
            root,
            files=pack.get("focus_files") or [],
            prompt=prompt_text,
            limit=8,
            write=True,
        )
    except Exception as exc:
        pack["file_self_knowledge"] = {"status": "error", "error": str(exc)}

    pack["deepseek_job"] = enqueue_deepseek_prompt_job(
        root,
        prompt_text,
        context_selection=context_selection,
        context_pack=pack,
        deleted_words=signals.get("deleted_words") or [],
        source=surface,
        priority=3,
    )
    pack["live_prompt_telemetry"] = _write_live_prompt_telemetry(root, pack)
    _write_copilot_live_query_blocks(root, pack, pack["live_prompt_telemetry"])
    try:
        _ensure_repo_on_path(root)
        build_operator_response_policy = src_import("operator_response_policy_seq001", "build_operator_response_policy")
        pack["operator_response_policy"] = build_operator_response_policy(
            root,
            prompt_text,
            surface=surface,
            context_pack=pack,
            inject=inject,
            write=True,
        )
    except Exception as exc:
        pack["operator_response_policy"] = {"status": "error", "error": str(exc)}
    (logs / "dynamic_context_pack.md").write_text(_render_dynamic_context_pack(pack) + "\n", encoding="utf-8")
    pack["injected"] = _inject_dynamic_context_pack(root, pack) if inject else False
    (logs / "dynamic_context_pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    return pack
