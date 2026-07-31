"""analyze_prompt_behavior_compiled_seq021_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq019_v001 import _write_json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import re

def _write_internal_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def _queue_deepseek(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    prompt = report["deepseek_prompt"]
    job_id = "ds-research-" + hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    job = {
        "schema": "deepseek_prompt_job/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        "status": "queued",
        "source": "scripts/analyze_prompt_behavior_seq002_v001_d0730__command_line_facade_for_the_lc_organism_health_refactor.py",
        "mode": "cognitive_response_style_research",
        "model": "deepseek-v4-pro",
        "prompt": prompt,
        "priority": 1,
        "context_pack_path": "logs/prompt_behavior_analysis_latest.json",
        "autonomous_write": False,
    }
    log = root / "logs" / "deepseek_prompt_jobs.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(job, ensure_ascii=False) + "\n")
    _write_json(root / "logs" / "deepseek_prompt_latest.json", job)
    return job
