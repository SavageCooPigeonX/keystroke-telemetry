"""analyze_prompt_behavior_compiled_seq016_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import PromptRow
from collections import Counter, defaultdict
from typing import Any
import re

def _role_models(rows: list[PromptRow]) -> dict[str, Any]:
    roles = {
        "codex": r"\b(codex|copilot|chat gpt|gpt)\b",
        "claude_opus": r"\b(claude|opus)\b",
        "deepseek": r"\bdeepseek\b",
        "grok": r"\bgrok\b",
    }
    out: dict[str, Any] = {}
    for role, pattern in roles.items():
        hits = [row for row in rows if re.search(pattern, row.msg, re.I)]
        if not hits:
            continue
        out[role] = {
            "mentions": len(hits),
            "reinforcement": dict(Counter(row.reinforcement for row in hits)),
            "dominant_themes": Counter(t for row in hits for t in row.themes).most_common(8),
            "positive_contexts": [
                {"session_n": row.session_n, "msg": row.msg[:260]}
                for row in hits
                if row.reinforcement == "positive"
            ][:8],
            "negative_contexts": [
                {"session_n": row.session_n, "msg": row.msg[:260]}
                for row in hits
                if row.reinforcement in {"negative", "negative_soft", "mixed"}
            ][:10],
            "compiled_role": _compile_role(role, hits),
        }
    return out


def _compile_role(role: str, hits: list[PromptRow]) -> str:
    text = " ".join(row.msg.lower() for row in hits)
    if role == "codex":
        if "operator prober" in text or "probe" in text:
            return "Codex is being shaped as operator probe, prompt-capture surface, and execution harness; it is punished when it behaves like a generic answerer."
        return "Codex is primarily evaluated as the live interface between operator intent, code context, and execution."
    if role == "claude_opus":
        return "Claude/Opus is repeatedly pulled toward long-horizon orchestration, grader behavior, subagent runtime, and stateful thought holding; adapter failures get punished."
    if role == "deepseek":
        return "DeepSeek is framed as compiler/hands: run consensus, write bounded artifacts, repair schemas, and execute after the probe/orchestrator has clarified intent."
    if role == "grok":
        return "Grok is framed as retrieval/probe intelligence: void search, artifact extraction, entity expansion, and network discovery."
    return "Role unresolved."
