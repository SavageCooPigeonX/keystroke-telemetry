"""batch_rewrite_sim_seq001_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq002_v001 import load_file_sim_config
from .batch_rewrite_sim_seq001_seq002_v001 import merge_file_sim_config
from .batch_rewrite_sim_seq001_seq003_v001 import compile_intent
from .batch_rewrite_sim_seq001_seq004_v001 import render_batch_rewrite_sim
from .batch_rewrite_sim_seq001_seq005_v001 import _file_job_council
from .batch_rewrite_sim_seq001_seq012_v001 import _render_file_job_council
from .batch_rewrite_sim_seq001_seq013_v001 import _rank_candidates
from .batch_rewrite_sim_seq001_seq016_v001 import _rewrite_orchestration
from .batch_rewrite_sim_seq001_seq017_v001 import _attach_incompatibility_reports
from .batch_rewrite_sim_seq001_seq018_v001 import _attach_consensus_scores
from .batch_rewrite_sim_seq001_seq021_v001 import _queue_deepseek_completion_jobs
from .batch_rewrite_sim_seq001_seq023_v001 import _orchestrator_oath
from .batch_rewrite_sim_seq001_seq024_v001 import _render_orchestrator_oath
from .batch_rewrite_sim_seq001_seq025_v001 import _render_file_push_narrative_fragment
from .batch_rewrite_sim_seq001_seq029_v001 import _distributed_intent_encoding
from .batch_rewrite_sim_seq001_seq030_v001 import _fire_record
from .batch_rewrite_sim_seq001_seq030_v001 import _identity_growth_record
from .batch_rewrite_sim_seq001_seq031_v001 import _git_status
from .batch_rewrite_sim_seq001_seq031_v001 import _load_failure_model
from .batch_rewrite_sim_seq001_seq034_v001 import SCHEMA
from .batch_rewrite_sim_seq001_seq034_v001 import _append_jsonl
from .batch_rewrite_sim_seq001_seq034_v001 import _load_json
from .batch_rewrite_sim_seq001_seq034_v001 import _load_jsonl
from .batch_rewrite_sim_seq001_seq034_v001 import _now
from .batch_rewrite_sim_seq001_seq034_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import os
import re

def simulate_batch_rewrites(
    root: Path,
    intent: str = "",
    limit: int | None = None,
    write: bool = True,
    config: dict[str, Any] | None = None,
    trigger: str = "manual",
    context_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    config = merge_file_sim_config(config or load_file_sim_config(root, write_default=write))
    limit = int(limit or config.get("max_proposals") or 6)
    compiled = compile_intent(root, intent)
    history = _load_jsonl(root / "logs" / "dead_token_collective_pairs.jsonl", int(config.get("history_limit") or 10000))
    dead_summary = _load_json(root / "logs" / "dead_token_collective_history.json") or {}
    failure = _load_failure_model(root)
    dirty = _git_status(root)
    candidates = _rank_candidates(root, compiled, history, dead_summary, failure, dirty, limit, config, context_selection)
    _attach_incompatibility_reports(candidates)
    _attach_consensus_scores(candidates, compiled, config)
    now = _now()
    result = {
        "schema": SCHEMA,
        "status": "fired",
        "ts": now,
        "trigger": trigger,
        "root": str(root),
        "mode": "source_rewrite_orchestration",
        "target_state": config.get("target_state", "interlinked_source_state"),
        "write_policy": "source_rewrite_after_orchestrator_approval",
        "file_sim_config": config,
        "rewrite_orchestration": _rewrite_orchestration(config),
        "intent": compiled,
        "distributed_intent_encoding": _distributed_intent_encoding(context_selection, compiled),
        "self_model": {
            "history_pairs": len(history),
            "avg_fix_rate": failure.get("avg_fix_rate"),
            "persistent_modules": failure.get("persistent_modules", [])[:10],
            "dirty_files": sorted(dirty)[:20],
        },
        "orchestrator": {
            "orchestrator_only": bool((config.get("orchestrator_policy") or {}).get("orchestrator_only", True)),
            "monitor_per_prompt": bool((config.get("orchestrator_policy") or {}).get("monitor_per_prompt", True)),
            "email_per_prompt": bool((config.get("orchestrator_policy") or {}).get("email_per_prompt", True)),
            "approval_required": bool((config.get("orchestrator_policy") or {}).get("approval_required", True)),
            "auto_write_allowed": bool((config.get("orchestrator_policy") or {}).get("auto_write_allowed", False)),
            "overwrite_policy": "quick proposal -> grader -> context injection -> incompatibility report -> approval -> deepseek rewrite -> compile",
            "next_allowed_actions": [
                "inject_context_pack",
                "request_operator_approval",
                "run_dry_source_rewrite",
                "apply_source_rewrite_after_approval",
                "run_cross_file_validation",
            ],
        },
        "orchestrator_oath": _orchestrator_oath(compiled),
        "proposals": candidates,
        "paths": {
            "latest": "logs/batch_rewrite_sim_latest.json",
            "history": "logs/batch_rewrite_sim.jsonl",
            "narrative": "logs/batch_rewrite_sim.md",
            "fire_history": "logs/file_sim_fire_history.jsonl",
            "config": "logs/file_sim_config.json",
            "deepseek_code_completion_jobs": "logs/deepseek_code_completion_jobs.jsonl",
            "orchestrator_dev_oath": "logs/orchestrator_dev_oath.md",
            "file_push_narrative_fragment": "logs/file_push_narrative_fragment.md",
            "file_job_council": "logs/file_job_council_latest.json",
            "file_job_council_history": "logs/file_job_council.jsonl",
            "file_job_council_markdown": "logs/file_job_council.md",
            "file_self_sim_learning": "logs/file_self_sim_learning_latest.json",
            "deepseek_learning_packets": "logs/deepseek_learning_packets.jsonl",
        },
    }
    result["file_job_council"] = _file_job_council(root, result)
    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        for proposal in candidates:
            _append_jsonl(logs / "file_identity_growth.jsonl", _identity_growth_record(result, proposal))
        result["deepseek_code_completion"] = _queue_deepseek_completion_jobs(root, result)
        result["file_job_council"] = _file_job_council(root, result)
        _write_json(logs / "file_job_council_latest.json", result["file_job_council"])
        _append_jsonl(logs / "file_job_council.jsonl", result["file_job_council"])
        (logs / "file_job_council.md").write_text(_render_file_job_council(result["file_job_council"]), encoding="utf-8")
        if (config.get("compiler_layers") or {}).get("file_self_learning", True):
            try:
                from src.file_self_sim_learning_seq001_v001 import simulate_file_self_learning
                result["file_self_learning"] = simulate_file_self_learning(
                    root,
                    intent=compiled.get("raw", ""),
                    limit=limit,
                    write=True,
                    source_result=result,
                    config=config,
                )
            except Exception as exc:
                result["file_self_learning_error"] = str(exc)
        try:
            from src.file_email_plugin_seq001_v001 import emit_file_sim_emails
            result["file_email"] = emit_file_sim_emails(root, result)
        except Exception as exc:
            result["file_email_error"] = str(exc)
        (logs / "orchestrator_dev_oath.md").write_text(_render_orchestrator_oath(result), encoding="utf-8")
        fragment = _render_file_push_narrative_fragment(result)
        (logs / "file_push_narrative_fragment.md").write_text(fragment, encoding="utf-8")
        _append_jsonl(logs / "file_push_narrative_fragments.jsonl", {
            "schema": "file_push_narrative_fragment/v1",
            "ts": result.get("ts"),
            "intent_key": (result.get("intent") or {}).get("intent_key", ""),
            "fragment": fragment,
        })
        (logs / "batch_rewrite_sim.md").write_text(render_batch_rewrite_sim(result), encoding="utf-8")
        _write_json(logs / "batch_rewrite_sim_latest.json", result)
        _append_jsonl(logs / "batch_rewrite_sim.jsonl", result)
        _append_jsonl(logs / "file_sim_fire_history.jsonl", _fire_record(result))
    return result
