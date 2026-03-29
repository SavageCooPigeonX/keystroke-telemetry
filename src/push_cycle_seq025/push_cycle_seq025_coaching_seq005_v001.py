"""push_cycle_seq025_coaching_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

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
