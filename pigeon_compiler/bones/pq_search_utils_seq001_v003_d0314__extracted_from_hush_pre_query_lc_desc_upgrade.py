"""pigeon_compiler/bones/pq_search_utils_seq001_v001.py

BONE MODULE — Extracted from hush_pre_query_seq001_v001.py (v4.9.13)
Origin: Lines 155-619, last modified 2026-02-14 (manifest utils, stats, formatters)
        Lines 1343-1453 (hot triggers, last modified 2026-02-24/03-01)

Search utilities: pronoun resolver, query optimizer, session stats,
guidance formatter, hot triggers. All deterministic — zero LLM calls.
"""
import re
import logging

logger = logging.getLogger('hush')

# ── Pronoun detection regex ──
_SEARCH_PRONOUNS = re.compile(
    r'\b(his|her|their|its|him|them)\b',
    re.IGNORECASE,
)

_PRONOUN_FP = re.compile(
    r'\b(?:history|histogram|hiss|hire|herself|himself|themselves|itself|herbal|heritage|hero|heroin|heroic|historic|historical)\b',
    re.IGNORECASE,
)

# ── Search query optimization constants ──
SEARCH_STRIP_PREFIXES = [
    'can you', 'could you', 'please', 'i want to', 'i need to',
    'i want you to', 'help me', 'go ahead and', "let's", 'try to',
    'i would like to', "i'd like to", 'maybe', 'just', 'hey', 'hi', 'yo',
]

SEARCH_STRIP_VERBS = [
    'google', 'search', 'search for', 'look up', 'look into',
    'find out about', 'find info on', 'find information on',
    'find out', 'find', 'look for', 'search up', 'get info on',
    'pull up', 'check out', 'research',
]

SEARCH_STRIP_SUFFIXES = [
    'for me', 'real quick', 'right now', 'asap', 'please',
    'if you can', 'when you get a chance', 'thanks', 'thx',
]


def resolve_search_entity(session: dict | None) -> str:
    """Extract most recently discussed entity name from session context.

    Resolution priority:
      1. _grok_flagged_entities
      2. sim_entity
      3. _last_entity_list
      4. Recent JOB submissions
      5. Recent user/assistant messages — proper nouns
    """
    if not session:
        return ''

    grok = session.get('_grok_flagged_entities', [])
    if grok:
        name = grok[-1].get('name', '')
        if name:
            return name

    sim = session.get('sim_entity')
    if sim:
        return sim

    el = session.get('_last_entity_list', [])
    if el:
        last = el[-1]
        if isinstance(last, dict):
            return last.get('name', last.get('entity_name', ''))
        return str(last)

    jobs = session.get('_submitted_jobs', [])
    if jobs:
        return jobs[-1].get('entity_name', '')

    _FP = {
        'Good Morning', 'Good Evening', 'Good Night', 'Thank You',
        'Williams Lake', 'New York', 'British Columbia', 'Dream Mode',
        'Context Select', 'Shard Recall', 'Deep Recall', 'Search For',
        'Project Gtfo', 'Live Debug', 'Pipeline Telemetry', 'Write Hints',
        'Context Pre', 'Real Data', 'Prompt Box', 'Hush Loop',
    }

    for m in reversed(session.get('messages', [])[-20:]):
        if m.get('role') != 'user':
            continue
        c = m.get('content', '')
        if not c or len(c) < 5 or c.startswith('/'):
            continue
        names = re.findall(
            r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+)\b', c
        )
        for n in names:
            if n not in _FP and len(n) > 4:
                return n

    for m in reversed(session.get('messages', [])[-12:]):
        if m.get('role') != 'assistant':
            continue
        c = m.get('content', '')
        if not c or len(c) < 10:
            continue
        names = re.findall(
            r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+)\b', c
        )
        for n in names:
            if n not in _FP and len(n) > 4:
                return n

    return ''


def resolve_search_pronouns(query: str, session: dict | None = None) -> str:
    """Replace unresolved pronouns in a search query with entity context.

    v4.9.9: "his location" + session context [Pete Hegseth]
            → "Pete Hegseth location"
    """
    if not query or not session:
        return query

    if not _SEARCH_PRONOUNS.search(query):
        return query

    if _PRONOUN_FP.search(query):
        stripped = _PRONOUN_FP.sub('', query).strip()
        if not _SEARCH_PRONOUNS.search(stripped):
            return query

    entity_name = resolve_search_entity(session)
    if not entity_name:
        return query

    resolved = re.sub(
        r'\b(?:his|her|their|its)\b',
        entity_name,
        query,
        count=1,
    )

    if resolved == query:
        resolved = re.sub(
            r'\b(?:him|them)\b',
            entity_name,
            query,
            count=1,
        )

    if entity_name.lower() in query.lower():
        return query

    if resolved != query:
        logger.info(
            f"[SEARCH-PRONOUN] Resolved: '{query[:60]}' → '{resolved[:60]}' "
            f"(entity: {entity_name})"
        )

    return resolved


def optimize_search_query(raw_target: str, original_message: str = '') -> str:
    """Deterministic pre-Serper reformatter — strip filler, optimize length."""
    if not raw_target or len(raw_target.strip()) < 2:
        if original_message:
            raw_target = original_message
        else:
            return raw_target

    query = raw_target.strip()
    lower = query.lower()

    for prefix in SEARCH_STRIP_PREFIXES:
        if lower.startswith(prefix + ' '):
            query = query[len(prefix):].strip()
            lower = query.lower()
        elif lower.startswith(prefix):
            query = query[len(prefix):].strip()
            lower = query.lower()

    for verb in sorted(SEARCH_STRIP_VERBS, key=len, reverse=True):
        if lower.startswith(verb + ' '):
            query = query[len(verb):].strip()
            lower = query.lower()
            break

    changed = True
    while changed:
        changed = False
        for suffix in SEARCH_STRIP_SUFFIXES:
            if lower.endswith(' ' + suffix):
                query = query[:-(len(suffix))].strip()
                lower = query.lower()
                changed = True
                break

    query = re.sub(
        r'^(?:the|a|an|about|regarding|concerning|on|of)\s+',
        '', query, flags=re.IGNORECASE,
    ).strip()

    query = re.sub(
        r'\s+(?:about|regarding|concerning)\s+',
        ' ', query, flags=re.IGNORECASE,
    ).strip()

    query = re.sub(
        r'^(?:what (?:is|are|was|were|about)|who (?:is|are|was)|'
        r'how (?:does|do|is|are|to)|where (?:is|are|can)|'
        r'when (?:is|was|did|does|will)|why (?:is|are|did|does))\s+',
        '', query, flags=re.IGNORECASE,
    ).strip()

    if len(query) > 2 and query[0] in ('"', "'") and query[-1] == query[0]:
        query = query[1:-1].strip()

    query = re.sub(r'\s+', ' ', query).strip()

    if len(query) > 80:
        truncated = query[:80].rsplit(' ', 1)[0]
        query = truncated if len(truncated) > 30 else query[:80]

    if len(query.strip()) < 3:
        query = raw_target.strip()[:80]

    return query


def compute_session_stats(session: dict) -> dict:
    """Compute session stats for the context select agent to track."""
    from maif_whisperer.persona.hush_prompt_seq001_v003_d0314__superintelligent_field_intelligence_agent_lc_desc_upgrade import MODEL_CONTEXT_TOKENS
    msgs = session.get('messages', [])
    total_chars = sum(len(m.get('content', '')) for m in msgs)
    sys_chars = len(msgs[0].get('content', '')) if msgs else 0
    conv_chars = total_chars - sys_chars
    est_tokens = total_chars // 4
    return {
        'message_count': session.get('message_count', 0),
        'total_chars': total_chars,
        'system_chars': sys_chars,
        'conversation_chars': conv_chars,
        'est_tokens': est_tokens,
        'est_pct': round((est_tokens / MODEL_CONTEXT_TOKENS) * 100, 1),
        'cost': round(session.get('cost', 0), 4),
        'session_num': session.get('session_num', 1),
        'sim_mode': session.get('sim_mode', False),
        'msg_count': len(msgs),
    }


def format_session_stats(stats: dict) -> str:
    """Format stats for prompt injection."""
    return (
        f"msgs={stats['message_count']} ctx={stats['est_tokens']:,}t ({stats['est_pct']}%) "
        f"cost=${stats['cost']} conv={stats['conversation_chars']:,}c "
        f"sim={'ON' if stats['sim_mode'] else 'off'}"
    )


def format_guidance_block(guidance: dict) -> str:
    """Format guidance tags into a readable block for the guided prompt."""
    lines = []
    if guidance.get('next_load'):
        lines.append(f"NEXT_LOAD: {guidance['next_load']}")
    if guidance.get('write_shards'):
        lines.append(f"WRITE_SHARDS: {', '.join(guidance['write_shards'])}")
    if guidance.get('write_hints'):
        for sid, hint in guidance['write_hints'].items():
            lines.append(f"WRITE_HINT ({sid}): {hint}")
    if guidance.get('remember'):
        lines.append(f"REMEMBER: {', '.join(guidance['remember'])}")
    if guidance.get('context_switch'):
        lines.append(f"PREVIOUS_CONTEXT_SWITCH: {guidance['context_switch']}")
    return "\n".join(lines) if lines else "(no specific guidance)"


def hot_trigger_search_override(message: str, result: dict) -> dict:
    """Override when user explicitly said 'google' but Gemini routed elsewhere."""
    msg_lower = message.lower().strip()
    search_verbs = [
        r'^\s*(?:google|search|look\s*up)\s*(.+)',
        r'^\s*(?:google|search)([a-z].+)',
    ]
    for pat in search_verbs:
        m = re.match(pat, msg_lower)
        if m:
            after = m.group(1).strip()
            if after and len(after) > 1:
                old_tool = result['tool']
                result['tool'] = 'serper_search'
                result['target'] = after[:100]
                result['intent'] = 'search'
                logger.info(
                    f"[HOT-TRIGGER] Search override: '{old_tool}' → serper_search "
                    f"(user said '{msg_lower[:30]}')"
                )
                return result
    return result


def hot_trigger_check(message: str, result: dict) -> dict:
    """HOT TRIGGER fallback — catches tool intent Gemini missed.

    If Gemini returned NONE but the message clearly needs a tool,
    override the routing decision.
    """
    if result.get('tool', 'NONE') != 'NONE':
        return result

    lower = message.lower().strip()

    search_patterns = [
        r'(?:google|search for|look up|search)\s+(.+)',
        r'(?:google|search)([a-z].+)',
    ]
    for pat in search_patterns:
        m = re.match(pat, lower)
        if m:
            target = m.group(1).strip()
            if target and len(target) > 2:
                result['tool'] = 'serper_search'
                result['target'] = target[:100]
                result['intent'] = 'search'
                logger.info(f"[HOT-TRIGGER] Override to serper_search")
                return result

    proper_nouns = re.findall(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+)\b', message)
    fp_nouns = {
        'Good Morning', 'Good Evening', 'Good Night', 'Thank You',
        'Williams Lake', 'New York', 'British Columbia', 'Dream Mode',
    }
    entity_nouns = [n for n in proper_nouns if n not in fp_nouns]
    if entity_nouns and len(lower.split()) <= 8:
        result['tool'] = 'entity_lookup'
        result['target'] = entity_nouns[0]
        result['intent'] = 'entity'
        logger.info(f"[HOT-TRIGGER] Override to entity_lookup")
        return result

    job_patterns = [
        r'(?:check|show|list|view|see)\s+(?:my\s+)?(?:jobs?|queue|tasks?)',
        r'(?:what|show)\s+(?:are\s+)?(?:my\s+)?(?:pending|active|running)',
    ]
    for pat in job_patterns:
        if re.search(pat, lower):
            result['tool'] = 'hush_jobs'
            result['intent'] = 'admin'
        logger.info(f"[HOT-TRIGGER] Override to {result['tool']}")
        return result

    return result


def fallback_direct_write(guidance: dict, session: dict, session_id: str, result: dict) -> dict:
    """Fallback: if Gemini post-writer fails, write directly (old behavior)."""
    write_shards = guidance.get('write_shards', [])
    write_hints = guidance.get('write_hints', {})

    if write_hints and not write_shards:
        write_shards = list(write_hints.keys())

    if write_shards and write_hints:
        try:
            from maif_whisperer.memory.distributed_memory_seq002_v003_d0314__37_shards_1_master_lc_desc_upgrade import direct_shard_append_batch
            user_id = session.get('user_id', session_id)
            write_results = direct_shard_append_batch(
                write_shards=write_shards,
                write_hints=write_hints,
                user_id=user_id,
                source='guidance:fallback_direct',
            )
            result['written'] = [
                r.get('shard_id', '?') for r in write_results if r.get('success')
            ]
            logger.info(
                f"  ┌─ 📝 SHARD WRITE (fallback direct) ──────────┐\n"
                f"  │ {len(result['written'])} shard(s): {', '.join(result['written']):<33s}│\n"
                f"  └──────────────────────────────────────────────┘"
            )
        except Exception as e:
            logger.error(f"[{session_id}] FALLBACK WRITE FAILED: {e}")

    return result
