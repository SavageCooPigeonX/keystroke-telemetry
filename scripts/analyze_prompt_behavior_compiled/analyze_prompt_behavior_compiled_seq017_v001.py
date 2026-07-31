"""analyze_prompt_behavior_compiled_seq017_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _internal_logs(report: dict[str, Any]) -> list[str]:
    logs = [
        "INTERNAL OPERATOR MODEL LOG",
        f"source={report['source']}",
        f"prompts={report['prompt_count']} schema={report['schema']}",
        "",
        "REWARD MODEL",
    ]
    for mode, count in report["behavioral_events"]["reward_mode_counts"][:10]:
        logs.append(f"REWARD mode={mode} count={count}")
    logs.append("")
    logs.append("PUNISHMENT MODEL")
    for mode, count in report["behavioral_events"]["punishment_mode_counts"][:12]:
        logs.append(f"PUNISH mode={mode} count={count}")
    logs.append("")
    logs.append("HIGH-SIGNAL CORRECTION EVENTS")
    for item in report["behavioral_events"]["punishment_events"][:10]:
        logs.append(
            "OBS "
            f"session={item['session_n']} load={item['cognitive_load']} "
            f"fail={','.join(item['inferred_failed_response_style'])} "
            f"themes={','.join(item['themes'][:4])} :: {item['msg']}"
        )
    logs.append("")
    logs.append("HIGH-SIGNAL REWARD EVENTS")
    for item in report["behavioral_events"]["reward_events"][:8]:
        logs.append(
            "OBS "
            f"session={item['session_n']} load={item['cognitive_load']} "
            f"reward={','.join(item['inferred_rewarded_response_style'])} "
            f"themes={','.join(item['themes'][:4])} :: {item['msg']}"
        )
    logs.append("")
    logs.append("CORRECTION CHAINS")
    for chain in report["correction_chains"][:8]:
        logs.append(f"CHAIN {chain['operator_log']}")
    logs.append("")
    logs.append("ROLE MODEL")
    for role, model in report["role_models"].items():
        logs.append(f"ROLE {role}: {model['compiled_role']}")
    return logs
