"""Copilot probe push-cycle packets for DeepSeek/compiler handoff.

This is the per-prompt control packet: Copilot/Codex probes operator intent,
files wake through graph edges, and DeepSeek receives a bounded compiler job.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "copilot_probe_push_cycle/v1"


def build_copilot_probe_push_cycle(
    root: Path,
    prompt: str,
    deleted_words: list[str] | None = None,
    *,
    context_pack: dict[str, Any] | None = None,
    context_selection: dict[str, Any] | None = None,
    focus_files: list[dict[str, Any]] | None = None,
    source: str = "codex",
    write: bool = True,
) -> dict[str, Any]:
    """Build the durable packet for one prompt -> sim -> compiler cycle."""
    root = Path(root)
    prompt = str(prompt or "").strip()
    deleted = [str(word) for word in (deleted_words or []) if str(word).strip()]
    context_selection = context_selection or (context_pack or {}).get("context_selection") or {}
    base_focus = _collect_focus_files(context_selection, context_pack or {}, focus_files or [])

    intent_graph = _build_intent_graph(root, prompt, deleted, context_selection)
    intent_moves = _intent_moves(intent_graph)
    for move in intent_moves:
        for file_name in move.get("files") or []:
            base_focus.append({"name": file_name, "reason": "intent_graph", "score": move.get("confidence", 0.0)})

    waking_files = _expand_waking_files(root, base_focus, prompt, deleted, write=write)
    graph = _build_file_graph(root, prompt, deleted, waking_files, write=write)
    cycle_id = _cycle_id(prompt, deleted, intent_moves, waking_files, source)
    now = _now()

    packet: dict[str, Any] = {
        "schema": SCHEMA,
        "ts": now,
        "cycle_id": cycle_id,
        "source": source,
        "operator_prompt": prompt,
        "deleted_words": deleted,
        "operator_probe": {
            "role": "codex_copilot_operator_probe",
            "read": _operator_read(prompt, intent_moves, deleted),
            "probe_goal": "extract intent pressure, wake the right files, and hand the mutation to the compiler",
            "non_goal": "do not treat Copilot/Codex as the primary coder when a compiler handoff is available",
            "probe_questions": _probe_questions(intent_moves, waking_files),
        },
        "intent_moves": intent_moves,
        "file_sim_orchestration": {
            "mode": "sequential_graph_sim",
            "waking_files": waking_files[:12],
            "graph_id": graph.get("graph_id"),
            "graph_edges": graph.get("edge_count", 0),
            "focus_packets": _compact_focus_packets(graph),
            "sequence": _simulation_sequence(intent_moves, waking_files),
        },
        "deepseek_compiler_handoff": {
            "role": "deepseek_coder_compiler_each_prompt",
            "model": _deepseek_model(),
            "autonomous_write": _autonomous_write_enabled(),
            "context_pack_path": "logs/copilot_probe_push_cycle_latest.json",
            "dynamic_context_pack_path": "logs/dynamic_context_pack.json",
            "compiler_prompt": "",
        },
        "validation_closure": {
            "gates": [
                "pytest for touched unit surface",
                "git diff --check",
                "intent_loop receipt recorded",
                "numeric prompt touch recorded",
                "training candidate generated if code changed",
            ],
            "closure_logs": [
                "logs/deepseek_prompt_results.jsonl",
                "logs/intent_loop_latest.json",
                "logs/edit_pairs.jsonl",
                "logs/training_pairs.jsonl",
                "logs/file_intelligence_graph_history.jsonl",
            ],
            "backward_learning_pass": (
                "after validation, feed accepted touched files back into intent_file_memory, "
                "intent_nodes, numeric touches, and file graph co-touch edges"
            ),
        },
        "context_pack_summary": _context_pack_summary(context_pack or {}, context_selection),
        "paths": {
            "latest": "logs/copilot_probe_push_cycle_latest.json",
            "history": "logs/copilot_probe_push_cycle.jsonl",
            "markdown": "logs/copilot_probe_push_cycle.md",
        },
    }
    packet["deepseek_compiler_handoff"]["compiler_prompt"] = render_deepseek_compiler_prompt(packet)
    if write:
        logs = root / "logs"
        _write_json(logs / "copilot_probe_push_cycle_latest.json", packet)
        _append_jsonl(logs / "copilot_probe_push_cycle.jsonl", packet)
        (logs / "copilot_probe_push_cycle.md").write_text(render_copilot_probe_push_cycle(packet), encoding="utf-8")
    return packet


def render_deepseek_compiler_prompt(packet: dict[str, Any]) -> str:
    """Render the exact prompt body DeepSeek should see for this cycle."""
    probe = packet.get("operator_probe") or {}
    handoff = packet.get("deepseek_compiler_handoff") or {}
    lines = [
        "PUSH CYCLE CONTRACT:",
        "Copilot/Codex is the operator probe and sim orchestrator.",
        "DeepSeek is the bounded coding/compiler delegate.",
        "Do not expand scope unless the file graph proves the dependency.",
        "",
        "OPERATOR READ:",
        str(probe.get("read") or ""),
        "",
        "RAW PROMPT:",
        str(packet.get("operator_prompt") or ""),
        "",
        f"DELETED WORDS: {', '.join(packet.get('deleted_words') or []) or 'none'}",
        "",
        "INTENT MOVES:",
    ]
    for move in packet.get("intent_moves") or []:
        files = ", ".join(move.get("files") or []) or "none"
        lines.append(
            f"- {move.get('intent_key')} | confidence={move.get('confidence')} | files={files} | {move.get('why')}"
        )
    lines.extend(["", "WAKING FILES:"])
    for file_row in ((packet.get("file_sim_orchestration") or {}).get("waking_files") or [])[:10]:
        sources = ", ".join(file_row.get("sources") or [])
        lines.append(f"- {file_row.get('name')} score={file_row.get('score')} via {sources}")
    lines.extend(["", "FILE GRAPH FOCUS:"])
    for file_packet in ((packet.get("file_sim_orchestration") or {}).get("focus_packets") or [])[:6]:
        lines.append(f"- {file_packet.get('id')}: {file_packet.get('role_hint') or 'unknown role'}")
        for edge in file_packet.get("top_edges") or []:
            lines.append(f"  edge {edge.get('type')} -> {edge.get('peer')}: {edge.get('evidence')}")
    lines.extend([
        "",
        "REQUIRED OUTPUT:",
        "1. Restate the bounded mutation target.",
        "2. Name files to touch first and files to avoid.",
        "3. Propose the smallest patch or say NO_MUTATION if context is insufficient.",
        "4. Name validation gates.",
        "5. Explain what should be learned backward into file memory if accepted.",
        "",
        f"CONTEXT PACK: {handoff.get('context_pack_path') or 'logs/copilot_probe_push_cycle_latest.json'}",
    ])
    return "\n".join(lines)[:9000]


def render_copilot_probe_push_cycle(packet: dict[str, Any]) -> str:
    """Human-readable current push-cycle report."""
    lines = [
        "# Copilot Probe Push Cycle",
        "",
        f"- schema: `{packet.get('schema')}`",
        f"- cycle_id: `{packet.get('cycle_id')}`",
        f"- source: `{packet.get('source')}`",
        "",
        "## Operator Read",
        "",
        str((packet.get("operator_probe") or {}).get("read") or ""),
        "",
        "## Intent Moves",
        "",
    ]
    for move in packet.get("intent_moves") or []:
        files = ", ".join(move.get("files") or []) or "none"
        lines.append(f"- `{move.get('intent_key')}` confidence `{move.get('confidence')}` files `{files}`")
    lines.extend(["", "## Waking Files", ""])
    for row in ((packet.get("file_sim_orchestration") or {}).get("waking_files") or [])[:12]:
        lines.append(f"- `{row.get('name')}` score `{row.get('score')}` via `{', '.join(row.get('sources') or [])}`")
    lines.extend(["", "## Compiler Handoff", ""])
    handoff = packet.get("deepseek_compiler_handoff") or {}
    lines.extend([
        f"- role: `{handoff.get('role')}`",
        f"- model: `{handoff.get('model')}`",
        f"- autonomous_write: `{handoff.get('autonomous_write')}`",
        f"- context_pack_path: `{handoff.get('context_pack_path')}`",
        "",
        "## Closure",
        "",
    ])
    for gate in (packet.get("validation_closure") or {}).get("gates") or []:
        lines.append(f"- {gate}")
    return "\n".join(lines) + "\n"


def _build_intent_graph(
    root: Path,
    prompt: str,
    deleted_words: list[str],
    context_selection: dict[str, Any],
) -> dict[str, Any]:
    try:
        from src.tc_intent_keys_seq001_v001 import generate_intent_graph

        return generate_intent_graph(
            root,
            prompt,
            deleted_words=deleted_words,
            limit=5,
            context_selection=context_selection,
            write=True,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc), "intents": []}


def _build_file_graph(
    root: Path,
    prompt: str,
    deleted_words: list[str],
    waking_files: list[dict[str, Any]],
    *,
    write: bool,
) -> dict[str, Any]:
    try:
        from src.file_intelligence_graph_seq001_v001 import build_file_intelligence_graph

        return build_file_intelligence_graph(
            root,
            prompt=prompt,
            deleted_words=deleted_words,
            focus_files=[str(item.get("name") or "") for item in waking_files],
            write=write,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc), "focus_packets": [], "edge_count": 0}


def _expand_waking_files(
    root: Path,
    base_focus: list[dict[str, Any]],
    prompt: str,
    deleted_words: list[str],
    *,
    write: bool,
) -> list[dict[str, Any]]:
    if not base_focus:
        base_focus = [{"name": "src/tc_intent_keys_seq001_v001.py", "reason": "default_intent_surface", "score": 0.25}]
    try:
        from src.file_intelligence_graph_seq001_v001 import expand_files_with_graph

        return expand_files_with_graph(
            root,
            base_focus,
            prompt=prompt,
            deleted_words=deleted_words,
            limit=12,
            write=write,
        )
    except Exception:
        return _dedupe_file_rows(base_focus)[:12]


def _intent_moves(intent_graph: dict[str, Any]) -> list[dict[str, Any]]:
    moves = []
    for item in (intent_graph.get("intents") or [])[:5]:
        moves.append({
            "index": item.get("index"),
            "segment": item.get("segment"),
            "intent_key": item.get("intent_key"),
            "scope": item.get("scope"),
            "verb": item.get("verb"),
            "target": item.get("target"),
            "scale": item.get("scale"),
            "confidence": item.get("confidence", 0.0),
            "void": bool(item.get("void")),
            "files": item.get("files") or [],
            "why": item.get("why") or "",
        })
    return moves


def _collect_focus_files(
    context_selection: dict[str, Any],
    context_pack: dict[str, Any],
    explicit_focus: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(explicit_focus)
    rows.extend(context_selection.get("files") or [])
    rows.extend(context_pack.get("focus_files") or [])
    return _dedupe_file_rows(rows)


def _dedupe_file_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            row = {"name": str(row)}
        name = str(row.get("name") or row.get("file") or row.get("path") or "").replace("\\", "/").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        out.append({
            "name": name,
            "score": row.get("score", row.get("final_score", 0.0)),
            "sources": row.get("sources") or [row.get("reason") or row.get("source") or "context"],
        })
    return out


def _compact_focus_packets(graph: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for packet in (graph.get("focus_packets") or [])[:8]:
        edges = []
        for edge in (packet.get("top_edges") or [])[:4]:
            peer = edge.get("dst") if edge.get("src") == packet.get("id") else edge.get("src")
            edges.append({
                "type": edge.get("type"),
                "peer": peer,
                "weight": edge.get("weight"),
                "evidence": str(edge.get("evidence") or "")[:180],
            })
        out.append({
            "id": packet.get("id"),
            "path": packet.get("path"),
            "role_hint": str(packet.get("role_hint") or "")[:220],
            "risks": packet.get("risks") or [],
            "top_edges": edges,
        })
    return out


def _simulation_sequence(intent_moves: list[dict[str, Any]], waking_files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary_files = [str(row.get("name")) for row in waking_files[:5] if row.get("name")]
    return [
        {
            "step": 1,
            "actor": "copilot_probe",
            "job": "pressure-test the operator prompt and extract unresolved intent",
            "intent_keys": [move.get("intent_key") for move in intent_moves[:5]],
        },
        {
            "step": 2,
            "actor": "file_sim",
            "job": "wake graph-neighbor files and collect concerns before mutation",
            "files": primary_files,
        },
        {
            "step": 3,
            "actor": "orchestrator_grader",
            "job": "choose the smallest mutation plan and reject scope creep",
        },
        {
            "step": 4,
            "actor": "deepseek_compiler",
            "job": "draft or refuse the bounded patch with validation gates",
        },
        {
            "step": 5,
            "actor": "backward_learning_pass",
            "job": "record accepted files, failures, and deranked context for the next prompt",
        },
    ]


def _operator_read(prompt: str, moves: list[dict[str, Any]], deleted_words: list[str]) -> str:
    prompt_lower = prompt.lower()
    if "copilot" in prompt_lower and "deepseek" in prompt_lower:
        base = (
            "You are redefining Copilot/Codex as the cognition probe and scheduler: "
            "it should compile operator pressure into file-aware jobs, then hand coding "
            "to DeepSeek/compiler every prompt cycle."
        )
    elif "intent" in prompt_lower and "file" in prompt_lower:
        base = (
            "You are asking the repo to treat intent as routing math: prompts wake files, "
            "files simulate consequences, and accepted fixes become memory."
        )
    else:
        base = "The prompt is asking for a bounded next move, not a generic status answer."
    if deleted_words:
        base += f" Deleted-word residue should be treated as hidden intent pressure: {', '.join(deleted_words[:8])}."
    if moves:
        keys = ", ".join(str(move.get("intent_key")) for move in moves[:3] if move.get("intent_key"))
        if keys:
            base += f" Current intent keys: {keys}."
    return base


def _probe_questions(moves: list[dict[str, Any]], waking_files: list[dict[str, Any]]) -> list[str]:
    primary = ", ".join(str(row.get("name")) for row in waking_files[:4] if row.get("name")) or "none"
    return [
        "Which operator ambiguity must be resolved before mutation?",
        "Which file owns the next bounded compiler action?",
        f"Which graph neighbors must be loaded before DeepSeek writes? current={primary}",
        "What validation receipt closes this prompt loop?",
    ]


def _context_pack_summary(context_pack: dict[str, Any], context_selection: dict[str, Any]) -> dict[str, Any]:
    signals = context_pack.get("signals") or {}
    return {
        "surface": context_pack.get("surface"),
        "context_status": context_selection.get("status"),
        "context_confidence": context_selection.get("confidence", 0),
        "focus_file_count": len(context_pack.get("focus_files") or []),
        "deleted_words": signals.get("deleted_words") or [],
        "stale_blocks": context_selection.get("stale_blocks") or [],
    }


def _cycle_id(
    prompt: str,
    deleted_words: list[str],
    moves: list[dict[str, Any]],
    waking_files: list[dict[str, Any]],
    source: str,
) -> str:
    payload = json.dumps(
        {
            "prompt": prompt,
            "deleted": deleted_words[:12],
            "moves": [move.get("intent_key") for move in moves[:5]],
            "files": [row.get("name") for row in waking_files[:8]],
            "source": source,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return "probe-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _deepseek_model() -> str:
    return os.environ.get("DEEPSEEK_MODEL") or os.environ.get("DEEPSEEK_CODER_MODEL") or "deepseek-coder"


def _autonomous_write_enabled() -> bool:
    return os.environ.get("DEEPSEEK_AUTONOMOUS_PROMPT_WRITES", "").lower() in {"1", "true", "yes"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
