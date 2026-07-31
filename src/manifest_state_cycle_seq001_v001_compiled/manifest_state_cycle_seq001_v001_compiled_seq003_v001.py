"""manifest_state_cycle_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _append_jsonl
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _own_manifest
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _sha
from .manifest_state_cycle_seq001_v001_compiled_seq005_v001 import _write_json
from pathlib import Path
from typing import Any
import json

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
