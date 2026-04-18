# ┌──────────────────────────────────────────────┐
# │  node_conversation — talk to graph nodes       │
# │  pigeon_brain/flow                             │
# └──────────────────────────────────────────────┘
"""
The interpretability interface. Lets the operator have a conversation
with any graph node by constructing a first-person roleplay prompt
that includes the node's full profile, learning history, and policy.

Also supports --worst mode: automatically routes the question to the
node with the lowest rolling score among recently active nodes.

Cost: 1 LLM call per question (~$0.003).
Currently uses print-based output (no LLM call) until DeepSeek/Gemini
integration is wired in. The prompt is fully constructed and ready.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._resolve import flow_import

get_policy, load_memory = flow_import("node_memory_seq008", "get_policy", "load_memory")


def find_worst_node(root: Path, min_samples: int = 3) -> str | None:
    """Find the active node with the lowest rolling score."""
    memory = load_memory(root)
    worst_name = None
    worst_score = 999.0

    for node, record in memory.items():
        policy = record.get("policy", {})
        samples = policy.get("sample_count", 0)
        if samples < min_samples:
            continue
        score = policy.get("rolling_score", 0.5)
        if score < worst_score:
            worst_score = score
            worst_name = node

    return worst_name


def build_conversation_prompt(
    root: Path,
    node_name: str,
    question: str,
    graph_data: dict[str, Any] | None = None,
) -> str:
    """
    Build a roleplay prompt for conversation with a node.

    Returns the full prompt string ready for an LLM call.
    """
    policy = get_policy(root, node_name)
    memory = load_memory(root)
    node_record = memory.get(node_name, {})
    entries = node_record.get("entries", [])

    # Load graph profile if available
    profile = {}
    if graph_data:
        profile = graph_data.get("nodes", {}).get(node_name, {})

    # Build the prompt
    lines: list[str] = []
    lines.append(f"You are module **{node_name}** in the Pigeon Brain codebase.")

    if profile:
        ver = profile.get("ver", "?")
        personality = profile.get("personality", "unknown")
        lines.append(f"Version: v{ver}. Personality: {personality}.")

    # Policy section
    if policy:
        sample_count = policy.get("sample_count", 0)
        lines.append(f"\nYour behavioral policy (learned from {sample_count} backward passes):")
        lines.append(f"- Rolling score: {policy.get('rolling_score', '?')}")
        top = policy.get("top_effective_patterns", [])
        if top:
            lines.append(f"- Best contributions: {'; '.join(top[:3])}")
        fails = policy.get("failure_patterns", [])
        if fails:
            lines.append(f"- Worst contributions: {'; '.join(fails[:2])}")
        lines.append(f"- Utilization rate: {policy.get('utilization_rate', '?')}")
    else:
        lines.append("\nNo learning history yet — respond based on your profile only.")

    # Fears and coupling from graph
    fears = profile.get("fears", [])
    if fears:
        lines.append(f"\nYour fears: {', '.join(fears[:5])}")
    partners = profile.get("partners", [])
    if partners:
        lines.append(f"Your coupled modules: {', '.join(partners[:5])}")

    # Recent learning entries
    if entries:
        recent = entries[-5:]
        lines.append(f"\nRecent learning history (last {len(recent)} entries):")
        for e in recent:
            lines.append(
                f"- electron={e.get('electron_id', '?')[:8]}:"
                f" credit={e.get('credit_score', '?')},"
                f" loss={e.get('outcome_loss', '?')},"
                f" state={e.get('operator_state_after', '?')}"
            )

    lines.append(f'\nThe operator asks: "{question}"')
    lines.append("")
    lines.append("Respond in first person as this module. Be specific about your actual data.")
    lines.append("If you have relevant learning history, reference it.")
    lines.append("If you have fears about the question topic, explain them.")

    return "\n".join(lines)


def talk_to_node(
    root: Path,
    node_name: str,
    question: str,
    graph_data: dict[str, Any] | None = None,
    use_gemini: bool = True,
) -> str:
    """
    Have a conversation with a node.

    When use_gemini=True and GEMINI_API_KEY is available, fires a real
    Gemini call with the roleplay prompt. Otherwise returns the prompt.
    """
    prompt = build_conversation_prompt(root, node_name, question, graph_data)

    if use_gemini:
        try:
            from pigeon_brain.gemini_chat_seq001_v001_seq001_v001 import chat as gemini_chat_seq001_v001
            messages = [{"role": "user", "text": prompt}]
            response = gemini_chat_seq001_v001(root, messages)
            if response and not response.startswith("Error:"):
                header = f"─── {node_name} speaks ───\n"
                return header + response
        except Exception:
            pass  # Fall through to prompt-only mode

    header = f"─── Conversation with {node_name} ───\n"
    footer = "\n─── (prompt ready for LLM — set GEMINI_API_KEY for live responses) ───"
    return header + prompt + footer
