"""codex_compat_build_dynamic_context_pack_seq042_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 042 | VER: v002 | 161 lines | ~2,221 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_add_file_sim_focus_files_seq041_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _add_file_sim_focus_files
from .codex_compat_build_focus_files_seq039_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _build_focus_files
from .codex_compat_build_opus_instruction_layer_seq040_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _build_opus_instruction_layer
from .codex_compat_enqueue_deepseek_prompt_job_seq038_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import enqueue_deepseek_prompt_job
from .codex_compat_ensure_repo_on_path_seq009_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _ensure_repo_on_path
from .codex_compat_inject_dynamic_context_pack_seq023_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _inject_dynamic_context_pack
from .codex_compat_load_json_seq059_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_json
from .codex_compat_log_counts_seq033_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _log_counts
from .codex_compat_parse_deleted_words_seq003_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _parse_deleted_words
from .codex_compat_refresh_state_seq057_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import refresh_state
from .codex_compat_render_dynamic_context_pack_seq043_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _render_dynamic_context_pack
from .codex_compat_select_context_seq056_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import select_context
from .codex_compat_surface_activity_seq032_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _surface_activity
from .codex_compat_utc_now_seq001_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _utc_now
from .codex_compat_write_copilot_live_query_blocks_seq031_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _write_copilot_live_query_blocks
from .codex_compat_write_live_prompt_telemetry_seq028_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _write_live_prompt_telemetry
from pathlib import Path
from typing import Any
import json
import os
import re
from src._resolve import src_import

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
    hush = _build_hush_runtime(root, prompt_text, parsed_deleted, context_selection)

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
        "hush": hush,
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

    if _hush_requests_artifact_only(hush):
        pack["deepseek_job"] = {
            "status": "skipped",
            "mode": "artifact_only",
            "reason": "hush_creative_artifact_only",
        }
    else:
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
    _ensure_operator_policy_file_comments(root, pack)
    (logs / "dynamic_context_pack.md").write_text(_render_dynamic_context_pack(pack) + "\n", encoding="utf-8")
    pack["injected"] = _inject_dynamic_context_pack(root, pack) if inject else False
    (logs / "dynamic_context_pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    return pack


def _ensure_operator_policy_file_comments(root: Path, pack: dict[str, Any]) -> None:
    policy = pack.setdefault("operator_response_policy", {})
    if not isinstance(policy, dict):
        policy = {}
        pack["operator_response_policy"] = policy
    if policy.get("file_comments"):
        policy.setdefault("deepseek_response_policy_audit", _response_policy_audit(True, "existing file comments"))
        return
    comments = []
    for item in (pack.get("focus_files") or [])[:8]:
        if not isinstance(item, dict):
            continue
        rel = str(item.get("name") or "").strip()
        if not rel:
            continue
        selected_by = "file_sim" if item.get("reason") == "file_sim_proposal" else str(item.get("reason") or "context")
        file_says = _file_says(root, rel)
        learning = {
            "schema": "file_solution_backward_pass/v1",
            "path": rel,
            "selected_by": selected_by,
            "pattern_tokens": _tokens(" ".join([pack.get("prompt", ""), rel, file_says]))[:16],
        }
        comments.append({
            "schema": "operator_response_file_comment/v1",
            "file": rel,
            "selected_by": selected_by,
            "file_signal": f"{selected_by.replace('_', '-')} selected me for this prompt; preserve the proof path.",
            "file_says": file_says,
            "file_fix_proposal": f"I think the fix is: inspect `{rel}`, apply one bounded mutation, and verify the named test/compile gate.",
            "fix_grade": {
                "schema": "file_fix_grader/v1",
                "score": 0.74 if selected_by == "file_sim" else 0.62,
                "decision": "safe_dry_run",
                "reason": "file comment synthesized from focus-file selection",
            },
            "backward_pass_learning": learning,
        })
        _append_jsonl(root / "logs" / "file_solution_backward_pass.jsonl", learning)
    if comments:
        policy["file_comments"] = comments
        policy["deepseek_response_policy_audit"] = _response_policy_audit(True, "file comments synthesized from focus files")


def _build_hush_runtime(
    root: Path,
    prompt: str,
    deleted_words: list[str],
    context_selection: dict[str, Any],
) -> dict[str, Any]:
    if not prompt:
        return {}
    try:
        _ensure_repo_on_path(root)
        build_hush_intent_runtime = src_import("hush_intent_runtime_seq001", "build_hush_intent_runtime")
        return build_hush_intent_runtime(
            root,
            prompt,
            write=True,
            deleted_words=deleted_words,
            context_selection=context_selection,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _hush_requests_artifact_only(hush: dict[str, Any]) -> bool:
    if not isinstance(hush, dict):
        return False
    authority = hush.get("runtime_authority") if isinstance(hush.get("runtime_authority"), dict) else {}
    if authority.get("mode") == "creative_artifact_only":
        return True
    move_names = {str(move.get("name") or "") for move in (hush.get("intent_moves") or []) if isinstance(move, dict)}
    return "creative_artifact_only" in move_names


def _file_says(root: Path, rel: str) -> str:
    path = root / rel
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return f"{rel} was selected by context routing."
    doc = re.search(r'"""(.*?)"""', text, re.S)
    if doc:
        return re.sub(r"\s+", " ", doc.group(1)).strip()[:220]
    first = next((line.strip("# ").strip() for line in text.splitlines() if line.strip()), "")
    return first[:220] or f"{rel} was selected by context routing."


def _response_policy_audit(should_make: bool, reason: str) -> dict[str, Any]:
    return {
        "schema": "deepseek_response_policy_audit/v1",
        "should_make_response_policy": should_make,
        "reason": reason,
    }


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(text).lower()) if len(token) >= 3]


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
