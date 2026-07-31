"""file_sim_deepseek_lane_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_sim_deepseek_lane_seq001_v001_compiled_seq002_v001 import _select_action
from .file_sim_deepseek_lane_seq001_v001_compiled_seq003_v001 import _context_pack
from .file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001 import _hush_blocks_mutation
from .file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001 import _hush_runtime
from .file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001 import _hush_summary
from .file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001 import _prompt
from .file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001 import CONTEXT_PACK
from .file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001 import PROMPT_JOBS
from .file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001 import _append_jsonl
from .file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001 import _blocked_delegates
from .file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001 import _now
from .file_sim_deepseek_lane_seq001_v001_compiled_seq005_v001 import _write_json
from pathlib import Path
from src.file_deepseek_delegate_seq001_v001 import queue_file_deepseek_delegates
from typing import Any
import hashlib
import json
import os

def queue_perpendicular_deepseek_job(root: Path, sim: dict[str, Any], *, write: bool = True) -> dict[str, Any]:
    """Queue exactly one DeepSeek job from a file-sim result."""
    root = Path(root)
    hush = _hush_runtime(root, sim)
    action = _select_action(sim, hush)
    pack = _context_pack(sim, action)
    prompt = _prompt(sim, action)
    if _hush_blocks_mutation(hush):
        delegates = _blocked_delegates(hush)
    else:
        delegates = queue_file_deepseek_delegates(
            root,
            sim.get("learning_packets") or [],
            intent=sim.get("intent") or {},
            write=write,
            limit=3,
        )
    job_id = "dsfs-" + hashlib.sha1(
        f"{sim.get('ts')}|{action.get('mode')}|{action.get('target_file')}".encode("utf-8")
    ).hexdigest()[:16]
    job = {
        "schema": "deepseek_prompt_job/v1",
        "ts": _now(),
        "job_id": job_id,
        "status": "queued",
        "source": "file_sim_perpendicular_lane/v1",
        "mode": action["mode"],
        "model": os.environ.get("DEEPSEEK_CODING_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro",
        "priority": action["priority"],
        "prompt": prompt,
        "focus_files": action["focus_files"],
        "context_pack_path": CONTEXT_PACK,
        "context_confidence": action["confidence"],
        "autonomous_write": False,
        "write_artifact": True,
        "artifact_path": f"logs/deepseek_artifacts/{job_id}_{action['mode']}.md",
        "max_tokens": 8000,
        "selected_action": action,
        "hush_mutation_fence": ((hush.get("repo_classification") or {}).get("mutation_fence") or "unknown") if hush else "unknown",
    }
    result = {
        "schema": "file_sim_deepseek_lane/v1",
        "ts": _now(),
        "queued": False,
        "job": job,
        "action": action,
        "context_pack_path": CONTEXT_PACK,
        "rule": "DeepSeek runs perpendicular to Copilot; it drafts plans/artifacts until approval opens surgery.",
        "hush_intent_runtime": _hush_summary(hush),
        "file_delegates": delegates,
    }
    if write:
        _write_json(root / CONTEXT_PACK, pack)
        _append_jsonl(root / PROMPT_JOBS, job)
        _write_json(root / "logs" / "file_sim_deepseek_lane_latest.json", result | {"queued": True})
        _append_jsonl(root / "logs" / "file_sim_deepseek_lane.jsonl", result | {"queued": True})
        result["queued"] = True
    return result
