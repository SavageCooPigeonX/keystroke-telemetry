"""Compile operator prompts into manifest-aware file-sim packets."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENCODED_RE = re.compile(r"seq(?P<seq>\d+)(?:_v(?P<version>\d+))?(?:_d(?P<date>\d{4}))?(?:__(?P<intent>.+))?")

def decode_file_intent(path: str) -> dict[str, Any]:
    rel = path.replace("\\", "/").strip("/")
    stem = Path(rel).stem
    match = ENCODED_RE.search(stem)
    encoded = (match.group("intent") if match else "") or ""
    if not encoded and "__" in stem:
        encoded = stem.split("__", 1)[1]
    words = [part for part in re.split(r"[_\W]+", encoded.lower()) if part]
    return {
        "path": rel,
        "seq": match.group("seq") if match else None,
        "version": match.group("version") if match else None,
        "date_code": match.group("date") if match else None,
        "encoded_intent": " ".join(words) if words else "unencoded standard path",
        "changelog_hint": "file-name-intent:" + (" ".join(words) if words else "unencoded standard path"),
    }

def build_prompt_context_packet(
    root: Path,
    prompt: str,
    *,
    source: str = "codex",
    focus_files: list[str] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    prompt = (prompt.strip() or _latest_prompt(root)).strip()
    changed = focus_files or _git_changed_files(root)
    intent_graph = _intent_graph(root, prompt)
    context_selection = _load_json(root / "logs" / "context_selection.json") or {}
    manifest_state = _manifest_state(root, intent_graph, context_selection, changed)
    probe_packet = _copilot_probe_packet(root, prompt, context_selection, changed, source, write)
    packet = {
        "schema": "prompt_manifest_context_packet/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "prompt_hash": _sha(prompt),
        "operator_prompt": prompt,
        "role_contract": {
            "small_file_runtime": "gemini_file_probe",
            "folder_manifest_manager": "deepseek_folder_manifest",
            "master_manifest_session": "opus_repo_orchestrator",
            "execution_surface": "codex_copilot_after_file_sim_sync",
            "mutation_rule": "codex acts after file-sim confirms prompt context",
        },
        "intent_key_encoding": intent_graph,
        "context_selection": _thin_context_selection(context_selection),
        "file_name_changelog": [decode_file_intent(rel) for rel in changed[:80]],
        "manifest_contract": manifest_state.get("write_boundary", []),
        "manifest_state_protocol": manifest_state,
        "copilot_prompt_box": _render_prompt_box(prompt, intent_graph, context_selection, changed, manifest_state),
        "probe_cycle": probe_packet,
    }
    if write:
        _write_json(root / "logs" / "prompt_context_packet_latest.json", packet)
        _append_jsonl(root / "logs" / "prompt_context_packets.jsonl", packet)
        _write_json(root / "logs" / "opus_master_manifest_session.json", _opus_session(packet))
        (root / "logs" / "copilot_prompt_box_latest.md").write_text(packet["copilot_prompt_box"], encoding="utf-8")
    return packet

def _intent_graph(root: Path, prompt: str) -> dict[str, Any]:
    try:
        from src.tc_intent_keys_seq001_v001 import generate_intent_graph

        return generate_intent_graph(root, prompt, write=True)
    except Exception as exc:
        return {"schema": "intent_graph_unavailable/v1", "prompt": prompt, "error": str(exc)}

def _copilot_probe_packet(root: Path, prompt: str, context: dict[str, Any], changed: list[str], source: str, write: bool) -> dict[str, Any]:
    try:
        from src.copilot_probe_push_cycle_seq001_v001 import build_copilot_probe_push_cycle

        return build_copilot_probe_push_cycle(
            root,
            prompt,
            [],
            context_selection=context,
            focus_files=changed[:20],
            source=source,
            write=write,
        )
    except Exception as exc:
        return {"schema": "copilot_probe_cycle_unavailable/v1", "error": str(exc)}

def _manifest_state(root: Path, graph: dict[str, Any], context: dict[str, Any], changed: list[str]) -> dict[str, Any]:
    from src.manifest_state_protocol_seq001_v001 import build_manifest_state_protocol

    return build_manifest_state_protocol(root, graph, context, changed)

def _thin_context_selection(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": context.get("schema"),
        "prompt_hash": context.get("prompt_hash"),
        "selected_files": context.get("selected_files") or context.get("files") or [],
        "steer": context.get("steer") or context.get("tc_steer") or {},
    }

def _render_prompt_box(prompt: str, graph: dict[str, Any], context: dict[str, Any], changed: list[str], manifest_state: dict[str, Any]) -> str:
    from src.manifest_state_protocol_seq001_v001 import render_manifest_state_prompt

    keys = graph.get("intents") or graph.get("intent_keys") or graph.get("keys") or []
    if isinstance(keys, dict):
        keys = list(keys.values())
    selected = [_selected_path(row) for row in (context.get("selected_files") or context.get("files") or [])]
    lines = [
        "# Copilot Prompt Box",
        "",
        "## Operator Prompt",
        prompt,
        "",
        "## File-Sim Sync Contract",
        "- Wait for manifest context before code mutation.",
        "- If manifest state is missing, stop and compile/read manifests first.",
        "- Treat file names as changelog hints when explaining why files are touched.",
        "- DeepSeek audits folder/state weakness; Opus/master manifest verifies final prompt.",
    ]
    lines.extend(["", *render_manifest_state_prompt(manifest_state), "", "## Intent Keys"])
    for row in keys[:12] if isinstance(keys, list) else []:
        lines.append(f"- `{row.get('intent_key') or row}`")
    lines.extend(["", "## Selected / Changed Files"])
    for rel in list(dict.fromkeys([*selected[:20], *changed[:20]])):
        lines.append(f"- `{rel}` :: {decode_file_intent(str(rel))['changelog_hint']}")
    return "\n".join(lines) + "\n"

def _selected_path(row: Any) -> str:
    if isinstance(row, dict):
        return str(row.get("path") or row.get("file") or row.get("target") or row.get("name") or row)
    return str(row)
def _opus_session(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "opus_master_manifest_session/v1",
        "ts": packet["ts"],
        "prompt_hash": packet["prompt_hash"],
        "master_role": packet["role_contract"]["master_manifest_session"],
        "verification_state": "pending_deepseek_audit",
        "prompt_box": "logs/copilot_prompt_box_latest.md",
        "latest_packet": "logs/prompt_context_packet_latest.json",
        "contract": packet["role_contract"],
        "manifest_state_protocol": "logs/prompt_context_packet_latest.json#manifest_state_protocol",
    }

def _latest_prompt(root: Path) -> str:
    path = root / "logs" / "prompt_journal.jsonl"
    if not path.exists():
        return ""
    for line in reversed(path.read_text(encoding="utf-8", errors="ignore").splitlines()):
        try:
            row = json.loads(line)
        except Exception:
            continue
        return str(row.get("msg") or row.get("prompt") or row.get("text") or row.get("message") or "")
    return ""

def _git_changed_files(root: Path) -> list[str]:
    out: list[str] = []
    for cmd in (["git", "diff", "--name-only"], ["git", "diff", "--name-only", "--cached"]):
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            out.extend(line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip())
    return list(dict.fromkeys(out))

def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
