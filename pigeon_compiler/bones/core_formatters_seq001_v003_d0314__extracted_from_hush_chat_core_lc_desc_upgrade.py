"""pigeon_compiler/bones/core_formatters_seq001_v001.py

BONE MODULE — Extracted from hush_chat_core_seq001_v001.py (v4.9.13)
Origin: Lines 1655-1790. All dated 2026-02-13 to 2026-02-24 (stable).

Reply sanitizer, continuation anchor, context warnings.
Deterministic string operations — zero LLM calls.
"""
import re
import logging

logger = logging.getLogger('hush')


def sanitize_reply(reply: str) -> str:
    """Strip internal pipeline markers from DeepSeek reply before display.

    Removes: ---THINK---/---REPLY--- markers, GUIDANCE keywords,
    CONTEXT_SELECT blocks, stray XML-like tags.
    """
    if not reply:
        return reply

    # v4.7.0: Quick path — most replies have no markers
    reply_upper = reply.upper()
    has_markers = any(m in reply_upper for m in (
        '---THINK', '---REPLY', '---GUIDANCE', '---CONTEXT_SELECT',
        '<CONTEXT_SELECT', '</CONTEXT_SELECT',
    ))

    if not has_markers:
        # Still check for GUIDANCE keywords
        _GUIDANCE_KEYWORDS = (
            'WRITE_SHARDS:', 'WRITE_HINTS:', 'NEXT_LOAD:', 'REMEMBER:',
            'CONTEXT_SWITCH:', 'DROP_PREFETCH:', 'PB_STATE:', 'PB_COMPLETE:',
            'CORRECT_SHARD:', 'WORKFLOW_CONTEXT:', 'GUIDANCE:',
        )
        if not any(kw in reply_upper for kw in _GUIDANCE_KEYWORDS):
            return reply.strip() or reply

    # Strip block markers
    reply = re.sub(r'-{2,}\s*(?:THINK|REPLY|GUIDANCE|CONTEXT_SELECT)\s*-{2,}\s*', '', reply, flags=re.IGNORECASE)

    # Strip GUIDANCE keyword lines
    _GUIDANCE_KEYWORDS = (
        'WRITE_SHARDS:', 'WRITE_HINTS:', 'NEXT_LOAD:', 'REMEMBER:',
        'CONTEXT_SWITCH:', 'DROP_PREFETCH:', 'PB_STATE:', 'PB_COMPLETE:',
        'CORRECT_SHARD:', 'WORKFLOW_CONTEXT:', 'GUIDANCE:',
    )
    lines = reply.split('\n')
    cleaned = []
    for line in lines:
        line_upper = line.strip().upper()
        if any(line_upper.startswith(kw) for kw in _GUIDANCE_KEYWORDS):
            continue
        cleaned.append(line)
    reply = '\n'.join(cleaned)

    # Strip XML context_select blocks
    reply = re.sub(
        r'<CONTEXT_SELECT>.*?</CONTEXT_SELECT>',
        '', reply, flags=re.DOTALL | re.IGNORECASE,
    )

    # Collapse multiple blank lines
    reply = re.sub(r'\n{3,}', '\n\n', reply)

    return reply.strip() or reply


def inject_continuation_anchor(message: str, session: dict):
    """Inject continuation anchor — tells DeepSeek this is a follow-up.

    If the user's message is very short and the session has prior conversation,
    inject a system message that establishes continuity.
    """
    if not message or len(message) > 100:
        return

    msgs = session.get('messages', [])
    if len(msgs) < 4:
        return

    # Look for a recent assistant message to reference
    for m in reversed(msgs[-6:]):
        if m.get('role') == 'assistant':
            preview = m.get('content', '')[:200]
            if preview:
                session['messages'].append({
                    "role": "system",
                    "content": (
                        f"[CONTINUATION — operator is responding to your last message]\n"
                        f"Your last response started: \"{preview[:150]}...\"\n"
                        f"Operator says: \"{message}\"\n"
                        f"ACTION: Continue naturally from your last response."
                    ),
                })
                return


def inject_context_warning(session, session_id, ctx_tokens, ctx_pct, model_context_tokens):
    """Inject context overflow warning if needed. Returns warning level."""
    if ctx_pct > 80:
        session['messages'].append({
            "role": "system",
            "content": (
                "[⚠️ CONTEXT OVERFLOW WARNING — RED ZONE]\n"
                f"Current usage: {ctx_tokens:,}/{model_context_tokens:,} tokens ({ctx_pct:.1f}%)\n"
                "ACTION: Shorten responses. Offer to archive conversation."
            ),
        })
        return 'red'
    elif ctx_pct > 60:
        session['messages'].append({
            "role": "system",
            "content": (
                "[⚠️ CONTEXT WINDOW — YELLOW ZONE]\n"
                f"Current usage: {ctx_tokens:,}/{model_context_tokens:,} tokens ({ctx_pct:.1f}%)\n"
                "ACTION: Be concise. Prioritize new information."
            ),
        })
        return 'yellow'
    return None


def log_prompt_diag(session_id, session, message, tool_result, prefetch_was_injected):
    """Log prompt diagnostics — message counts, sizes, injection status."""
    msgs = session.get('messages', [])
    sys_count = sum(1 for m in msgs if m.get('role') == 'system')
    usr_count = sum(1 for m in msgs if m.get('role') == 'user')
    ast_count = sum(1 for m in msgs if m.get('role') == 'assistant')
    total_chars = sum(len(m.get('content', '')) for m in msgs)
    logger.info(
        f"[{session_id}] PROMPT DIAG: {len(msgs)} msgs "
        f"(sys={sys_count} usr={usr_count} ast={ast_count}) "
        f"chars={total_chars:,} tool={'yes' if tool_result.get('intel') else 'no'} "
        f"prefetch={'yes' if prefetch_was_injected else 'no'} "
        f"msg='{message[:50]}'"
    )
