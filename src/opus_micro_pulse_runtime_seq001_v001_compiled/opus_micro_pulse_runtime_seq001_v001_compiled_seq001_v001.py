"""opus_micro_pulse_runtime_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq002_v001 import classify_prompt
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq003_v001 import render_opus_micro_pulse
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq004_v001 import _composition_fragments
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq004_v001 import _select_files
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq005_v001 import _selected_manifests
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq006_v001 import _file_interrogation
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq008_v001 import _stale_flags
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq008_v001 import _theories
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq009_v001 import _opus_theory_packet
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq010_v001 import _cannon_packet
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq012_v001 import _pending_backward_packet
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq013_v001 import _write_manifest_state
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq014_v001 import _write_copilot_bootstrap
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _intent_keys
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _session_broker
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _composition_source
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _latest_prompt_row
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq017_v001 import _row_text
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import EXECUTOR_PROMPT
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import HISTORY
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import LATEST
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import MARKDOWN
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import SCHEMA
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _append_jsonl
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _now
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _sha
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import re

def build_opus_micro_pulse_runtime(
    root: Path,
    prompt: str | None = None,
    *,
    prompt_row: dict[str, Any] | None = None,
    write: bool = True,
    max_pulses: int = 3,
    file_limit: int = 8,
) -> dict[str, Any]:
    """Simulate pause-pulse file interrogation before an Enter/cannon event."""
    root = Path(root)
    row = prompt_row or _latest_prompt_row(root)
    prompt = (prompt if prompt is not None else _row_text(row)).strip()
    prompt_hash = _sha(prompt)
    fragments = _composition_fragments(prompt, row, max_pulses=max_pulses)
    pulses = []
    seen_files: list[str] = []
    for idx, fragment in enumerate(fragments, start=1):
        classification = classify_prompt(fragment)
        files = _select_files(root, fragment, classification, file_limit=file_limit)
        for rel in files:
            if rel not in seen_files:
                seen_files.append(rel)
        pulse = {
            "pulse_id": f"{prompt_hash}.{idx:02d}",
            "pause_index": idx,
            "partial_prompt": fragment,
            "prompt_class": classification["prompt_class"],
            "sim_policy": classification["sim_policy"],
            "session_broker": _session_broker(classification, fragment),
            "intent_keys_live": _intent_keys(fragment, classification),
            "selected_files": files,
            "selected_manifests": _selected_manifests(root, fragment, files),
            "file_interrogations": [
                _file_interrogation(root, rel, fragment, classification, idx) for rel in files
            ],
            "stale_flags": _stale_flags(root, files),
        }
        pulse["theories"] = _theories(pulse)
        pulse["opus_theory_packet"] = _opus_theory_packet(pulse)
        pulses.append(pulse)
    final_classification = classify_prompt(prompt)
    cannon = _cannon_packet(prompt, prompt_hash, final_classification, pulses, seen_files)
    pending = _pending_backward_packet(root, prompt_hash, seen_files, cannon)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "prompt_hash": prompt_hash,
        "session_id": row.get("session_id", ""),
        "session_n": row.get("session_n", row.get("session", "")),
        "source": row.get("source", "manual"),
        "operator_prompt": prompt,
        "composition_source": _composition_source(row),
        "pulse_count": len(pulses),
        "pulses": pulses,
        "cannon_job": cannon,
        "pending_backward_learning": pending,
        "paths": {
            "latest": LATEST,
            "history": HISTORY,
            "markdown": MARKDOWN,
            "executor_prompt": EXECUTOR_PROMPT,
            "cannon_latest": "logs/prompt_cannon_job_latest.json",
            "pending_backward_latest": "logs/backward_file_intelligence_learning_pending_latest.json",
        },
    }
    if write:
        logs = root / "logs"
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_opus_micro_pulse(result), encoding="utf-8")
        (logs / "opus_executor_prompt_latest.md").write_text(cannon["executor_prompt"], encoding="utf-8")
        _write_json(logs / "prompt_cannon_job_latest.json", cannon)
        _append_jsonl(logs / "prompt_cannon_jobs.jsonl", cannon)
        _write_json(logs / "backward_file_intelligence_learning_pending_latest.json", pending)
        _append_jsonl(logs / "backward_file_intelligence_learning_pending.jsonl", pending)
        _write_copilot_bootstrap(root, result)
        _write_manifest_state(root, result)
    return result
