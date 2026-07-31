"""analyze_prompt_behavior_compiled_seq018_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import json
import re

def _deepseek_prompt(report: dict[str, Any]) -> str:
    compact = {
        "daily": report["daily"][-10:],
        "theme_reinforcement": {
            k: {kk: vv for kk, vv in v.items() if kk != "examples"}
            for k, v in report["theme_reinforcement"].items()
        },
        "shift_points": report["shift_points"],
        "emergent_threads": report["emergent_threads"][:10],
        "graph_edges": report["cooccurrence_graph"]["top_edges"][:12],
        "behavioral_events": {
            "punishment_mode_counts": report["behavioral_events"]["punishment_mode_counts"][:12],
            "reward_mode_counts": report["behavioral_events"]["reward_mode_counts"][:10],
            "punishment_events": report["behavioral_events"]["punishment_events"][:12],
            "reward_events": report["behavioral_events"]["reward_events"][:8],
        },
        "correction_chains": report["correction_chains"][:10],
        "role_models": report["role_models"],
        "internal_log_excerpt": report.get("internal_logs", [])[:60],
    }
    return (
        "You are DeepSeek acting as a cognitive-behavior research auditor for a local prompt journal.\n"
        "Research and reason about cognitive effects of response styles, especially how responses can either "
        "amplify an operator's exploratory cognition or collapse it into frustration.\n\n"
        "Write this like internal product/behavior logs on an operator, not a public-facing empathy essay. "
        "Do not give generic therapy language. Connect the telemetry to concrete response-style mechanisms: "
        "cognitive load, autonomy support, validation vs over-agreement, premature task closure, curiosity, "
        "repair after misattunement, and long-horizon thought scaffolding.\n\n"
        "Use this behavioral analysis artifact:\n"
        f"{json.dumps(compact, indent=2)}\n\n"
        "Required output:\n"
        "1. Identify the response styles that appear positively reinforced.\n"
        "2. Identify response styles that appear negatively reinforced.\n"
        "3. Explain the most likely cognitive shift points.\n"
        "4. Extract the hidden thing the operator is looking for.\n"
        "5. Propose a response policy for future Codex/Claude/DeepSeek roles.\n"
        "6. Emit 12 internal-log style rules that the assistant should follow when this operator is frustrated.\n"
    )
