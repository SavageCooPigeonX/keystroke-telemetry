"""pigeon_compiler/bones/nl_parsers_seq001_v001.py

BONE MODULE — Extracted from hush_nl_detection_seq001_v001.py (v4.9.13)
Origin: Lines 131, 254-428, 534, 656-750, 1485. All dated 2026-02-13/14 (stable).

Pure NL pattern matchers, validators, pronoun resolvers.
Zero LLM calls. Zero session mutation (except _detect_affirmative which is semi-stable).
"""
import re
import logging

logger = logging.getLogger('hush')


def is_changelog_query(lower: str) -> bool:
    """Check if message is asking about changelog / version history."""
    _CHANGELOG_WORDS = {
        'changelog', 'change log', 'what changed', "what's new",
        'whats new', 'version history', 'release notes', 'recent changes',
        'latest update', 'what was updated', "what's been updated",
        'recent updates', 'latest changes', 'new features',
    }
    return any(w in lower for w in _CHANGELOG_WORDS)


def detect_email_edit(message, lower, session, uid):
    """Detect 'change the subject to...' / 'make it more...' style email edits.

    Returns dict with edit instructions if detected, else None.
    Pure pattern matching — no LLM.
    """
    _EMAIL_EDIT_PATTERNS = [
        r'(?:change|edit|update|modify|fix|adjust|revise|rewrite)\s+(?:the\s+)?(?:subject|title|heading)',
        r'(?:change|edit|update|modify|fix|adjust|revise|rewrite)\s+(?:the\s+)?(?:body|content|text|message)',
        r'(?:make|change)\s+(?:it|the (?:email|invite|draft))\s+(?:more|less)',
        r'(?:add|include|mention|put)\s+(?:in\s+)?(?:the\s+)?(?:subject|body|email)',
        r"(?:tone|style|approach)\s+(?:should be|needs to be|is too)",
    ]
    if not session.get('_staged_invite') and not session.get('_staged_email'):
        return None

    for pat in _EMAIL_EDIT_PATTERNS:
        if re.search(pat, lower):
            return {'edit_requested': True, 'raw_instruction': message}

    return None


def detect_email_approval(message, lower, session, uid):
    """Detect email/invite send approval ('send it', 'looks good', etc).

    Returns dict if approval detected, else None.
    """
    _APPROVAL_WORDS = {
        'send it', 'send the email', 'send the invite', 'looks good',
        'perfect', 'good to go', 'approve', 'fire away', 'ship it',
        'send that', 'yes send', 'go ahead send', 'confirmed',
    }
    if not session.get('_staged_invite') and not session.get('_staged_email'):
        return None

    stripped = lower.strip().rstrip('!.,')
    if stripped in _APPROVAL_WORDS:
        return {'approved': True}

    return None


_PRONOUN_SET = {'them', 'him', 'her', 'that person', 'that entity', 'that business', 'they'}


def resolve_pronoun_to_entity(session):
    """Resolve 'them'/'him'/'her' to most recently discussed entity name.

    Scans recent system messages for entity data injections and
    recent user messages for proper nouns.
    """
    recent = session.get('messages', [])[-20:]

    for msg in reversed(recent):
        if msg.get('role') != 'system':
            continue
        content = msg.get('content', '')
        m = re.search(r'ENTITY BASELINE:\s*(.+?)\s*═', content)
        if m:
            return m.group(1).strip()
        m = re.search(r'Entity "(.+?)"', content)
        if m:
            return m.group(1).strip()
        m = re.search(r'DRAFT INVITE FOR\s+(.+?)\s*\(', content)
        if m:
            return m.group(1).strip()
        m = re.search(r'JOB (?:SUBMITTED|STAGED).*?Name:\s*(.+?)(?:\n|$)', content)
        if m:
            return m.group(1).strip()

    for msg in reversed(recent):
        if msg.get('role') != 'user':
            continue
        text = msg.get('content', '')
        if len(text) < 4 or text.startswith('/'):
            continue
        m = re.search(r'/(?:map|brief|search|job|grok)\s+(.+)', text)
        if m:
            return m.group(1).split(';')[0].strip()

    return None


def extract_email_from_context(entity_name, session):
    """Try to find an email for the entity from recent conversation context.

    Checks recent system messages for email addresses associated with entity.
    Returns email string or None.
    """
    recent = session.get('messages', [])[-20:]
    for msg in reversed(recent):
        content = msg.get('content', '')
        if entity_name.lower() in content.lower():
            emails = re.findall(r'[\w.+-]+@[\w.-]+\.\w{2,}', content)
            for email in emails:
                if 'myaifingerprint' not in email and 'noreply' not in email:
                    return email
    return None


def detect_waitlist_intent(lower, session, uid):
    """Detect 'show waitlist' / 'who's on the waitlist' style.

    Returns dict if matched, else None. Pure keyword matching.
    """
    _WAITLIST_PATTERNS = [
        r'(?:show|check|view|see|list|get)\s+(?:the\s+)?waitlist',
        r"(?:who'?s|who\s+is)\s+(?:on\s+)?(?:the\s+)?waitlist",
        r'waitlist\s+(?:status|count|numbers?)',
    ]
    for pat in _WAITLIST_PATTERNS:
        if re.search(pat, lower):
            return {'tool': 'waitlist_read', 'target': ''}
    return None


_GOOGLE_PATTERNS = [
    r'(?:google|web search|search google|search the web|search online|look up online|google search)\s+(?:for\s+)?(.+)',
    r'(?:search|find)\s+(?:on\s+)?(?:the\s+)?(?:web|internet|google|online)\s+(?:for\s+)?(.+)',
    r'(?:can you|could you|please)\s+(?:search|google|look up)\s+(?:for\s+)?(.+)',
    r'(?:do a|run a)\s+(?:google\s+)?search\s+(?:on|for|about)\s+(.+)',
    r'(?:search|google)\s+(?:for|about|up)\s+(.+)',
    r'^(?:search|google)\s+(.+?)\s+(?:online|on the web|on google)\s*$',
    r'^(?:search|google|look up|find)\s+(.+?)\s+(?:email|contact|phone|address|info)\s+(?:online|on the web|on google)?\s*$',
    r'^(?:search|google|look up)\s+(.+?)\s*$',
]

_NL_SEARCH_SKIP = {'for', 'me', 'it', 'this', 'that', 'something', ''}


def detect_google_search_match(lower: str) -> str | None:
    """Match NL google search patterns. Returns search query or None.

    This is the PURE PATTERN MATCH extracted from _detect_google_search.
    The caller handles session injection and tool firing.
    """
    for pattern in _GOOGLE_PATTERNS:
        match = re.search(pattern, lower)
        if not match:
            continue
        search_query = match.group(1).strip().rstrip('?.,!')
        if len(search_query) <= 2 or search_query in _NL_SEARCH_SKIP:
            continue
        return search_query
    return None


_AFFIRMATIVE_WORDS = {
    'yes', 'yeah', 'yep', 'yea', 'sure', 'do it', 'go ahead', 'go for it',
    'please', 'pls', 'ok', 'okay', 'k', 'ye', 'ya', 'absolutely', 'definitely',
    'yes please', 'yep do it', 'go', 'lets go', "let's go", 'send it', 'fire away',
}


def is_affirmative(lower: str) -> bool:
    """Check if message is an affirmative reply. Pure string match."""
    return lower.strip().rstrip('!.') in _AFFIRMATIVE_WORDS


def safe_log(intent_msg, uid):
    """Log intent event (best-effort)."""
    try:
        from maif_whisperer.hush_v38.logging.hush_intent_log_seq001_v003_d0314__replaces_master_intent_log_lc_desc_upgrade import (
            log_intent_structured,
        )
        log_intent_structured(
            user_id=uid or 'unknown',
            session_id='nl',
            user_message=intent_msg,
            detected_intent='nl_detection',
            tool_fired='true',
        )
    except Exception:
        pass
