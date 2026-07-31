"""file_sim_deepseek_lane_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001 import _dedupe
from .file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001 import _now
from typing import Any

def _action(mode: str, priority: int, job: dict[str, Any], bounded: str) -> dict[str, Any]:
    target = str(job.get("file") or "")
    focus = _dedupe([target, *(job.get("context_pack") or []), "src/MANIFEST.md", "MANIFEST.md"])
    return {
        "mode": mode,
        "priority": priority,
        "target_file": target,
        "intent_key": job.get("job_id") or "",
        "bounded_action": bounded,
        "focus_files": focus,
        "validation_plan": job.get("validation_plan") or [],
        "confidence": 0.75 if job.get("status") == "ready_for_split_plan" else 0.45,
        "line_count": job.get("line_count"),
        "size_state": job.get("size_state"),
        "split_pressure": job.get("split_pressure"),
    }


def _context_pack(sim: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    target = action.get("target_file")
    packets = [packet for packet in sim.get("learning_packets") or [] if packet.get("file") == target]
    edges = [
        edge for edge in (sim.get("relationship_graph") or {}).get("edges") or []
        if edge.get("from") == target or edge.get("to") == target
    ]
    return {
        "schema": "file_sim_deepseek_context_pack/v1",
        "ts": _now(),
        "role": "perpendicular_deepseek_lane",
        "target_state": "interlinked_source_state",
        "selected_action": action,
        "hush_intent_runtime": sim.get("hush_intent_runtime") or {},
        "intent": sim.get("intent") or {},
        "learning_packets": packets[:2],
        "relationship_edges": edges[:16],
        "manifest_state": "folder MANIFEST.md is source-local state; root MANIFEST.md is global stage",
        "must_not_do": [
            "do not overwrite source",
            "do not split without validation",
            "do not erase manifest state",
            "do not outrank Copilot/operator approval",
        ],
    }
