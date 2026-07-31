"""root_sim_key_file_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .root_sim_key_file_seq001_v001_compiled_seq005_v001 import _merge
from pathlib import Path
from typing import Any

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
