"""Opus pause-pulse simulation optimizer for prompt-to-file intelligence."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.manifest_syntax_matcher_seq001_v001 import match_manifest_syntax
from src.operator_syntax_triggers_seq001_v001 import match_operator_syntax_triggers

SCHEMA = "opus_micro_pulse_runtime/v1"
LATEST = "logs/opus_micro_pulse_latest.json"
HISTORY = "logs/opus_micro_pulse.jsonl"
MARKDOWN = "logs/opus_micro_pulse.md"
EXECUTOR_PROMPT = "logs/opus_executor_prompt_latest.md"

PROMPT_CLASSES = {
    "conversation": {
        "policy": "learning_packet_only",
        "mutates": False,
        "tokens": {"take", "what", "think", "idea", "maybe", "opinion", "talk", "why"},
    },
    "exploration": {
        "policy": "hypothesis_packet",
        "mutates": False,
        "tokens": {"what", "if", "could", "maybe", "imagine", "theory", "explore"},
    },
    "directive": {
        "policy": "standard_file_sim",
        "mutates": True,
        "tokens": {"build", "implement", "make", "wire", "add", "fix", "execute", "do"},
    },
    "debug": {
        "policy": "debug_chain",
        "mutates": True,
        "tokens": {"debug", "bug", "broken", "stale", "wrong", "cutoff", "failing", "test"},
    },
    "audit": {
        "policy": "audit_chain",
        "mutates": False,
        "tokens": {"audit", "assess", "review", "weakness", "risk", "grade"},
    },
    "correction": {
        "policy": "operator_contract_learning",
        "mutates": False,
        "tokens": {"wrong", "hate", "stupid", "not", "closer", "frustration", "opposite"},
    },
    "planning": {
        "policy": "architecture_packet",
        "mutates": False,
        "tokens": {"plan", "architecture", "workflow", "strategy", "system", "contract"},
    },
}


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


def classify_prompt(text: str) -> dict[str, Any]:
    tokens = set(_tokens(text))
    scores: dict[str, int] = {}
    for name, spec in PROMPT_CLASSES.items():
        scores[name] = len(tokens & set(spec["tokens"]))
    if re.search(r"\b(build|implement|execute|do that|go ahead|make sure)\b", text, re.I):
        scores["directive"] += 4
    if re.search(r"\b(debug|bug|stale|wrong|failing|cutoff|broken)\b", text, re.I):
        scores["debug"] += 3
    if re.search(r"\b(audit|review|assess|grade)\b", text, re.I):
        scores["audit"] += 3
    if re.search(r"\b(what if|maybe|imagine|theory|could)\b", text, re.I):
        scores["exploration"] += 2
    if re.search(r"\b(hate|stupid|wrong|opposite|not quite|frustrat)\w*\b", text, re.I):
        scores["correction"] += 3
    if re.search(r"\b(plan|architecture|workflow|system|contract)\b", text, re.I):
        scores["planning"] += 2
    prompt_class = max(scores, key=lambda key: (scores[key], _class_priority(key)))
    spec = PROMPT_CLASSES[prompt_class]
    return {
        "prompt_class": prompt_class,
        "sim_policy": spec["policy"],
        "durable_mutation_allowed": bool(spec["mutates"]),
        "scores": scores,
        "epistemic_status": _epistemic_status(prompt_class),
    }


def render_opus_micro_pulse(result: dict[str, Any]) -> str:
    cannon = result.get("cannon_job") or {}
    lines = [
        "# Opus Micro-Pulse Runtime",
        "",
        f"- prompt_hash: `{result.get('prompt_hash')}`",
        f"- prompt_class: `{cannon.get('prompt_class')}`",
        f"- executor_session: `{cannon.get('executor_session')}`",
        f"- sim_policy: `{cannon.get('sim_policy')}`",
        f"- predicted_files: `{len(cannon.get('predicted_files') or [])}`",
        "",
        "## Expanded Task For Executor",
        "",
        cannon.get("expanded_task", ""),
        "",
        "## Pause Pulses",
        "",
    ]
    for pulse in result.get("pulses") or []:
        lines.extend([
            f"### Pulse {pulse.get('pause_index')} - {pulse.get('prompt_class')}",
            "",
            f"- session: `{(pulse.get('session_broker') or {}).get('executor_session')}`",
            f"- policy: `{pulse.get('sim_policy')}`",
            f"- intent_keys: {', '.join('`' + key + '`' for key in pulse.get('intent_keys_live') or []) or '`none`'}",
            "",
            "#### File Interrogations",
            "",
        ])
        for item in pulse.get("file_interrogations") or []:
            lines.append(f"- `{item.get('file')}` {item.get('file_comment')}")
            lines.append(f"  - coding_agent: {item.get('coding_agent_note')}")
        lines.extend(["", "#### Theories", ""])
        for theory in pulse.get("theories") or []:
            lines.append(f"- `{theory.get('theory')}` confidence={theory.get('confidence')} :: {theory.get('reason')}")
        lines.append("")
    pending = result.get("pending_backward_learning") or {}
    lines.extend([
        "## Pending Backward Learning",
        "",
        f"- status: `{pending.get('status')}`",
        f"- predicted_files_waiting_for_diff: `{len(pending.get('predicted_files') or [])}`",
        f"- metric: `{pending.get('metric')}`",
    ])
    return "\n".join(lines) + "\n"


def _composition_fragments(prompt: str, row: dict[str, Any], *, max_pulses: int) -> list[str]:
    rewrites = row.get("rewrites") or []
    fragments = []
    for rewrite in rewrites[-max_pulses:]:
        new = str(rewrite.get("new") or "").strip()
        if len(new) >= 24:
            fragments.append(new)
    if not fragments:
        words = prompt.split()
        if not words:
            return [""]
        for pct in (0.35, 0.7, 1.0):
            take = max(1, min(len(words), int(len(words) * pct)))
            fragments.append(" ".join(words[:take]))
    fragments.append(prompt)
    out: list[str] = []
    for frag in fragments:
        frag = frag.strip()
        if frag and frag not in out:
            out.append(frag)
    return out[-max_pulses:] or [prompt]


def _select_files(root: Path, fragment: str, classification: dict[str, Any], *, file_limit: int) -> list[str]:
    syntax = match_operator_syntax_triggers(root, fragment, intent_key=" ".join(_intent_keys(fragment, classification)), limit=file_limit)
    files = [str(row.get("file") or "") for row in syntax if row.get("file")]
    files.extend(_explicit_runtime_files(fragment))
    if classification["prompt_class"] in {"debug", "directive"}:
        files.extend([
            "src/opus_micro_pulse_runtime_seq001_v001.py",
            "src/root_sim_key_file_seq001_v001.py",
            "src/unified_manifest_state_seq001_v001.py",
        ])
    if classification["prompt_class"] in {"conversation", "correction", "exploration"}:
        files.extend([
            "logs/prompt_journal.jsonl",
            "logs/operator_syntax_triggers.json",
        ])
    return [rel for rel in dict.fromkeys(files) if rel][:file_limit]


def _explicit_runtime_files(text: str) -> list[str]:
    low = text.lower()
    rows = []
    if "manifest" in low:
        rows.extend(["MANIFEST.md", "ROOT_SIM_KEYS.md", "src/unified_manifest_state_seq001_v001.py"])
    if "root" in low or "sim key" in low:
        rows.extend(["src/root_sim_key_file_seq001_v001.py", "ROOT_SIM_KEYS.md"])
    if "prompt" in low:
        rows.extend(["src/prompt_manifest_compiler_seq001_v001.py", "logs/prompt_journal.jsonl"])
    if "file" in low and ("talk" in low or "comment" in low or "conscious" in low):
        rows.extend(["src/file_bug_chat_seq001_v001.py", "logs/file_bug_chat_latest.json"])
    if "backward" in low or "diff" in low:
        rows.extend(["src/codex_edit_outcome_binder_seq001_v001.py", "logs/edit_pairs.jsonl"])
    return rows


def _selected_manifests(root: Path, fragment: str, files: list[str]) -> list[dict[str, Any]]:
    try:
        match = match_manifest_syntax(root, fragment + " " + " ".join(files), limit=6, write=False)
        return match.get("selected_manifests") or []
    except Exception:
        return []


def _file_interrogation(root: Path, rel: str, fragment: str, classification: dict[str, Any], pulse_index: int) -> dict[str, Any]:
    profile = _file_profile(root, rel)
    intent_keys = _intent_keys(fragment, classification)
    reason = _why_opus_called(rel, fragment, classification)
    self_claim = profile.get("identity") or _identity_from_path(rel)
    mismatch = _mismatch(reason, self_claim)
    solution = _file_solution(rel, classification, mismatch)
    faults = _persistent_faults(root, rel)
    comment = (
        f"I was touched by Opus on pause {pulse_index} because it thinks I am {reason}. "
        f"I am really {self_claim}. {mismatch} Solution: {solution}. "
        f"Persistent faults: {faults}."
    )
    return {
        "file": rel,
        "opus_reason": reason,
        "file_self_model": self_claim,
        "mismatch": mismatch,
        "intent_keys": intent_keys,
        "file_comment": comment,
        "coding_agent_note": (
            f"If Codex touches `{rel}`, verify whether Opus prediction `{reason}` matched actual role `{self_claim}`. "
            f"After execution, write touched/predicted/missed status into the backward learning packet."
        ),
        "deepseek_folder_manager_note": _deepseek_note(rel, solution),
        "persistent_faults": faults,
        "numeric_encoding": _numeric(_tokens(" ".join([rel, fragment, self_claim]))),
    }


def _file_profile(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    if path.exists() and path.is_file():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:5000]
        except Exception:
            text = ""
        doc = ""
        for line in text.splitlines()[:20]:
            stripped = line.strip().strip('"')
            if stripped and not stripped.startswith(("from ", "import ")):
                doc = stripped
                break
        return {"identity": doc or _identity_from_path(rel)}
    return {"identity": _identity_from_path(rel)}


def _why_opus_called(rel: str, fragment: str, classification: dict[str, Any]) -> str:
    low = fragment.lower()
    if "manifest" in rel.lower() or "manifest" in low:
        return "manifest state holder for this prompt"
    if "prompt" in rel.lower() or "prompt" in low:
        return "prompt composition and intent-key compiler"
    if "bug" in rel.lower() or "debug" in classification["prompt_class"]:
        return "debug pressure witness"
    if "root" in rel.lower():
        return "root navigation key for called files"
    if "log" in rel.lower():
        return "operator history evidence"
    return f"{classification['prompt_class']} context candidate"


def _mismatch(reason: str, self_claim: str) -> str:
    reason_tokens = set(_tokens(reason))
    claim_tokens = set(_tokens(self_claim))
    if reason_tokens & claim_tokens:
        return "Opus read me mostly correctly."
    return "Opus may be flattening my role; calibrate my syntax triggers before trusting this route."


def _file_solution(rel: str, classification: dict[str, Any], mismatch: str) -> str:
    if "flattening" in mismatch:
        return "increase learned syntax triggers from this prompt if Codex actually touches me"
    if classification["prompt_class"] == "conversation":
        return "log as learning only; do not launch file sim"
    if classification["prompt_class"] == "debug":
        return "route through debug chain and require grader receipt"
    return "keep me in the executor packet only if later pulses still select me"


def _persistent_faults(root: Path, rel: str) -> str:
    bugs = _load_json(root / "logs" / "file_bug_surface_latest.json") or {}
    hits = [row for row in bugs.get("bugs") or [] if str(row.get("owner") or "") == rel]
    if hits:
        return "; ".join(str(row.get("title") or "open bug") for row in hits[:3])
    syntax = _load_json(root / "logs" / "operator_syntax_triggers.json") or {}
    row = (syntax.get("files") or {}).get(rel) or {}
    if int(row.get("observations") or 0) == 0:
        return "low-touch file; can be missed by Opus unless static syntax matches"
    return f"observations={row.get('observations', 0)}; learned triggers may need backward-pass validation"


def _deepseek_note(rel: str, solution: str) -> str:
    folder = _folder_for(rel)
    return f"Folder manager `{folder}` should store this pulse comment locally and normalize the repair rule: {solution}."


def _stale_flags(root: Path, files: list[str]) -> list[dict[str, Any]]:
    surface = _load_json(root / "logs" / "file_bug_surface_latest.json") or {}
    bugs = surface.get("bugs") or []
    rows = []
    owners = set(files)
    for bug in bugs:
        title = str(bug.get("title") or "").lower()
        owner = str(bug.get("owner") or "")
        if owner in owners or "stale" in title:
            rows.append({
                "owner": owner,
                "severity": bug.get("severity"),
                "title": bug.get("title"),
                "next_action": bug.get("next_action"),
            })
        if len(rows) >= 8:
            break
    return rows


def _theories(pulse: dict[str, Any]) -> list[dict[str, Any]]:
    files = pulse.get("selected_files") or []
    stale = pulse.get("stale_flags") or []
    cls = pulse.get("prompt_class")
    return [
        {
            "theory": "intent_route",
            "confidence": round(min(0.95, 0.35 + len(files) * 0.06), 3),
            "reason": f"{len(files)} files self-selected for {cls} policy",
        },
        {
            "theory": "stale_poison_risk",
            "confidence": round(min(0.9, 0.2 + len(stale) * 0.09), 3),
            "reason": f"{len(stale)} stale flags must be shown before executor action",
        },
        {
            "theory": "missed_file_learning",
            "confidence": 0.72 if files else 0.31,
            "reason": "Codex diff will train files touched-but-not-predicted after execution",
        },
    ]


def _opus_theory_packet(pulse: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": "simulation_optimizer",
        "read_only_until_enter": True,
        "selected_files": pulse.get("selected_files") or [],
        "file_comments": [row.get("file_comment") for row in pulse.get("file_interrogations") or []],
        "executor_warning": "Use this as prediction, not truth; backward pass must score the diff.",
    }


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


def _render_executor_prompt(
    *,
    prompt: str,
    classification: dict[str, Any],
    session: dict[str, Any],
    predicted: list[str],
    selected_manifests: list[str],
    interrogations: list[dict[str, Any]],
    quick_fixes: list[str],
    stale: list[dict[str, Any]],
    theories: list[dict[str, Any]],
) -> str:
    lines = [
        "# Opus Executor Prompt",
        "",
        "This generated prompt is the primary instruction packet for Codex/Copilot.",
        "Use the raw operator prompt only as fallback evidence when this packet is ambiguous.",
        "",
        "## Execution Gate",
        "",
        f"- prompt_class: `{classification['prompt_class']}`",
        f"- sim_policy: `{classification['sim_policy']}`",
        f"- executor_session: `{session['executor_session']}`",
        f"- executor_reason: {session['reason']}",
        "",
        "## Operator Fallback Prompt",
        "",
        prompt,
        "",
        "## Required Read Set",
        "",
        "- `logs/prompt_cannon_job_latest.json`",
        "- `logs/opus_micro_pulse_latest.json`",
        "- `logs/cannon_execution_gate_latest.json`",
        "- `MANIFEST.md`",
        "- `ROOT_SIM_KEYS.md`",
    ]
    for rel in selected_manifests:
        lines.append(f"- `{rel}`")
    lines.extend(["", "## Predicted File Chain", ""])
    lines.extend(f"- `{rel}`" for rel in predicted)
    lines.extend(["", "## Quick Fix / Improvement Queue", ""])
    if quick_fixes:
        lines.extend(f"- {row}" for row in quick_fixes[:12])
    else:
        lines.append("- `none-surfaced`")
    lines.extend(["", "## File Intelligence", ""])
    for row in interrogations[:18]:
        lines.extend([
            f"### {row.get('file')}",
            "",
            f"- opus_reason: {row.get('opus_reason')}",
            f"- self_model: {row.get('file_self_model')}",
            f"- file_comment: {row.get('file_comment')}",
            f"- coding_agent: {row.get('coding_agent_note')}",
            f"- deepseek_folder_manager: {row.get('deepseek_folder_manager_note')}",
            "",
        ])
    if not interrogations:
        lines.append("- `none-selected`")
    lines.extend(["", "## Stale / Blocking Evidence", ""])
    if stale:
        for row in stale[:12]:
            lines.append(f"- `{row.get('severity')}` `{row.get('owner')}` {row.get('title')} :: {row.get('next_action')}")
    else:
        lines.append("- `none-surfaced`")
    lines.extend(["", "## Opus Theories", ""])
    for row in theories[:9]:
        lines.append(f"- `{row.get('theory')}` confidence={row.get('confidence')} :: {row.get('reason')}")
    lines.extend([
        "",
        "## Executor Contract",
        "",
        "- Do not execute from the raw operator prompt alone.",
        "- Treat this packet as the refined task.",
        "- Complete local quick fixes when they are inside the selected file chain.",
        "- If a quick fix is not local, defer it explicitly in the closeout receipt.",
        "- After work, write a touched-file receipt for backward file-intelligence learning.",
    ])
    return "\n".join(lines) + "\n"


def _quick_fix_queue(interrogations: list[dict[str, Any]], stale: list[dict[str, Any]]) -> list[str]:
    rows = []
    for item in interrogations:
        mismatch = str(item.get("mismatch") or "")
        if "flattening" in mismatch:
            rows.append(f"`{item.get('file')}` update syntax/numeric triggers if Codex actually touches this file")
        faults = str(item.get("persistent_faults") or "")
        if faults and "low-touch" not in faults and "observations=" not in faults:
            rows.append(f"`{item.get('file')}` verify persistent fault: {faults}")
    for item in stale:
        rows.append(f"`{item.get('owner')}` stale pressure: {item.get('title')} -> {item.get('next_action')}")
    return _dedupe(rows)


def _dedupe(rows: list[str]) -> list[str]:
    return list(dict.fromkeys(row for row in rows if row))


def _pending_backward_packet(root: Path, prompt_hash: str, predicted_files: list[str], cannon: dict[str, Any]) -> dict[str, Any]:
    touched = _git_changed_files(root)
    predicted = list(dict.fromkeys(predicted_files[:18]))
    touched_set = set(touched)
    predicted_set = set(predicted)
    return {
        "schema": "backward_file_intelligence_learning_pending/v1",
        "ts": _now(),
        "prompt_hash": prompt_hash,
        "status": "pending_until_executor_diff_or_next_file_call",
        "executor_session": cannon.get("executor_session"),
        "metric": "opus_dynamic_file_intelligence_prediction_vs_codex_execution_diff",
        "predicted_files": predicted,
        "currently_touched_files": touched[:40],
        "true_positive_now": sorted(predicted_set & touched_set),
        "missed_by_opus_now": sorted(touched_set - predicted_set)[:40],
        "dead_weight_now": sorted(predicted_set - touched_set)[:40],
        "learning_rule": (
            "Touched+predicted raises trigger confidence; touched+not-predicted adds syntax/numeric triggers; "
            "predicted+untouched waits pending until that file is called again."
        ),
    }


def _write_manifest_state(root: Path, result: dict[str, Any]) -> None:
    try:
        from src.unified_manifest_state_seq001_v001 import refresh_master_manifest
    except Exception:
        return
    files = (result.get("cannon_job") or {}).get("predicted_files") or []
    for folder in sorted({_folder_for(rel) for rel in files}):
        manifest = root / ("MANIFEST.md" if folder in {"", "."} else f"{folder}/MANIFEST.md")
        if not manifest.exists():
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text(f"# MANIFEST - {folder or '.'}\n", encoding="utf-8")
        old = manifest.read_text(encoding="utf-8", errors="ignore")
        new = _append_pulse_folder_block(old, folder, result)
        if new != old:
            manifest.write_text(new, encoding="utf-8")
    refresh_master_manifest(root, files, dry_run=False)


def _write_copilot_bootstrap(root: Path, result: dict[str, Any]) -> None:
    path = root / ".github" / "copilot-instructions.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    start = "<!-- codex:opus-cannon-bootstrap -->"
    end = "<!-- /codex:opus-cannon-bootstrap -->"
    cannon = result.get("cannon_job") or {}
    block = "\n".join([
        start,
        "## Opus Cannon Bootstrap",
        "",
        "This file is only the bootstrap contract. The generated Opus cannon is the current executor prompt.",
        "",
        "- primary_executor_prompt: `logs/opus_executor_prompt_latest.md`",
        "- cannon_packet: `logs/prompt_cannon_job_latest.json`",
        "- pulse_packet: `logs/opus_micro_pulse_latest.json`",
        "- gate_packet: `logs/cannon_execution_gate_latest.json`",
        f"- current_prompt_hash: `{result.get('prompt_hash')}`",
        f"- current_executor_session: `{cannon.get('executor_session')}`",
        f"- current_prompt_class: `{cannon.get('prompt_class')}`",
        "",
        "Executor rule: read the primary executor prompt first; use the operator prompt only as fallback evidence.",
        end,
    ])
    if start in old and end in old:
        new = re.sub(rf"{re.escape(start)}.*?{re.escape(end)}", block, old, flags=re.S)
    else:
        new = old.rstrip() + "\n\n" + block + "\n"
    if new != old:
        path.write_text(new, encoding="utf-8")


def _append_pulse_folder_block(content: str, folder: str, result: dict[str, Any]) -> str:
    start = "<!-- manifest:opus-micro-pulse-state -->"
    end = "<!-- /manifest:opus-micro-pulse-state -->"
    content = re.sub(rf"\n?{re.escape(start)}.*?{re.escape(end)}\n?", "", content, flags=re.S).rstrip()
    cannon = result.get("cannon_job") or {}
    lines = [
        start,
        "## Opus Micro-Pulse State",
        "",
        f"- prompt_hash: `{result.get('prompt_hash')}`",
        f"- prompt_class: `{cannon.get('prompt_class')}`",
        f"- executor_session: `{cannon.get('executor_session')}`",
        f"- metric: `opus_prediction_vs_executor_diff`",
        "",
        "### Local Pulse Comments",
        "",
    ]
    for pulse in result.get("pulses") or []:
        for item in pulse.get("file_interrogations") or []:
            rel = str(item.get("file") or "")
            if _folder_for(rel) == folder:
                lines.append(f"- `{rel}` {item.get('file_comment')}")
                lines.append(f"  - coding_agent: {item.get('coding_agent_note')}")
    lines.extend(["", "### Pending Backward Pass", ""])
    pending = result.get("pending_backward_learning") or {}
    for rel in pending.get("predicted_files") or []:
        if _folder_for(str(rel)) == folder:
            lines.append(f"- `{rel}` waiting_for_codex_diff")
    lines.append(end)
    return content + "\n\n" + "\n".join(lines) + "\n"


def _session_broker(classification: dict[str, Any], text: str) -> dict[str, Any]:
    cls = classification["prompt_class"]
    low = text.lower()
    if cls in {"conversation", "correction", "exploration"}:
        session = "opus_learning_only"
        reason = "prompt teaches operator/file intelligence without immediate executor mutation"
    elif re.search(r"\b(ui|frontend|design|css|jsx|screen|layout)\b", low):
        session = "copilot_ui_session"
        reason = "UI/design language favors visible iterative executor"
    elif cls in {"debug", "directive"}:
        session = "codex_execution_session"
        reason = "clear repair/build intent should become bounded diff"
    elif cls == "audit":
        session = "deepseek_audit_session"
        reason = "audit prompt should inspect and grade before mutation"
    else:
        session = "claude_code_architecture_session"
        reason = "architecture/planning prompt needs long-context orchestration"
    return {"executor_session": session, "reason": reason}


def _intent_keys(text: str, classification: dict[str, Any]) -> list[str]:
    tokens = _tokens(text)
    anchors = [tok for tok in tokens if tok in {
        "opus", "micro", "pulse", "file", "manifest", "prompt", "codex", "backward",
        "diff", "intent", "keys", "debug", "stale", "simulation", "folder", "deepseek",
        "gemini", "copilot", "executor", "runtime", "learning", "syntax",
    }]
    if not anchors:
        anchors = tokens[:4]
    keys = [f"{classification['prompt_class']}:{tok}" for tok in anchors[:10]]
    return list(dict.fromkeys(keys)) or [f"{classification['prompt_class']}:general"]


def _identity_from_path(rel: str) -> str:
    name = Path(rel.replace("\\", "/")).stem.replace("_", " ")
    if rel.endswith(".jsonl") or rel.endswith(".json"):
        return f"log/state artifact for {name}"
    if rel.endswith(".md"):
        return f"manifest/readable state document for {name}"
    return f"code module for {name}"


def _folder_for(rel: str) -> str:
    clean = rel.replace("\\", "/").strip("/")
    if not clean or "/" not in clean:
        return "."
    return str(Path(clean).parent).replace("\\", "/")


def _epistemic_status(prompt_class: str) -> str:
    if prompt_class in {"conversation", "exploration", "correction", "planning"}:
        return "candidate_learning_not_durable_truth"
    if prompt_class == "audit":
        return "inspection_before_mutation"
    return "sealed_or_actionable_after_enter"


def _class_priority(name: str) -> int:
    return {"directive": 7, "debug": 6, "correction": 5, "audit": 4, "planning": 3, "exploration": 2, "conversation": 1}.get(name, 0)


def _composition_source(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "has_rewrites": bool(row.get("rewrites")),
        "rewrite_count": len(row.get("rewrites") or []),
        "hesitation_count": (row.get("signals") or {}).get("hesitation_count"),
        "source": row.get("source", ""),
    }


def _latest_prompt_row(root: Path) -> dict[str, Any]:
    path = root / "logs" / "prompt_journal.jsonl"
    if not path.exists():
        return {}
    for line in reversed(path.read_text(encoding="utf-8", errors="ignore").splitlines()):
        try:
            return json.loads(line)
        except Exception:
            continue
    return {}


def _row_text(row: dict[str, Any]) -> str:
    return str(row.get("msg") or row.get("prompt") or row.get("text") or row.get("message") or "")


def _git_changed_files(root: Path) -> list[str]:
    import subprocess

    out: list[str] = []
    for cmd in (["git", "diff", "--name-only"], ["git", "diff", "--name-only", "--cached"]):
        try:
            proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        except Exception:
            continue
        if proc.returncode == 0:
            out.extend(line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip())
    return list(dict.fromkeys(out))


def _tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[a-zA-Z0-9]+", str(text).replace("_", " ").lower()) if len(tok) > 2]


def _numeric(tokens: list[str]) -> dict[str, Any]:
    bins = [0] * 16
    for tok in tokens:
        bins[int(hashlib.sha256(tok.encode("utf-8")).hexdigest()[:2], 16) % len(bins)] += 1
    return {"bins": bins, "token_count": len(tokens)}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


__all__ = ["build_opus_micro_pulse_runtime", "classify_prompt", "render_opus_micro_pulse"]
