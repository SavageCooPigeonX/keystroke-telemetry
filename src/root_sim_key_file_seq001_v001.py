"""Root navigation key for every file/key called into sim."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_KEY = "ROOT_SIM_KEYS.md"
DEFAULT_ATTENTION_LIMIT = 18
def build_root_sim_key_file(root: Path, *, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    packet = _load_json(root / "logs" / "prompt_context_packet_latest.json") or {}
    probe = _load_json(root / "logs" / "copilot_probe_push_cycle_latest.json") or {}
    chat = _load_json(root / "logs" / "file_bug_chat_latest.json") or {}
    pulse = _load_json(root / "logs" / "opus_micro_pulse_latest.json") or {}
    rows: dict[str, dict[str, Any]] = {}
    _add_prompt_packet(rows, packet)
    _add_probe_cycle(rows, probe)
    _add_bug_chat(rows, chat)
    _add_opus_pulse(rows, pulse)
    ordered = sorted(rows.values(), key=lambda row: (row.get("kind", ""), row.get("file", "")))
    attention = _attention_plan(ordered, DEFAULT_ATTENTION_LIMIT)
    result = {
        "schema": "root_sim_key_file/v1",
        "ts": _now(),
        "path": ROOT_KEY,
        "called_count": len(ordered),
        "attention_limit": DEFAULT_ATTENTION_LIMIT,
        "attention_selected_count": len(attention),
        "attention_plan": attention,
        "called_files": ordered,
        "source_paths": [
            "logs/prompt_context_packet_latest.json",
            "logs/copilot_probe_push_cycle_latest.json",
            "logs/file_bug_chat_latest.json",
            "logs/opus_micro_pulse_latest.json",
        ],
    }
    if write:
        _write_json(root / "logs" / "root_sim_key_file_latest.json", result)
        _append_jsonl(root / "logs" / "root_sim_key_file.jsonl", result)
        (root / ROOT_KEY).write_text(render_root_sim_key_file(result), encoding="utf-8")
        _write_live_manifest_receipts(root, result)
    return result
def render_root_sim_key_file(result: dict[str, Any]) -> str:
    lines = [
        "# Root Sim Keys",
        "",
        "One root navigation file for every file/key called into the latest sim surfaces.",
        "",
        f"- called: `{result.get('called_count', 0)}`",
        f"- attention_selected: `{result.get('attention_selected_count', 0)}/{result.get('attention_limit', 18)}`",
        f"- generated: `{result.get('ts', '')}`",
        "", "## Attention Plan", "", "| File / Key | Slot | Why |", "|---|---|---|",
    ]
    for row in result.get("attention_plan") or []:
        lines.append(f"| `{row.get('file')}` | {row.get('attention_slot')} | {_cell(row.get('why'))} |")
    lines.extend([
        "",
        "## Called Files / Keys",
        "",
        "| File / Key | Kind | Local Manifest | Why In Sim | Intent Keys |",
        "|---|---|---|---|---|",
    ])
    for row in result.get("called_files") or []:
        lines.append(
            f"| `{row.get('file')}` | {row.get('kind')} | `{row.get('local_manifest')}` | "
            f"{_cell(row.get('why'))} | {_cell(', '.join(row.get('intent_keys') or []), 180)} |"
        )
    lines.extend(["", "## File Comments", ""])
    for row in result.get("called_files") or []:
        if row.get("operator_comment") or row.get("coding_agent_note") or row.get("opus_note"):
            lines.extend([f"### {row.get('file')}", "", f"**Operator Note:** {row.get('operator_comment', '')}", "", f"**Coding Agent Note:** {row.get('coding_agent_note', '')}", "", f"**Opus Note:** {row.get('opus_note', '')}", ""])
    return "\n".join(lines) + "\n"
def _attention_plan(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    quotas = [
        ("prompt_intent", 6),
        ("manifest_shard", 3),
        ("bug_chat", 4),
        ("opus_pulse", 4),
        ("probe_wake", 3),
        ("low_touch", 2),
    ]
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for slot, quota in quotas:
        pool = _slot_pool(rows, slot)
        for row in pool:
            if len([r for r in selected if r["attention_slot"] == slot]) >= quota:
                break
            if row["file"] in seen:
                continue
            selected.append({**row, "attention_slot": slot})
            seen.add(row["file"])
    for row in rows:
        if len(selected) >= limit:
            break
        if row["file"] not in seen:
            selected.append({**row, "attention_slot": "fill"})
            seen.add(row["file"])
    return selected[:limit]
def _slot_pool(rows: list[dict[str, Any]], slot: str) -> list[dict[str, Any]]:
    if slot == "low_touch":
        return [row for row in rows if not row.get("operator_comment") and "probe_wake" not in row.get("kind", "")]
    return [row for row in rows if slot in row.get("kind", "")]
def _write_live_manifest_receipts(root: Path, result: dict[str, Any]) -> None:
    try:
        from src.unified_manifest_state_seq001_v001 import append_folder_unified_state, refresh_master_manifest
    except Exception:
        return
    called = [row.get("file", "") for row in result.get("called_files") or []]
    folders = sorted({_folder_for_file(str(rel)) for rel in called})
    for folder in folders:
        manifest = root / ("MANIFEST.md" if folder in {"", "."} else f"{folder}/MANIFEST.md")
        if not manifest.exists():
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(f"# MANIFEST - {folder or '.'}\n", encoding="utf-8")
        old = manifest.read_text(encoding="utf-8", errors="ignore")
        new = append_folder_unified_state(root, old, "." if folder in {"", "."} else folder, called, old)
        if new != old:
            manifest.write_text(new, encoding="utf-8")
    refresh_master_manifest(root, called, dry_run=False)
def _folder_for_file(file_path: str) -> str:
    clean = file_path.strip("\"'").replace("\\", "/")
    if not clean or "/" not in clean:
        return "."
    return str(Path(clean).parent).replace("\\", "/")
def _add_prompt_packet(rows: dict[str, dict[str, Any]], packet: dict[str, Any]) -> None:
    for intent in ((packet.get("intent_key_encoding") or {}).get("intents") or []):
        key = str(intent.get("intent_key") or "")
        for file_path in intent.get("files") or []:
            _merge(rows, str(file_path), "prompt_intent", intent.get("segment", ""), key)
    for shard in ((packet.get("manifest_state_protocol") or {}).get("shattered_intent_keys") or []):
        key = str(shard.get("intent_key") or "")
        for file_path in shard.get("files") or []:
            _merge(rows, str(file_path), "manifest_shard", shard.get("segment", ""), key)
def _add_probe_cycle(rows: dict[str, dict[str, Any]], probe: dict[str, Any]) -> None:
    sim = probe.get("file_sim_orchestration") or {}
    for item in sim.get("waking_files") or []:
        name = str(item.get("path") or item.get("file") or item.get("name") or "")
        why = ",".join(str(src) for src in item.get("sources") or [])
        _merge(rows, name, "probe_wake", why, "")
def _add_bug_chat(rows: dict[str, dict[str, Any]], chat: dict[str, Any]) -> None:
    for comment in chat.get("comments") or []:
        owner = str(comment.get("owner") or "")
        row = _merge(rows, owner, "bug_chat", comment.get("why_touched", ""), comment.get("intent_key", ""))
        row["operator_comment"] = comment.get("operator_comedy", "")
        row["coding_agent_note"] = comment.get("coding_agent_note", "")
        row["opus_note"] = comment.get("opus_manager_note", "")
        row["learned"] = comment.get("learned_from_sim", "")
        row["interlink_score"] = comment.get("interlink_score")
def _add_opus_pulse(rows: dict[str, dict[str, Any]], pulse: dict[str, Any]) -> None:
    for item in (pulse.get("cannon_job") or {}).get("predicted_files") or []:
        _merge(rows, str(item), "opus_pulse", "Opus pause pulse predicted this file before Enter", "")
    for pulse_row in pulse.get("pulses") or []:
        for item in pulse_row.get("file_interrogations") or []:
            rel = str(item.get("file") or "")
            row = _merge(rows, rel, "opus_pulse", item.get("opus_reason", ""), ",".join(item.get("intent_keys") or []))
            if item.get("file_comment"):
                row["operator_comment"] = item.get("file_comment", "")
            if item.get("coding_agent_note"):
                row["coding_agent_note"] = item.get("coding_agent_note", "")
            if item.get("deepseek_folder_manager_note"):
                row["opus_note"] = item.get("deepseek_folder_manager_note", "")
            row["learned"] = item.get("mismatch", "")
def _merge(rows: dict[str, dict[str, Any]], file_path: str, kind: str, why: Any, intent_key: str) -> dict[str, Any]:
    key = file_path.strip()
    row = rows.setdefault(key, {
        "file": key,
        "kind": kind,
        "local_manifest": _local_manifest(key),
        "why": "",
        "intent_keys": [],
        "operator_comment": "",
        "coding_agent_note": "",
        "opus_note": "",
        "learned": "",
    })
    kinds = set(str(row.get("kind") or "").split("+"))
    kinds.add(kind)
    row["kind"] = "+".join(sorted(k for k in kinds if k))
    if why and str(why) not in str(row.get("why") or ""):
        row["why"] = (str(row.get("why") or "") + " " + str(why)).strip()
    if intent_key:
        row["intent_keys"] = list(dict.fromkeys([*row.get("intent_keys", []), str(intent_key)]))
    return row
def _local_manifest(file_path: str) -> str:
    clean = file_path.strip("\"'").replace("\\", "/")
    if not clean or "/" not in clean:
        return "MANIFEST.md"
    folder = str(Path(clean).parent).replace("\\", "/")
    if folder in {"", "."}:
        return "MANIFEST.md"
    return f"{folder}/MANIFEST.md"
def _cell(value: Any, limit: int = 140) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:limit]
def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
