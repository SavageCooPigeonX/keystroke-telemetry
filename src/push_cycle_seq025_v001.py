"""Push-based learning cycle — the PUSH is the unit of learning.

Each git push = one learning cycle:
  1. Collect all prompts since last push (operator signal)
  2. Collect git diff (copilot signal — the operator never types code)
  3. Compute sync score (did copilot output match operator intent?)
  4. Generate dual coaching (for operator AND for coding agent)
  5. Update calibration + node memory
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CYCLE_STATE_PATH = "logs/push_cycle_state.json"
CYCLE_LOG_PATH = "logs/push_cycles.jsonl"
JOURNAL_PATH = "logs/prompt_journal.jsonl"


def _load_state(root: Path) -> dict:
    p = root / CYCLE_STATE_PATH
    if p.exists():
        try:
            return json.loads(p.read_text("utf-8"))
        except Exception:
            pass
    return {"last_journal_line": 0, "total_cycles": 0, "last_commit": None}


def _save_state(root: Path, state: dict) -> None:
    p = root / CYCLE_STATE_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2) + "\n", "utf-8")


def _load_journal_since(root: Path, after_line: int) -> list[dict]:
    """Load all prompt_journal entries since the last push."""
    p = root / JOURNAL_PATH
    if not p.exists():
        return []
    entries = []
    with open(p, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if i <= after_line or not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return entries


def _extract_operator_signal(entries: list[dict]) -> dict:
    """Aggregate operator signal from all prompts in this push cycle."""
    if not entries:
        return {"prompt_count": 0}
    wpms = [e.get("signals", {}).get("wpm", 0) or e.get("wpm", 0) for e in entries]
    dels = [e.get("signals", {}).get("deletion_ratio", 0) or e.get("deletion_ratio", 0) for e in entries]
    hess = [e.get("signals", {}).get("hesitation_count", 0) for e in entries]
    intents = {}
    for e in entries:
        intent = e.get("intent", "unknown")
        intents[intent] = intents.get(intent, 0) + 1
    module_refs = set()
    for e in entries:
        for m in e.get("module_refs", []):
            module_refs.add(m)
    deleted_words = []
    for e in entries:
        for w in e.get("deleted_words", []):
            if isinstance(w, str):
                deleted_words.append(w)
            elif isinstance(w, dict):
                deleted_words.append(w.get("word", ""))
    states = {}
    for e in entries:
        s = e.get("cognitive_state", "unknown")
        states[s] = states.get(s, 0) + 1
    avg = lambda xs: sum(xs) / len(xs) if xs else 0
    return {
        "prompt_count": len(entries),
        "avg_wpm": round(avg(wpms), 1),
        "avg_deletion": round(avg(dels), 3),
        "total_hesitations": sum(hess),
        "intent_distribution": intents,
        "dominant_intent": max(intents, key=intents.get) if intents else "unknown",
        "module_refs": sorted(module_refs),
        "deleted_words": deleted_words[-20:],
        "cognitive_states": states,
        "dominant_state": max(states, key=states.get) if states else "unknown",
    }


def _extract_copilot_signal(changed_files: list[str]) -> dict:
    """Extract copilot signal from the git diff (files changed = copilot wrote)."""
    py_files = [f for f in changed_files if f.endswith(".py")]
    modules_touched = set()
    for f in py_files:
        stem = Path(f).stem
        # Strip pigeon suffix to get base module name
        parts = stem.split("_seq")
        if parts:
            modules_touched.add(parts[0])
    return {
        "files_changed": len(changed_files),
        "py_files_changed": len(py_files),
        "modules_touched": sorted(modules_touched),
        "non_py_files": [f for f in changed_files if not f.endswith(".py")],
    }


def _compute_sync(operator: dict, copilot: dict) -> dict:
    """Compute sync between operator intent and copilot output.

    Sync = how well did the code changes match what the operator was asking for?
    Since the operator never types code, ALL code is copilot.
    Operator → prompts (intent). Copilot → diffs (output).
    """
    op_modules = set(operator.get("module_refs", []))
    cp_modules = set(copilot.get("modules_touched", []))

    if not op_modules and not cp_modules:
        return {"score": 0.5, "reason": "no module references in either signal"}

    # Module overlap between operator references and copilot changes
    overlap = op_modules & cp_modules
    union = op_modules | cp_modules
    jaccard = len(overlap) / len(union) if union else 0.0

    # Effort ratio — prompts per file changed (lower = more efficient sync)
    prompts = operator.get("prompt_count", 1)
    files = max(copilot.get("py_files_changed", 1), 1)
    effort_ratio = prompts / files

    # Intent alignment — was the operator debugging/building/etc and did code change?
    intent = operator.get("dominant_intent", "unknown")
    intent_bonus = 0.0
    if intent == "debugging" and copilot.get("py_files_changed", 0) > 0:
        intent_bonus = 0.1  # fix intent + actual code change = aligned
    elif intent == "building" and copilot.get("py_files_changed", 0) >= 2:
        intent_bonus = 0.15  # build intent + multiple files = strong alignment
    elif intent == "restructuring" and copilot.get("py_files_changed", 0) >= 3:
        intent_bonus = 0.1  # restructure + many files = aligned

    # Frustration penalty — high deletion/hesitation = poor sync
    frustration_penalty = 0.0
    if operator.get("avg_deletion", 0) > 0.4:
        frustration_penalty = 0.1
    if operator.get("dominant_state") == "frustrated":
        frustration_penalty += 0.05

    sync_score = min(1.0, max(0.0,
        jaccard * 0.5 + intent_bonus + (1.0 / max(effort_ratio, 0.5)) * 0.3 - frustration_penalty
    ))

    return {
        "score": round(sync_score, 3),
        "jaccard": round(jaccard, 3),
        "module_overlap": sorted(overlap),
        "operator_only": sorted(op_modules - cp_modules),
        "copilot_only": sorted(cp_modules - op_modules),
        "effort_ratio": round(effort_ratio, 2),
        "intent_alignment": intent,
        "frustration_penalty": round(frustration_penalty, 3),
    }


def _generate_dual_coaching(operator: dict, copilot: dict, sync: dict) -> dict:
    """Generate coaching for BOTH the operator and the coding agent."""
    operator_tips = []
    agent_tips = []

    # Operator coaching based on their signal
    if operator.get("avg_deletion", 0) > 0.4:
        operator_tips.append("High deletion rate — try articulating intent more clearly before typing. Outline the task first.")
    if operator.get("prompt_count", 0) > 10 and copilot.get("py_files_changed", 0) < 3:
        operator_tips.append("Many prompts, few file changes — consider being more specific about which modules to touch.")
    if sync.get("operator_only"):
        operator_tips.append(f"You referenced {sync['operator_only']} but copilot didn't touch them — be more explicit about expected changes.")
    if operator.get("dominant_state") == "frustrated" and operator.get("prompt_count", 0) > 5:
        operator_tips.append("Frustration detected across multiple prompts — try breaking the task into smaller pushable units.")
    if not operator.get("module_refs"):
        operator_tips.append("No module references detected in prompts — naming specific modules helps copilot target the right files.")

    # Agent coaching based on copilot signal
    if sync.get("copilot_only"):
        agent_tips.append(f"Touched {sync['copilot_only']} without operator reference — confirm intent before modifying unreferenced modules.")
    if sync.get("effort_ratio", 0) > 5:
        agent_tips.append("Operator needed many prompts — respond with more complete implementations to reduce round-trips.")
    if sync.get("score", 0) < 0.3:
        agent_tips.append("Low sync score — operator intent and code output diverged. Ask clarifying questions earlier.")
    if copilot.get("py_files_changed", 0) > 15:
        agent_tips.append("Large blast radius — prefer focused changes. Wide scatter makes it hard for operator to verify.")

    return {
        "operator_coaching": operator_tips or ["Good sync — keep current communication pattern."],
        "agent_coaching": agent_tips or ["Good alignment with operator intent."],
    }


def run_push_cycle(root: Path, commit_hash: str, intent: str,
                   changed_files: list[str]) -> dict[str, Any]:
    """Run one push-based learning cycle. Called by git_plugin post-commit."""
    state = _load_state(root)

    # 1. Collect operator signal (all prompts since last push)
    entries = _load_journal_since(root, state["last_journal_line"])
    operator = _extract_operator_signal(entries)

    # 2. Collect copilot signal (what code changed)
    copilot = _extract_copilot_signal(changed_files)

    # 3. Compute sync
    sync = _compute_sync(operator, copilot)

    # 4. Generate dual coaching
    coaching = _generate_dual_coaching(operator, copilot, sync)

    # 5. Build cycle record
    now = datetime.now(timezone.utc).isoformat()
    total_journal_lines = state["last_journal_line"] + len(entries)
    cycle = {
        "ts": now,
        "commit": commit_hash,
        "intent": intent,
        "cycle_number": state["total_cycles"] + 1,
        "operator_signal": operator,
        "copilot_signal": copilot,
        "sync": sync,
        "coaching": coaching,
    }

    # 6. Append to cycle log
    log_path = root / CYCLE_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(cycle) + "\n")

    # 7. Update state
    state["last_journal_line"] = total_journal_lines
    state["total_cycles"] += 1
    state["last_commit"] = commit_hash
    state["last_sync_score"] = sync["score"]
    state["updated_at"] = now
    _save_state(root, state)

    return cycle
