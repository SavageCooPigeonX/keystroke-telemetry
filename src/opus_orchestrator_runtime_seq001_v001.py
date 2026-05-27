"""Claude Opus runtime pack for thought-completer chat."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.hush_intent_runtime_seq001_v001 import build_hush_intent_runtime
from src.opus_artifact_memory_seq001_v001 import build_opus_artifact_memory
from src.opus_coding_area_memory_seq001_v001 import build_opus_coding_area_memory
from src.opus_training_pair_debug_seq001_v001 import debug_training_pairs
from src.session_macro_cycle_seq001_v001 import build_session_macro_cycle

SCHEMA = "opus_orchestrator_runtime/v1"
LATEST = "logs/opus_orchestrator_runtime_latest.json"
HISTORY = "logs/opus_orchestrator_runtime.jsonl"
MARKDOWN = "logs/opus_orchestrator_runtime.md"
MANIFEST_NOTE = "logs/opus_orchestrator_manifest_note.md"


def build_opus_orchestrator_runtime(root: Path, prompt: str = "", *, write: bool = True) -> dict[str, Any]:
    """Assemble the chat surface Claude Opus should see before orchestration."""
    root = Path(root)
    journal = _jsonl_tail(root / "logs" / "prompt_journal.jsonl", 3)
    context = _json(root / "logs" / "dynamic_context_pack.json")
    fsk = _json(root / "logs" / "file_self_knowledge_latest.json")
    sim = _json(root / "logs" / "file_self_sim_learning_latest.json")
    delegates = _json(root / "logs" / "file_deepseek_delegate_latest.json")
    current_prompt = prompt or (journal[-1].get("msg", "") if journal else "")
    artifact = build_opus_artifact_memory(root, current_prompt, write=write)
    coding_memory = build_opus_coding_area_memory(root, current_prompt, write=write)
    training_debug = debug_training_pairs(root, write=write)
    hush = build_hush_intent_runtime(root, current_prompt, write=write)
    macro_cycle = build_session_macro_cycle(root, prompt_limit=5, window_minutes=20, write=write)
    packets = fsk.get("packets") or []
    jobs = delegates.get("jobs") or []
    fence = ((hush.get("repo_classification") or {}).get("mutation_fence")) or "blocked"
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "chat_surface": "thought_completer",
        "operator_prompt": current_prompt,
        "last_three_prompts": [_prompt_row(row) for row in journal],
        "roles": {
            "runtime_authority": "hush",
            "orchestrator": "claude-opus",
            "context_selector": "gemini",
            "file_reasoner": "gemini",
            "file_hands": "deepseek",
            "apply_grader": "claude-opus",
        },
        "gemini_context": {
            "confidence": (context.get("context_selection") or {}).get("confidence"),
            "files": (context.get("context_selection") or {}).get("files") or [],
            "intent_key": ((context.get("prompt_brain") or {}).get("intent") or {}).get("intent_key", ""),
        },
        "hush_intent_runtime": _hush_summary(hush),
        "orchestration_gate": {
            "mutation_fence": fence,
            "source_mutation_allowed": fence == "open",
            "rule": "Hush owns repo-room selection; blocked fences mean plans/artifacts only.",
        },
        "file_subagents": [_agent_from_packet(packet, jobs, fence) for packet in packets[:8]],
        "hush_file_packets": (hush.get("file_packets") or [])[:8],
        "artifact_memory": _artifact_summary(artifact),
        "coding_area_memory": _coding_memory_summary(coding_memory),
        "training_pair_debug": _training_debug_summary(training_debug),
        "session_macro_cycle": _macro_cycle_summary(macro_cycle),
        "manifest_state_write_cycle": _manifest_write_cycle_summary(root),
        "folder_context_coupling": _folder_context_coupling_summary(root),
        "work_completed": _work_completed(delegates, sim),
        "manifest_write": _manifest_write(current_prompt, packets, jobs),
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN, "manifest_note": MANIFEST_NOTE},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_opus_runtime(result), encoding="utf-8")
        (root / MANIFEST_NOTE).write_text(result["manifest_write"]["markdown"], encoding="utf-8")
    return result


def render_opus_runtime(runtime: dict[str, Any]) -> str:
    lines = ["# Opus Orchestrator Runtime", "", f"- prompt: {runtime.get('operator_prompt', '')}"]
    hush = runtime.get("hush_intent_runtime") or {}
    lines.append(f"- Hush repo: `{hush.get('active_repo')}` fence `{hush.get('mutation_fence')}`")
    lines.append(f"- context confidence: `{(runtime.get('gemini_context') or {}).get('confidence')}`")
    lines.extend(["", "## Last 3 Prompts"])
    for row in runtime.get("last_three_prompts") or []:
        lines.append(f"- `{row.get('session_n')}` {row.get('intent')} / {row.get('state')}: {row.get('preview')}")
    lines.extend(["", "## File Subagents"])
    for agent in runtime.get("file_subagents") or []:
        lines.append(f"- `{agent['file']}` {agent['readiness']} via {agent['gemini']} + {agent['deepseek_job']}")
    for packet in runtime.get("hush_file_packets") or []:
        lines.append(f"- Hush `{packet.get('file_identity')}` {packet.get('operator_display_name')} -> {packet.get('current_responsibility')}")
    lines.extend(["", "## Artifact Memory"])
    memory = runtime.get("artifact_memory") or {}
    lines.append(f"- compiler probe: `{memory.get('compiler_status')}`")
    lines.append(f"- training pairs: `{memory.get('training_pair_status')}`")
    for file in memory.get("high_touch_files") or []:
        lines.append(f"- hot: `{file}`")
    lines.extend(["", "## Coding Area Memory"])
    coding = runtime.get("coding_area_memory") or {}
    lines.append(f"- jobs proposed: `{coding.get('job_count')}`")
    for file in coding.get("top_files") or []:
        lines.append(f"- search: `{file}`")
    lines.extend(["", "## Training Pair Debug"])
    debug = runtime.get("training_pair_debug") or {}
    lines.append(f"- status: `{debug.get('status')}`")
    lines.append(f"- recommended: {debug.get('recommended_fix', '')}")
    macro = runtime.get("session_macro_cycle") or {}
    lines.extend(["", "## Session Macro Cycle"])
    lines.append(f"- status: `{macro.get('status')}`")
    lines.append(f"- read: {macro.get('macro_read', '')}")
    for cycle in macro.get("cycles") or []:
        lines.append(f"- `{cycle.get('cycle_id')}` {cycle.get('status')} prompts `{cycle.get('prompt_count')}`")
    manifest_cycle = runtime.get("manifest_state_write_cycle") or {}
    lines.extend(["", "## Manifest State Write Cycle"])
    lines.append(f"- status: `{manifest_cycle.get('status')}`")
    for row in manifest_cycle.get("file_writes") or []:
        lines.append(f"- `{row.get('file')}` -> `{row.get('manifest')}` changed={row.get('changed')}")
    coupling = runtime.get("folder_context_coupling") or {}
    lines.extend(["", "## Folder Context Coupling"])
    lines.append(f"- status: `{coupling.get('status')}`")
    for row in coupling.get("folders") or []:
        lines.append(f"- `{row.get('folder')}` autonomy={row.get('autonomy_score')} resistance={row.get('resistance_score')} mode={row.get('recommended_mode')}")
    lines.extend(["", "## Work Completed"])
    for item in runtime.get("work_completed") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Manifest Write", runtime.get("manifest_write", {}).get("markdown", "")])
    return "\n".join(lines) + "\n"


def _artifact_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    telemetry = artifact.get("telemetry_read") or {}
    return {
        "path": artifact.get("paths", {}).get("latest", "logs/opus_artifact_memory_latest.json"),
        "compiler_status": (artifact.get("compiler_probe") or {}).get("status", ""),
        "training_pair_status": telemetry.get("training_pair_status", ""),
        "high_touch_files": [row.get("file", "") for row in (artifact.get("high_touch_files") or [])[:5]],
        "file_death_areas": [row.get("file", "") for row in (artifact.get("file_death_areas") or [])[:5]],
    }


def _training_debug_summary(debug: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": "logs/opus_training_pair_debug_latest.json",
        "status": debug.get("status", ""),
        "recommended_fix": debug.get("recommended_fix", ""),
        "failed_steps": [row for row in debug.get("multi_step_reasoning", []) if not row.get("ok")],
    }


def _macro_cycle_summary(macro: dict[str, Any]) -> dict[str, Any]:
    cycles = macro.get("cycles") or []
    return {
        "path": "logs/session_macro_cycle_latest.json",
        "status": "needs_audit" if any(row.get("status") != "complete_enough" for row in cycles) else "complete_enough",
        "macro_read": macro.get("macro_read", ""),
        "known_agent_sessions": macro.get("known_agent_sessions") or [],
        "latest_prompt_deleted_words": macro.get("latest_prompt_deleted_words") or [],
        "cycles": [
            {
                "cycle_id": row.get("cycle_id", ""),
                "status": row.get("status", ""),
                "prompt_count": row.get("prompt_count", 0),
                "intent_keys": row.get("intent_keys", [])[:5],
            }
            for row in cycles[:3]
        ],
    }


def _manifest_write_cycle_summary(root: Path) -> dict[str, Any]:
    latest = _json(root / "logs" / "manifest_state_write_latest.json")
    return {
        "path": "logs/manifest_state_write_latest.json",
        "status": latest.get("status", "missing"),
        "file_writes": (latest.get("file_writes") or [])[:8],
        "selected_manifests": (latest.get("selected_manifests") or [])[:8],
        "manifest_syntax_match": ((latest.get("manifest_syntax_match") or {}).get("selected_manifests") or [])[:5],
    }


def _folder_context_coupling_summary(root: Path) -> dict[str, Any]:
    latest = _json(root / "logs" / "folder_context_coupling_latest.json")
    folders = latest.get("folders") or []
    return {
        "path": "logs/folder_context_coupling_latest.json",
        "status": "missing" if not latest else "needs_manifest_manager" if any(row.get("recommended_mode") != "self_managed" for row in folders) else "self_managed",
        "folders": folders[:8],
        "cross_folder_edges": (latest.get("cross_folder_edges") or [])[:8],
        "deepseek_manifest_manager": latest.get("deepseek_manifest_manager") or {},
    }


def _coding_memory_summary(memory: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": "logs/opus_coding_area_memory_latest.json",
        "job_count": len(memory.get("file_jobs") or []),
        "top_files": [row.get("file", "") for row in (memory.get("blocks") or [])[:6]],
        "contract": memory.get("orchestration_contract") or {},
    }


def _hush_summary(hush: dict[str, Any]) -> dict[str, Any]:
    repo = hush.get("repo_classification") or {}
    return {
        "path": "logs/hush_intent_runtime_latest.json",
        "active_repo": repo.get("active_repo", ""),
        "repo_confidence": repo.get("repo_confidence", 0),
        "mutation_fence": repo.get("mutation_fence", "blocked"),
        "intent_moves": [row.get("name", "") for row in hush.get("intent_moves") or []],
        "file_packet_count": len(hush.get("file_packets") or []),
    }


def _agent_from_packet(packet: dict[str, Any], jobs: list[dict[str, Any]], fence: str) -> dict[str, Any]:
    file_path = packet.get("file", "")
    job = next((row for row in jobs if row.get("target_file") == file_path), {})
    scope = packet.get("mutation_scope") or {}
    action = "artifact patch+test, no direct overwrite"
    if fence == "blocked":
        action = "plan/artifact only; Hush mutation fence is blocked"
    return {
        "file": file_path,
        "readiness": scope.get("readiness", ""),
        "gemini": "select context, file goal, neighbors, validation",
        "deepseek_job": job.get("job_id", "not_queued"),
        "allowed_action": action,
        "quote": packet.get("file_quote", ""),
    }


def _manifest_write(prompt: str, packets: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [p.get("file", "") for p in packets if (p.get("mutation_scope") or {}).get("readiness") == "draft_ready"]
    blocked = [p.get("file", "") for p in packets if (p.get("mutation_scope") or {}).get("readiness") == "blocked"]
    md = "\n".join([
        "### Opus Orchestrator Sim",
        f"- prompt: {prompt}",
        f"- ready files: {', '.join(ready[:6]) or 'none'}",
        f"- blocked files: {', '.join(blocked[:4]) or 'none'}",
        f"- delegate jobs: {', '.join(row.get('job_id', '') for row in jobs[:6]) or 'none'}",
        "- rule: Claude Opus may write manifest orchestration notes; source apply still requires grader pass.",
    ])
    return {"targets": ["MANIFEST.md", "src/MANIFEST.md", MANIFEST_NOTE], "markdown": md}


def _work_completed(delegates: dict[str, Any], sim: dict[str, Any]) -> list[str]:
    jobs = delegates.get("jobs") or []
    items = [f"queued {len(jobs)} Gemini+DeepSeek file delegate job(s)"]
    if sim:
        items.append(f"file sim mode {sim.get('mode')} with {(sim.get('backward_learning_pass') or {}).get('status')}")
    return items


def _prompt_row(row: dict[str, Any]) -> dict[str, Any]:
    return {"ts": row.get("ts"), "session_n": row.get("session_n"), "intent": row.get("intent"), "state": row.get("cognitive_state"), "preview": row.get("msg", "")[:180]}


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _jsonl_tail(path: Path, count: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
