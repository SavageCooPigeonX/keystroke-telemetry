"""opus_orchestrator_runtime_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import json

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


def _prompt_box_summary(box: dict[str, Any]) -> dict[str, Any]:
    open_rows = box.get("open_problems") or []
    return {
        "path": box.get("paths", {}).get("latest_md", "logs/copilot_prompt_box_latest.md"),
        "writer": box.get("writer", "claude-opus"),
        "open_count": box.get("open_count", 0),
        "max_open": box.get("max_open", 20),
        "dropped_count": box.get("dropped_count", 0),
        "routing_note": box.get("routing_note", ""),
        "intent_routes": (box.get("intent_routes") or [])[:6],
        "top_open": [
            {
                "id": row.get("id"),
                "intent_key": row.get("intent_key"),
                "priority_score": row.get("priority_score"),
                "effective_score": row.get("effective_score"),
            }
            for row in open_rows[:8]
        ],
    }
