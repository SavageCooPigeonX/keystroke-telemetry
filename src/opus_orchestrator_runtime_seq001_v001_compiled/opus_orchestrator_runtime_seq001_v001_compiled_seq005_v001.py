"""opus_orchestrator_runtime_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_orchestrator_runtime_seq001_v001_compiled_seq006_v001 import MANIFEST_NOTE
from typing import Any
import json

def _hush_summary(hush: dict[str, Any]) -> dict[str, Any]:
    repo = hush.get("repo_classification") or {}
    return {
        "path": "logs/hush_intent_runtime_latest.json",
        "active_repo": repo.get("active_repo", ""),
        "repo_confidence": repo.get("repo_confidence", 0),
        "mutation_fence": repo.get("mutation_fence", "blocked"),
        "intent_moves": [row.get("name", "") for row in hush.get("intent_moves") or []],
        "file_packet_count": len(hush.get("file_packets") or []),
    }


def _agent_from_packet(packet: dict[str, Any], jobs: list[dict[str, Any]], fence: str) -> dict[str, Any]:
    file_path = packet.get("file", "")
    job = next((row for row in jobs if row.get("target_file") == file_path), {})
    scope = packet.get("mutation_scope") or {}
    action = "artifact patch+test, no direct overwrite"
    if fence == "blocked":
        action = "plan/artifact only; Hush mutation fence is blocked"
    return {
        "file": file_path,
        "readiness": scope.get("readiness", ""),
        "gemini": "select context, file goal, neighbors, validation",
        "deepseek_job": job.get("job_id", "not_queued"),
        "allowed_action": action,
        "quote": packet.get("file_quote", ""),
    }


def _manifest_write(prompt: str, packets: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [p.get("file", "") for p in packets if (p.get("mutation_scope") or {}).get("readiness") == "draft_ready"]
    blocked = [p.get("file", "") for p in packets if (p.get("mutation_scope") or {}).get("readiness") == "blocked"]
    md = "\n".join([
        "### Opus Orchestrator Sim",
        f"- prompt: {prompt}",
        f"- ready files: {', '.join(ready[:6]) or 'none'}",
        f"- blocked files: {', '.join(blocked[:4]) or 'none'}",
        f"- delegate jobs: {', '.join(row.get('job_id', '') for row in jobs[:6]) or 'none'}",
        "- rule: Claude Opus may write manifest orchestration notes; source apply still requires grader pass.",
    ])
    return {"targets": ["MANIFEST.md", "src/MANIFEST.md", MANIFEST_NOTE], "markdown": md}


def _work_completed(delegates: dict[str, Any], sim: dict[str, Any]) -> list[str]:
    jobs = delegates.get("jobs") or []
    items = [f"queued {len(jobs)} Gemini+DeepSeek file delegate job(s)"]
    if sim:
        items.append(f"file sim mode {sim.get('mode')} with {(sim.get('backward_learning_pass') or {}).get('status')}")
    return items
