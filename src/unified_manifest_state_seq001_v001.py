"""Unified folder and master manifest state blocks."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

FOLDER_START = "<!-- manifest:folder-unified-state -->"
FOLDER_END = "<!-- /manifest:folder-unified-state -->"
MASTER_START = "<!-- manifest:master-persistent-state -->"
MASTER_END = "<!-- /manifest:master-persistent-state -->"
def append_folder_unified_state(root: Path, content: str, folder: str, changed: list[str], old: str = "") -> str:
    content = _replace_block(content, FOLDER_START, FOLDER_END, "")
    existing = _extract_block(old, FOLDER_START, FOLDER_END)
    block = render_folder_unified_state(root, folder, changed)
    if existing == block:
        block = existing
    return content.rstrip() + "\n\n" + block + "\n"
def render_folder_unified_state(root: Path, folder: str, changed: list[str]) -> str:
    protocol = _latest_protocol(root)
    own = "MANIFEST.md" if folder in {"", "."} else f"{folder}/MANIFEST.md"
    touched = [rel for rel in changed if _belongs(rel, folder)]
    read_set = [row.get("manifest") for row in protocol.get("read_set", [])]
    external = [rel for rel in read_set if rel and rel != own][:12]
    syntax = _syntax_rows(root, folder)
    lines = [
        FOLDER_START,
        "## Folder Unified State",
        "",
        f"- state_doc: `{own}`",
        "- write_authority: `own_folder_manifest_only`",
        "- read_authority: `selected_manifest_read_only`",
        f"- changed_files_in_scope: `{len(touched)}`",
        "",
        "### Local Files Learning Here",
        "",
        "| File | Observations | Learned Trigger Sample |",
        "|---|---:|---|",
    ]
    for row in syntax[:10]:
        learned = ", ".join((row.get("learned_operator_tokens") or [])[:8]) or "none"
        lines.append(f"| `{row.get('file')}` | {row.get('observations', 0)} | {_cell(learned)} |")
    if not syntax:
        lines.append("| `none` | 0 | no syntax trigger state for this folder yet |")
    lines.extend(["", "### Cross-Folder Manifests Read In Sim", ""])
    for rel in external:
        lines.append(f"- `{rel}`")
    if not external:
        lines.append("- `none-selected`")
    local_chats = [row for row in _bug_chat_rows(root) if _belongs(str(row.get("owner") or ""), folder)]
    lines.extend(["", "### Local Bug Chat", ""])
    for row in local_chats[:8]:
        lines.append(f"- `{row.get('owner')}` {row.get('operator_comedy')}")
        if row.get("coding_agent_note"):
            lines.append(f"  - coding_agent: {row.get('coding_agent_note')}")
    if not local_chats:
        lines.append("- `none-local`")
    key_state = _load_json(root / "logs" / "root_sim_key_file_latest.json") or {}
    attention = {row.get("file"): row.get("attention_slot") for row in key_state.get("attention_plan") or []}
    receipts = [row for row in key_state.get("called_files") or [] if _belongs(str(row.get("file") or ""), folder)]
    lines.extend(["", "### Live Sim Call Receipts", ""])
    for row in receipts[:12]:
        lines.append(f"- `{row.get('file')}` kind={row.get('kind')} attention={attention.get(row.get('file'), 'not_selected')} :: {_cell(row.get('why'))}")
    if not receipts:
        lines.append("- `none-called`")
    lines.extend(["", "### Local Write Queue", ""])
    for rel in touched[:12]:
        lines.append(f"- `{rel}` -> `{own}`")
    if not touched:
        lines.append("- `no-local-file-touch-this-cycle`")
    lines.append(FOLDER_END)
    return "\n".join(lines)
def refresh_master_manifest(root: Path, changed: list[str], *, dry_run: bool = False) -> dict[str, Any]:
    root = Path(root)
    path = root / "MANIFEST.md"
    old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else "# MASTER MANIFEST\n"
    new = append_master_persistent_state(root, old, changed)
    changed_flag = old != new
    if changed_flag and not dry_run:
        path.write_text(new, encoding="utf-8")
    return {"path": "MANIFEST.md", "changed": changed_flag}
def append_master_persistent_state(root: Path, content: str, changed: list[str]) -> str:
    content = _replace_block(content, MASTER_START, MASTER_END, "")
    protocol = _latest_protocol(root)
    prompt_packet = _load_json(root / "logs" / "prompt_context_packet_latest.json") or {}
    lines = [
        MASTER_START,
        "## Master Persistent State",
        "",
        "- state_doc: `MANIFEST.md`",
        "- role: `opus_master_manifest_project_structure_and_persistent_state`",
        "- folder_state_contract: `each folder writes one MANIFEST.md`",
        f"- latest_prompt_hash: `{prompt_packet.get('prompt_hash', '')}`",
        f"- manifest_gate: `{protocol.get('status', 'unknown')}`",
        "",
        "### Project Structure",
        "",
        "| Folder | Manifest | Changed In Scope |",
        "|---|---|---:|",
    ]
    for row in _folder_rows(root, changed)[:80]:
        lines.append(f"| `{row['folder']}` | `{row['manifest']}` | {row['changed_count']} |")
    lines.extend(["", "### Master Intent Keys", ""])
    for key in protocol.get("master_intent_keys", [])[:20]:
        lines.append(f"- `{key}`")
    if not protocol.get("master_intent_keys"):
        lines.append("- `none-current`")
    lines.extend(["", "### Surfaced Bug Queue", ""])
    for bug in _bug_rows(root)[:12]:
        lines.append(f"- `{bug.get('severity')}` `{bug.get('owner')}` {bug.get('title')} :: {bug.get('next_action')}")
    if not _bug_rows(root):
        lines.append("- `none-surfaced`")
    lines.extend(["", "### File Bug Chat", ""])
    for row in _bug_chat_rows(root)[:6]:
        lines.append(f"- `{row.get('owner')}` {row.get('operator_comedy')}")
    if not _bug_chat_rows(root):
        lines.append("- `none-generated`")
    key = _load_json(root / "logs" / "root_sim_key_file_latest.json") or {}
    lines.extend(["", "### Root Sim Key File", ""])
    lines.append(f"- `ROOT_SIM_KEYS.md` :: called={key.get('called_count', 0)}")
    pulse = _load_json(root / "logs" / "opus_micro_pulse_latest.json") or {}
    cannon = pulse.get("cannon_job") or {}
    lines.extend(["", "### Opus Micro-Pulse Runtime", ""])
    if pulse:
        lines.append(
            f"- `logs/opus_micro_pulse_latest.json` :: class={cannon.get('prompt_class')} "
            f"executor={cannon.get('executor_session')} predicted={len(cannon.get('predicted_files') or [])}"
        )
    else:
        lines.append("- `none-generated`")
    gate = _load_json(root / "logs" / "cannon_execution_gate_latest.json") or {}
    lines.extend(["", "### Cannon Execution Gate", ""])
    if gate:
        lines.append(
            f"- `logs/cannon_execution_gate_latest.json` :: status={gate.get('status')} "
            f"payload_ready={str(gate.get('payload_ready')).lower()} predicted={gate.get('predicted_file_count', 0)}"
        )
        if gate.get("blockers"):
            for blocker in gate.get("blockers", [])[:8]:
                lines.append(f"  - blocker: `{blocker}`")
    else:
        lines.append("- `blocked` :: cannon gate has not been configured")
    lines.extend(["", "### Persistent State Files", ""])
    for rel in _state_files():
        exists = (root / rel).exists()
        lines.append(f"- `{rel}` :: exists={str(exists).lower()}")
    lines.append(MASTER_END)
    return content.rstrip() + "\n\n" + "\n".join(lines) + "\n"
def _folder_rows(root: Path, changed: list[str]) -> list[dict[str, Any]]:
    manifests = sorted(path for path in root.rglob("MANIFEST.md") if ".git" not in path.parts)
    rows = []
    for manifest in manifests:
        folder = manifest.parent.relative_to(root).as_posix() if manifest.parent != root else "."
        count = sum(1 for rel in changed if _belongs(rel, folder))
        rows.append({"folder": folder, "manifest": manifest.relative_to(root).as_posix(), "changed_count": count})
    return rows
def _syntax_rows(root: Path, folder: str) -> list[dict[str, Any]]:
    state = _load_json(root / "logs" / "operator_syntax_triggers.json") or {}
    rows = [row for row in (state.get("files") or {}).values() if _belongs(str(row.get("file") or ""), folder)]
    rows.sort(key=lambda row: int(row.get("observations") or 0), reverse=True)
    return rows
def _state_files() -> list[str]:
    return [
        "logs/prompt_context_packet_latest.json",
        "logs/copilot_prompt_box_latest.md",
        "logs/intent_graph_latest.json",
        "logs/operator_syntax_triggers.json",
        "logs/opus_master_manifest_session.json",
        "logs/deepseek_push_audit_latest.json",
        "logs/file_bug_surface_latest.json",
        "logs/file_bug_chat_latest.json",
        "logs/root_sim_key_file_latest.json",
        "logs/opus_micro_pulse_latest.json",
        "logs/opus_executor_prompt_latest.md",
        "logs/prompt_cannon_job_latest.json",
        "logs/cannon_execution_gate_latest.json",
        "logs/backward_file_intelligence_learning_pending_latest.json",
    ]
def _latest_protocol(root: Path) -> dict[str, Any]:
    packet = _load_json(root / "logs" / "prompt_context_packet_latest.json") or {}
    return packet.get("manifest_state_protocol") or {}
def _bug_rows(root: Path) -> list[dict[str, Any]]:
    surface = _load_json(root / "logs" / "file_bug_surface_latest.json") or {}
    return surface.get("bugs") or []
def _bug_chat_rows(root: Path) -> list[dict[str, Any]]:
    chat = _load_json(root / "logs" / "file_bug_chat_latest.json") or {}
    return chat.get("comments") or []
def _replace_block(text: str, start: str, end: str, replacement: str) -> str:
    return re.sub(rf"\n?{re.escape(start)}.*?{re.escape(end)}\n?", replacement, text, flags=re.S).rstrip()
def _extract_block(text: str, start: str, end: str) -> str:
    match = re.search(rf"{re.escape(start)}.*?{re.escape(end)}", text, flags=re.S)
    return match.group(0).strip() if match else ""
def _belongs(file_path: str, folder: str) -> bool:
    clean = file_path.replace("\\", "/").strip("/")
    folder = folder.strip("/")
    return bool(clean) and (folder in {"", "."} or clean == folder or clean.startswith(folder + "/"))
def _cell(value: Any, limit: int = 160) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:limit]
def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
