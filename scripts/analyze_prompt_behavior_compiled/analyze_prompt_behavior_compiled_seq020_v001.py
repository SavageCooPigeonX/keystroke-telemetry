"""analyze_prompt_behavior_compiled_seq020_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import re

def _write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Internal Operator Behavioral Log",
        "",
        f"- schema: `{report['schema']}`",
        f"- prompts analyzed: `{report['prompt_count']}`",
        f"- source: `{report['source']}`",
        "",
        "## Internal Logs",
        "",
        "```text",
        *report["internal_logs"],
        "```",
        "",
        "## Behavioral Model",
        "",
        "### Rewarded Response Styles",
        "",
    ]
    for mode, count in report["behavioral_events"]["reward_mode_counts"][:12]:
        lines.append(f"- `{mode}` count={count}")
    lines += [
        "",
        "### Punished Response Styles",
        "",
    ]
    for mode, count in report["behavioral_events"]["punishment_mode_counts"][:14]:
        lines.append(f"- `{mode}` count={count}")
    lines += [
        "",
        "### High-Signal Punishment Events",
        "",
    ]
    for item in report["behavioral_events"]["punishment_events"][:14]:
        lines.append(
            f"- session `{item['session_n']}` load={item['cognitive_load']} "
            f"fail={item['inferred_failed_response_style']} :: {item['msg']}"
        )
    lines += [
        "",
        "### High-Signal Reward Events",
        "",
    ]
    for item in report["behavioral_events"]["reward_events"][:12]:
        lines.append(
            f"- session `{item['session_n']}` load={item['cognitive_load']} "
            f"reward={item['inferred_rewarded_response_style']} :: {item['msg']}"
        )
    lines += [
        "",
        "## Correction Chains",
        "",
    ]
    for chain in report["correction_chains"][:12]:
        lines.append(f"- {chain['operator_log']}")
    lines += [
        "",
        "## Role Model",
        "",
    ]
    for role, model in report["role_models"].items():
        lines.append(f"- `{role}`: {model['compiled_role']}")
    lines += [
        "",
        "## Theme Reinforcement",
        "",
    ]
    for theme, stats in sorted(report["theme_reinforcement"].items(), key=lambda kv: kv[1]["negative"], reverse=True):
        lines.append(
            f"- `{theme}` total={stats['total']} positive={stats['positive']} "
            f"negative={stats['negative']} mixed={stats['mixed']} neutral={stats['neutral']}"
        )
    lines += ["", "## Shift Points", ""]
    for item in report["shift_points"]:
        lines.append(
            f"- session `{item['at_session']}` load_delta={item['load_delta']} "
            f"themes={item['top_theme_delta']} :: {item['msg']}"
        )
    lines += ["", "## Emergent Threads", ""]
    for thread in report["emergent_threads"][:12]:
        lines.append(
            f"- `{thread['term']}` count={thread['count']} sessions={thread['first_session']}..{thread['last_session']} "
            f":: {thread['compiled_bridge']}"
        )
    lines += ["", "## DeepSeek Research Prompt", "", "```text", report["deepseek_prompt"], "```", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
