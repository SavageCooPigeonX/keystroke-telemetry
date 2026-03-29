"""push_cycle_seq025_sync_decomposed_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

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
