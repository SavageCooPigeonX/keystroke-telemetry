"""Apply a bounded prompt-driven manifest state write cycle."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.operator_syntax_triggers_seq001_v001 import learn_operator_syntax_triggers, match_operator_syntax_triggers
from src.folder_context_coupling_seq001_v001 import build_folder_context_coupling
from src.unified_manifest_state_seq001_v001 import append_folder_unified_state, refresh_master_manifest

LATEST = "logs/manifest_state_write_latest.json"
HISTORY = "logs/manifest_state_write.jsonl"
MARKDOWN = "logs/manifest_state_write.md"


def apply_manifest_state_cycle(
    root: Path,
    prompt: str,
    *,
    focus_files: list[str] | None = None,
    use_prompt_packet: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Let selected files write bounded learned state into their folder manifests."""
    root = Path(root)
    packet = _build_packet(root, prompt, focus_files or [], use_prompt_packet, write)
    graph = packet.get("intent_key_encoding") or {}
    learn_operator_syntax_triggers(root, graph, write=write)
    syntax_files = match_operator_syntax_triggers(root, prompt, intent_key=" ".join(packet.get("manifest_state_protocol", {}).get("master_intent_keys", [])), limit=8)
    selected_files = _selected_files(packet, syntax_files)
    selected_manifests = _selected_manifests(packet)
    folder_coupling = build_folder_context_coupling(
        root,
        prompt,
        focus_files=selected_files,
        selected_manifests=selected_manifests,
        write=write,
    )
    file_writes = _write_folder_manifests(root, selected_files, write)
    master = refresh_master_manifest(root, selected_files, dry_run=not write)
    result = {
        "schema": "manifest_state_write_cycle/v1",
        "ts": _now(),
        "prompt_hash": packet.get("prompt_hash", ""),
        "status": "manifest_state_written" if write else "dry_run",
        "selected_files": selected_files,
        "selected_manifests": selected_manifests,
        "file_writes": file_writes,
        "master_manifest": master,
        "syntax_matched_files": syntax_files,
        "folder_context_coupling": folder_coupling,
        "manifest_syntax_match": (packet.get("manifest_state_protocol") or {}).get("manifest_syntax_match") or {},
        "rule": "files write only to their own folder MANIFEST.md; selected external manifests are read-only sim context",
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_manifest_state_write(result), encoding="utf-8")
    return result


def render_manifest_state_write(result: dict[str, Any]) -> str:
    lines = [
        "# Manifest State Write Cycle",
        "",
        f"- status: `{result.get('status')}`",
        f"- prompt_hash: `{result.get('prompt_hash')}`",
        f"- rule: {result.get('rule')}",
        "",
        "## File Writes",
        "",
    ]
    for row in result.get("file_writes") or []:
        lines.append(f"- `{row.get('file')}` -> `{row.get('manifest')}` changed={row.get('changed')} reason={row.get('reason')}")
    if not result.get("file_writes"):
        lines.append("- `none`")
    lines.extend(["", "## Selected Manifests", ""])
    for row in result.get("selected_manifests") or []:
        lines.append(f"- `{row.get('manifest')}` source={row.get('source')} score={row.get('score', '')}")
    lines.extend(["", "## Manifest Syntax", ""])
    for row in (result.get("manifest_syntax_match") or {}).get("selected_manifests", [])[:10]:
        lines.append(f"- `{row.get('manifest')}` {row.get('classification')} tokens={', '.join(row.get('matched_tokens') or [])}")
    lines.extend(["", "## Folder Coupling", ""])
    for row in (result.get("folder_context_coupling") or {}).get("folders", [])[:10]:
        lines.append(f"- `{row.get('folder')}` autonomy={row.get('autonomy_score')} resistance={row.get('resistance_score')} mode={row.get('recommended_mode')}")
    return "\n".join(lines) + "\n"


def _selected_files(packet: dict[str, Any], syntax_files: list[dict[str, Any]]) -> list[str]:
    protocol = packet.get("manifest_state_protocol") or {}
    files = []
    for boundary in protocol.get("write_boundary") or []:
        folder = str(boundary.get("folder") or "")
        if folder:
            files.append(f"{folder}/MANIFEST.md")
    files.extend(str(row.get("file") or "") for row in syntax_files)
    files.extend(str(row.get("path") or "") for row in packet.get("file_name_changelog") or [])
    return [rel for rel in dict.fromkeys(file.replace("\\", "/") for file in files) if rel]


def _build_packet(root: Path, prompt: str, focus_files: list[str], use_prompt_packet: bool, write: bool) -> dict[str, Any]:
    if use_prompt_packet:
        from src.prompt_manifest_compiler_seq001_v001 import build_prompt_context_packet

        return build_prompt_context_packet(root, prompt, source="manifest_state_cycle", focus_files=focus_files, write=write)
    graph = _light_intent_graph(root, prompt, focus_files)
    from src.manifest_state_protocol_seq001_v001 import build_manifest_state_protocol

    protocol = build_manifest_state_protocol(root, graph, {"selected_files": [{"path": rel} for rel in focus_files]}, focus_files)
    packet = {
        "schema": "manifest_state_cycle_light_packet/v1",
        "prompt_hash": _sha(prompt),
        "operator_prompt": prompt,
        "intent_key_encoding": graph,
        "manifest_state_protocol": protocol,
        "file_name_changelog": [{"path": rel} for rel in focus_files],
    }
    if write:
        _write_json(root / "logs" / "prompt_context_packet_latest.json", packet)
        _append_jsonl(root / "logs" / "prompt_context_packets.jsonl", packet)
    return packet


def _light_intent_graph(root: Path, prompt: str, focus_files: list[str]) -> dict[str, Any]:
    intents = []
    for rel in focus_files:
        manifest = _own_manifest(root, rel)
        manifest_rel = manifest.relative_to(root).as_posix() if manifest and manifest.exists() else "MANIFEST.md"
        target = Path(rel).stem[:48].replace(" ", "_")
        intents.append({
            "intent_key": f"{Path(rel).parent.as_posix()}:route:{target}:minor",
            "segment": prompt[:240],
            "manifest_path": manifest_rel,
            "files": [rel],
        })
    return {"schema": "intent_graph/light_manifest_cycle/v1", "prompt": prompt, "intent_count": len(intents), "intents": intents}


def _selected_manifests(packet: dict[str, Any]) -> list[dict[str, Any]]:
    protocol = packet.get("manifest_state_protocol") or {}
    rows = [{"manifest": row.get("manifest"), "source": "manifest_read_set"} for row in protocol.get("read_set", [])]
    rows.extend({
        "manifest": row.get("manifest"),
        "source": "manifest_syntax_match",
        "score": row.get("score"),
        "matched_tokens": row.get("matched_tokens") or [],
    } for row in (protocol.get("manifest_syntax_match") or {}).get("selected_manifests", []))
    out = []
    seen = set()
    for row in rows:
        key = row.get("manifest")
        if key and key not in seen:
            seen.add(key)
            out.append(row)
    return out


def _write_folder_manifests(root: Path, files: list[str], write: bool) -> list[dict[str, Any]]:
    rows = []
    for rel in files:
        manifest = _own_manifest(root, rel)
        if not manifest or not manifest.exists():
            continue
        folder = "." if manifest.parent == root else manifest.parent.relative_to(root).as_posix()
        old = manifest.read_text(encoding="utf-8", errors="replace")
        scoped = [file for file in files if _belongs(file, folder)]
        new = append_folder_unified_state(root, old, folder, scoped, old)
        changed = old != new
        if changed and write:
            manifest.write_text(new, encoding="utf-8")
        rows.append({
            "file": rel,
            "manifest": manifest.relative_to(root).as_posix(),
            "folder": folder,
            "changed": changed,
            "reason": "syntax_or_context_selected_file_state",
        })
    return rows


def _own_manifest(root: Path, rel: str) -> Path | None:
    path = Path(rel)
    parts = path.parts
    for index in range(len(parts), 0, -1):
        candidate = root / Path(*parts[:index]) / "MANIFEST.md"
        if candidate.exists():
            return candidate
    return root / "MANIFEST.md" if (root / "MANIFEST.md").exists() else None


def _belongs(file_path: str, folder: str) -> bool:
    clean = file_path.replace("\\", "/").strip("/")
    folder = folder.strip("/")
    return bool(clean) and (folder in {"", "."} or clean == folder or clean.startswith(folder + "/"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


__all__ = ["apply_manifest_state_cycle", "render_manifest_state_write"]
