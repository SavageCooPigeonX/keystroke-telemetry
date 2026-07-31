"""opus_orchestrator_runtime_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any

def render_opus_runtime(runtime: dict[str, Any]) -> str:
    lines = ["# Opus Orchestrator Runtime", "", f"- prompt: {runtime.get('operator_prompt', '')}"]
    hush = runtime.get("hush_intent_runtime") or {}
    lines.append(f"- Hush repo: `{hush.get('active_repo')}` fence `{hush.get('mutation_fence')}`")
    lines.append(f"- context confidence: `{(runtime.get('gemini_context') or {}).get('confidence')}`")
    lines.extend(["", "## Last 3 Prompts"])
    for row in runtime.get("last_three_prompts") or []:
        lines.append(f"- `{row.get('session_n')}` {row.get('intent')} / {row.get('state')}: {row.get('preview')}")
    lines.extend(["", "## File Subagents"])
    for agent in runtime.get("file_subagents") or []:
        lines.append(f"- `{agent['file']}` {agent['readiness']} via {agent['gemini']} + {agent['deepseek_job']}")
    for packet in runtime.get("hush_file_packets") or []:
        lines.append(f"- Hush `{packet.get('file_identity')}` {packet.get('operator_display_name')} -> {packet.get('current_responsibility')}")
    lines.extend(["", "## Artifact Memory"])
    memory = runtime.get("artifact_memory") or {}
    lines.append(f"- compiler probe: `{memory.get('compiler_status')}`")
    lines.append(f"- training pairs: `{memory.get('training_pair_status')}`")
    for file in memory.get("high_touch_files") or []:
        lines.append(f"- hot: `{file}`")
    lines.extend(["", "## Coding Area Memory"])
    coding = runtime.get("coding_area_memory") or {}
    lines.append(f"- jobs proposed: `{coding.get('job_count')}`")
    for file in coding.get("top_files") or []:
        lines.append(f"- search: `{file}`")
    lines.extend(["", "## Training Pair Debug"])
    debug = runtime.get("training_pair_debug") or {}
    lines.append(f"- status: `{debug.get('status')}`")
    lines.append(f"- recommended: {debug.get('recommended_fix', '')}")
    box = runtime.get("opus_prompt_box") or {}
    lines.extend(["", "## Opus Prompt Box"])
    lines.append(f"- open: `{box.get('open_count', 0)}` / `{box.get('max_open', 20)}`")
    lines.append(f"- dropped: `{box.get('dropped_count', 0)}`")
    for row in box.get("top_open") or []:
        lines.append(f"- `{row.get('id')}` {row.get('intent_key')} score={row.get('priority_score')}")
    macro = runtime.get("session_macro_cycle") or {}
    lines.extend(["", "## Session Macro Cycle"])
    lines.append(f"- status: `{macro.get('status')}`")
    lines.append(f"- read: {macro.get('macro_read', '')}")
    for cycle in macro.get("cycles") or []:
        lines.append(f"- `{cycle.get('cycle_id')}` {cycle.get('status')} prompts `{cycle.get('prompt_count')}`")
    manifest_cycle = runtime.get("manifest_state_write_cycle") or {}
    lines.extend(["", "## Manifest State Write Cycle"])
    lines.append(f"- status: `{manifest_cycle.get('status')}`")
    for row in manifest_cycle.get("file_writes") or []:
        lines.append(f"- `{row.get('file')}` -> `{row.get('manifest')}` changed={row.get('changed')}")
    coupling = runtime.get("folder_context_coupling") or {}
    lines.extend(["", "## Folder Context Coupling"])
    lines.append(f"- status: `{coupling.get('status')}`")
    for row in coupling.get("folders") or []:
        lines.append(f"- `{row.get('folder')}` autonomy={row.get('autonomy_score')} resistance={row.get('resistance_score')} mode={row.get('recommended_mode')}")
    lines.extend(["", "## Work Completed"])
    for item in runtime.get("work_completed") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Manifest Write", runtime.get("manifest_write", {}).get("markdown", "")])
    return "\n".join(lines) + "\n"
