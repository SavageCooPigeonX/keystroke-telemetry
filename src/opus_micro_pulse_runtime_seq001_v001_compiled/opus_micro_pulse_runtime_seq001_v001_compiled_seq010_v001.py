"""opus_micro_pulse_runtime_seq001_v001_compiled_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq011_v001 import _render_executor_prompt
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq012_v001 import _dedupe
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq012_v001 import _quick_fix_queue
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _intent_keys
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _session_broker
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import EXECUTOR_PROMPT
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq018_v001 import _now
from typing import Any
import re

def _cannon_packet(
    prompt: str,
    prompt_hash: str,
    classification: dict[str, Any],
    pulses: list[dict[str, Any]],
    seen_files: list[str],
) -> dict[str, Any]:
    session = _session_broker(classification, prompt)
    stale = []
    manifests = []
    interrogations = []
    theories = []
    for pulse in pulses:
        stale.extend(pulse.get("stale_flags") or [])
        manifests.extend(pulse.get("selected_manifests") or [])
        interrogations.extend(pulse.get("file_interrogations") or [])
        theories.extend(pulse.get("theories") or [])
    predicted = seen_files[:18]
    quick_fixes = _quick_fix_queue(interrogations, stale)
    selected_manifests = _dedupe([str(row.get("manifest") or "") for row in manifests if row.get("manifest")])[:12]
    expanded = [
        "Use this Opus cannon payload as the primary executor prompt.",
        "The raw operator prompt is fallback evidence, not the execution source of truth.",
        "Read MANIFEST.md, ROOT_SIM_KEYS.md, and logs/opus_executor_prompt_latest.md before acting.",
        f"Prompt class: {classification['prompt_class']} / policy={classification['sim_policy']}.",
        "Use Opus pulse output as prediction, not accepted truth.",
        "Before code mutation, inspect the predicted files that still match the final prompt.",
        "Address quick fixes if they are local to the selected files; otherwise explicitly defer them in the receipt.",
        "After execution, emit touched-files receipt so backward learning can score predicted, missed, and dead-weight files.",
        "",
        "Operator prompt:",
        prompt,
        "",
        "Predicted files:",
        *[f"- {rel}" for rel in predicted],
    ]
    if selected_manifests:
        expanded.extend(["", "Selected manifests:"])
        expanded.extend(f"- {rel}" for rel in selected_manifests)
    if quick_fixes:
        expanded.extend(["", "Quick fix / file improvement queue:"])
        expanded.extend(f"- {row}" for row in quick_fixes[:10])
    if interrogations:
        expanded.extend(["", "File intelligence notes:"])
        for row in interrogations[:12]:
            expanded.append(f"- {row.get('file')}: {row.get('file_comment')}")
    if stale:
        expanded.extend(["", "Stale flags to verify first:"])
        for row in stale[:8]:
            expanded.append(f"- {row.get('severity')} {row.get('owner')}: {row.get('title')}")
    expanded.extend([
        "",
        "Required closeout receipt:",
        "- list touched files",
        "- mark predicted/touched/missed files",
        "- note any quick fixes completed or deferred",
        "- update the relevant folder MANIFEST.md and backward learning packet",
    ])
    executor_prompt = _render_executor_prompt(
        prompt=prompt,
        classification=classification,
        session=session,
        predicted=predicted,
        selected_manifests=selected_manifests,
        interrogations=interrogations,
        quick_fixes=quick_fixes,
        stale=stale,
        theories=theories,
    )
    return {
        "schema": "prompt_cannon_job/v1",
        "ts": _now(),
        "prompt_hash": prompt_hash,
        "prompt_class": classification["prompt_class"],
        "sim_policy": classification["sim_policy"],
        "executor_session": session["executor_session"],
        "executor_reason": session["reason"],
        "sealed_intent_keys": _intent_keys(prompt, classification),
        "predicted_files": predicted,
        "selected_manifests": selected_manifests,
        "quick_fix_queue": quick_fixes[:12],
        "file_intelligence_notes": interrogations[:18],
        "stale_flags": stale[:12],
        "executor_prompt_path": EXECUTOR_PROMPT,
        "executor_prompt": executor_prompt,
        "expanded_task": "\n".join(expanded),
        "mutation_allowed": classification["durable_mutation_allowed"],
    }
