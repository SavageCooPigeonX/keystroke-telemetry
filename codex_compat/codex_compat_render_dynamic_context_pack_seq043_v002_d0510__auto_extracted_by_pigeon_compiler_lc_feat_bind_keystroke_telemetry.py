"""codex_compat_render_dynamic_context_pack_seq043_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 043 | VER: v002 | 198 lines | ~2,316 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from typing import Any
import os
import re

def _render_dynamic_context_pack(pack: dict[str, Any], managed: bool = False) -> str:
    lines: list[str] = []
    if managed:
        lines.append("<!-- codex:dynamic-context-pack -->")
    lines.extend([
        "## Dynamic Context Pack",
        "",
        f"*Prepared {pack.get('ts', '')} for {pack.get('surface', 'unknown')}*",
        "",
        f"**PROMPT:** `{str(pack.get('prompt') or '')[:240]}`",
    ])

    signals = pack.get("signals") or {}
    lines.extend([
        f"**DELETION_RATIO:** `{signals.get('deletion_ratio', 0)}`",
        f"**INTENT_DELETION_RATIO:** `{signals.get('intent_deletion_ratio', 0)}`",
        f"**HESITATION_COUNT:** `{signals.get('hesitation_count', 0)}`",
        f"**COGNITIVE_STATE:** `{signals.get('cognitive_state') or 'unknown'}`",
        f"**DELETED_WORDS:** {', '.join(signals.get('deleted_words') or []) or 'none'}",
        "",
        "**FOCUS_FILES:**",
    ])
    focus_files = pack.get("focus_files") or []
    if focus_files:
        for item in focus_files[:10]:
            score = item.get("score")
            score_text = f" score={score}" if score is not None else ""
            reason = item.get("reason", "context")
            lines.append(f"- `{item.get('name', '?')}` via {reason}{score_text}")
    else:
        lines.append("- none")

    mira = pack.get("mira") or {}
    if isinstance(mira, dict) and mira:
        repo = mira.get("repo_classification") if isinstance(mira.get("repo_classification"), dict) else {}
        authority = mira.get("runtime_authority") if isinstance(mira.get("runtime_authority"), dict) else {}
        lines.extend([
            "",
            "**MIRA_RUNTIME:**",
            f"- name: `{mira.get('name', 'MIRA')}` role `{mira.get('role', 'unknown')}`",
            f"- loop: `{ ' -> '.join(mira.get('loop') or []) or 'Map -> Infer -> Reconstruct -> Align' }`",
            f"- repo: `{repo.get('active_repo', 'unknown')}` confidence `{repo.get('repo_confidence', 0)}`",
            f"- fence: `{authority.get('mutation_fence', 'unknown')}` mode `{authority.get('mode', 'unknown')}`",
            f"- source mutation allowed: `{authority.get('source_mutation_allowed', False)}`",
        ])
        entities = mira.get("entity_sim") if isinstance(mira.get("entity_sim"), list) else []
        for entity in entities[:4]:
            lines.append(
                f"- entity sim: `{entity.get('entity_id')}` status `{entity.get('sim_state')}` "
                f"privacy `{entity.get('privacy')}`"
            )
        probe = mira.get("intent_probe_capability") if isinstance(mira.get("intent_probe_capability"), dict) else {}
        if probe:
            lines.append(f"- MIRA probe capability: `{probe.get('status')}` egress `{probe.get('egress')}`")

    hush = pack.get("hush") or {}
    if isinstance(hush, dict) and hush:
        lines.extend([
            "",
            "**HUSH_FRONTEND:**",
            f"- surface: `{hush.get('surface', 'myaifingerprint.com')}`",
            f"- intent: `{hush.get('frontend_intent', 'maif_information')}`",
            f"- cards: `{len(hush.get('frontend_cards') or [])}`",
        ])

    self_knowledge = pack.get("file_self_knowledge") or {}
    if isinstance(self_knowledge, dict) and self_knowledge.get("packets"):
        lines.extend([
            "",
            "**FILE_SELF_KNOWLEDGE:**",
            f"- read: {str(self_knowledge.get('operator_read') or '')[:260]}",
        ])
        for packet in (self_knowledge.get("packets") or [])[:5]:
            scope = packet.get("mutation_scope") or {}
            owns = ", ".join(packet.get("owns") or [])[:120] or "unknown"
            lines.append(
                f"- `{packet.get('file')}` owns `{owns}` readiness `{scope.get('readiness')}`"
            )
            validates = packet.get("validates_with") or []
            if validates:
                lines.append(f"  - validates: `{validates[0]}`")
            quote = packet.get("file_quote")
            if quote:
                lines.append(f"  - says: {quote}")

    context = pack.get("context_selection") or {}
    lines.extend([
        "",
        f"**CONTEXT_CONFIDENCE:** `{context.get('confidence', 0)}`",
        f"**CONTEXT_STATUS:** `{context.get('status', 'unknown')}`",
        "",
        "**UNRESOLVED_INTENTS:**",
    ])
    unresolved = pack.get("unresolved_intents") or []
    if unresolved:
        for item in unresolved[:4]:
            lines.append(f"- `{item.get('status', '?')}` {str(item.get('text') or '')[:160]}")
    else:
        lines.append("- none")

    brain = pack.get("prompt_brain") or {}
    if brain:
        semantic = brain.get("semantic_profile") or {}
        lines.extend([
            "",
            "**PROMPT_BRAIN:**",
            f"- intent key: `{brain.get('intent_key') or 'none'}`",
            f"- semantic: `{', '.join(semantic.get('semantic_intents') or []) or 'none'}`",
            f"- profile hint: `{semantic.get('completion_hint') or 'none'}`",
            f"- prompt box open: `{(brain.get('prompt_box') or {}).get('open_count', 0)}`",
        ])

    policy = pack.get("operator_response_policy") or {}
    if isinstance(policy, dict) and policy:
        lines.extend([
            "",
            "**OPERATOR_RESPONSE_POLICY:**",
            f"- active arm: `{policy.get('active_arm', 'unknown')}`",
            f"- operator read: {str(policy.get('operator_read') or '')[:220]}",
            f"- required sections: `{', '.join(policy.get('required_sections') or [])}`",
            f"- next mutation: {str(policy.get('next_mutation') or '')[:220]}",
        ])
        for move in (policy.get("intent_moves") or [])[:5]:
            lines.append(f"- intent move: `{move.get('intent_key', 'none')}`")
        for item in (policy.get("probe_files") or [])[:6]:
            lines.append(f"- probe file: `{item.get('file')}` via {item.get('reason', 'policy')}")
        comments = policy.get("file_comments") if isinstance(policy.get("file_comments"), list) else []
        if comments:
            lines.append("**FILE_COMMENTS_SYNTH:**")
            for comment in comments[:8]:
                lines.append(
                    f"- `{comment.get('file')}` says `{str(comment.get('file_signal') or '')[:100]}`; "
                    f"{str(comment.get('file_fix_proposal') or '')[:140]}; grader `{(comment.get('fix_grade') or {}).get('decision', 'unknown')}`; "
                    f"backward `{(comment.get('backward_pass_learning') or {}).get('path_family', 'unknown')}`"
                )
        audit = policy.get("deepseek_response_policy_audit") if isinstance(policy.get("deepseek_response_policy_audit"), dict) else {}
        if audit:
            lines.append(f"- DeepSeek response policy audit: `{audit.get('should_make_response_policy', False)}` {str(audit.get('reason') or '')[:180]}")

    opus = pack.get("opus_instruction_layer") or {}
    if isinstance(opus, dict) and opus:
        contract = opus.get("response_contract") or {}
        lines.extend([
            "",
            "**OPUS_INSTRUCTION_LAYER:**",
            f"- status: `{opus.get('status', 'unknown')}` fires_for_prompt `{opus.get('fires_for_prompt', False)}`",
            f"- manager: `{opus.get('manager', 'opus')}` role `{opus.get('role', '')}`",
            f"- file comments required: `{contract.get('file_comments_required', False)}` section `{contract.get('section_name', 'File Comments')}`",
            f"- response format: {str(contract.get('format') or '')[:220]}",
        ])
        selected = opus.get("selected_files") if isinstance(opus.get("selected_files"), list) else []
        if selected:
            lines.append("**OPUS_SELECTED_FILE_COMMENTS:**")
            for item in selected[:8]:
                lines.append(f"- `{item.get('file')}`: {str(item.get('residue_comment') or '')[:220]}")
        else:
            lines.append("**OPUS_SELECTED_FILE_COMMENTS:** none")

    file_sim = pack.get("file_sim") or {}
    if file_sim:
        proposals = file_sim.get("proposals") or []
        lines.extend([
            "",
            "**FILE_SIM:**",
            f"- status: `{file_sim.get('status', 'unknown')}`",
            f"- target state: `{file_sim.get('target_state', 'unknown')}`",
            f"- trigger: `{file_sim.get('trigger', 'unknown')}`",
        ])
        for proposal in proposals[:5]:
            lines.append(
                f"- `{proposal.get('path')}` interlink={proposal.get('interlink_score')} "
                f"decision={proposal.get('decision')}"
            )

    intent_loop = pack.get("intent_loop") or {}
    if intent_loop:
        lines.extend([
            "",
            "**INTENT_LOOP:**",
            f"- loop: `{intent_loop.get('loop_id', 'none')}` status `{intent_loop.get('status', 'unknown')}`",
            f"- intent: `{intent_loop.get('intent_key', 'none')}`",
            f"- human: `{intent_loop.get('human_position', 'on_loop')}` approval_required `{intent_loop.get('approval_required', True)}`",
            f"- observed edits: `{len(intent_loop.get('observed_edits') or [])}` responses: `{len(intent_loop.get('observed_responses') or [])}`",
        ])
        for action in (intent_loop.get("next_actions") or [])[:3]:
            lines.append(f"- next: {action}")

    activity = pack.get("surface_activity") or {}
    switch = activity.get("latest_context_switch") or {}
    lines.extend([
        "",
        "**SURFACE_ACTIVITY:**",
        f"- latest key surface: `{activity.get('latest_key_surface') or 'unknown'}`",
        f"- latest key context: `{activity.get('latest_key_context') or 'unknown'}`",
        f"- latest UIA context: `{activity.get('latest_uia_context') or 'unknown'}`",
    ])
    if switch:
        lines.append(f"- latest context switch: `{switch.get('from')}` -> `{switch.get('to')}`")

    entropy = pack.get("entropy") or {}
    if entropy.get("status") == "ok":
        lines.extend([
            "",
            f"**ENTROPY:** global H `{entropy.get('global_avg_entropy')}`, tracked `{entropy.get('tracked_modules')}`",
        ])

    deepseek = pack.get("deepseek_job") or {}
    if isinstance(deepseek, dict) and deepseek:
        lines.extend([
            "",
            "**DEEPSEEK_V4:**",
            f"- model: `{deepseek.get('model')}`",
            f"- job: `{deepseek.get('job_id')}` status `{deepseek.get('status')}`",
            f"- autonomous write: `{deepseek.get('autonomous_write', False)}`",
        ])

    boundaries = pack.get("capture_boundaries") or {}
    if boundaries:
        lines.extend(["", "**CAPTURE_BOUNDARY:**"])
        lines.append(f"- composer: {boundaries.get('composer')}")
        lines.append(f"- Codex native chat: {boundaries.get('codex_native_chat')}")
        lines.append(f"- screenshot context: {boundaries.get('screenshot_context')}")

    if managed:
        lines.append("<!-- /codex:dynamic-context-pack -->")
    return "\n".join(line.rstrip() for line in lines)
