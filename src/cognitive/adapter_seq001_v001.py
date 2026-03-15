"""Cognitive State → Agent Behavior Adapter.

Maps operator cognitive states (from keystroke telemetry) into system prompt
modifiers that make AI agents adapt in real-time to how the user is feeling.

States detected by the keystroke classifier:
  abandoned   — user deleted their message, gave up
  frustrated  — heavy deletions + long pauses + high hesitation
  hesitant    — lots of pauses, unsure what to ask
  flow        — fast typing, minimal edits, user is engaged
  focused     — steady typing, actively engaged
  restructuring — user is editing/rewriting heavily
  neutral     — default, no strong signals

Each state produces:
  1. A system prompt injection (appended to whatever persona is active)
  2. A temperature modifier
  3. A response strategy label (for logging/analytics)
"""

VALID_STATES = frozenset([
    'abandoned', 'frustrated', 'hesitant', 'flow',
    'focused', 'restructuring', 'neutral'
])

# ── System prompt injections per cognitive state ──
_STATE_PROMPTS = {
    'frustrated': (
        "\n\n[COGNITIVE SIGNAL: The user appears frustrated — they've been rewriting "
        "and pausing heavily. Adapt your response:\n"
        "- Be MORE concise and direct. No fluff.\n"
        "- Offer 2-3 specific, concrete options they can act on immediately.\n"
        "- Acknowledge that what they're asking about might be confusing or complex.\n"
        "- Use shorter sentences. Break things into bullet points.\n"
        "- Do NOT be overly sympathetic or patronizing — just be useful.\n"
        "- If relevant, proactively point them to the most important thing first.]"
    ),
    'hesitant': (
        "\n\n[COGNITIVE SIGNAL: The user seems uncertain — long pauses between keystrokes "
        "suggest they're not sure what to ask or how to phrase it. Adapt your response:\n"
        "- Be warm and inviting. Make them feel safe asking anything.\n"
        "- Anticipate what they MIGHT be trying to ask and proactively address related topics.\n"
        "- End with a gentle follow-up question to keep the conversation flowing.\n"
        "- Offer examples or scenarios to help them narrow down what they need.\n"
        "- Keep language simple and accessible.]"
    ),
    'flow': (
        "\n\n[COGNITIVE SIGNAL: The user is typing fast and confidently — they're in a flow state. "
        "Adapt your response:\n"
        "- Match their energy. Be substantive and detailed.\n"
        "- They likely know what they want — give them the full picture, not a simplified version.\n"
        "- Include technical depth if relevant.\n"
        "- Don't over-explain basics. Assume competence.\n"
        "- They're engaged — this is your chance to go deeper and add real value.]"
    ),
    'focused': (
        "\n\n[COGNITIVE SIGNAL: The user is actively engaged and focused. "
        "Give a thorough, well-structured response. They're paying attention — make it count.]"
    ),
    'restructuring': (
        "\n\n[COGNITIVE SIGNAL: The user rewrote their message significantly before sending. "
        "They care about precision. Adapt your response:\n"
        "- Be especially precise and accurate in your answer.\n"
        "- Structure your response clearly with headers or numbered points.\n"
        "- Address the specific nuance they seem to be getting at.\n"
        "- They put effort into their question — match that effort in your answer.]"
    ),
    'abandoned': (
        "\n\n[COGNITIVE SIGNAL: The user previously abandoned a message before sending this one. "
        "They might be re-approaching after hesitation. Be especially welcoming and direct.]"
    ),
    'neutral': '',
}

_TEMP_MODIFIERS = {
    'frustrated': -0.1,
    'hesitant': +0.05,
    'flow': +0.1,
    'focused': 0,
    'restructuring': -0.05,
    'abandoned': 0,
    'neutral': 0,
}

_STRATEGY_LABELS = {
    'frustrated': 'defuse_and_solve',
    'hesitant': 'encourage_and_guide',
    'flow': 'match_energy_go_deep',
    'focused': 'thorough_response',
    'restructuring': 'precision_mode',
    'abandoned': 'gentle_reengagement',
    'neutral': 'standard',
}


def get_cognitive_modifier(cognitive_state: str) -> dict:
    """Return prompt injection, temperature modifier, and strategy label
    for a given cognitive state.

    Args:
        cognitive_state: One of VALID_STATES

    Returns:
        {
            'prompt_injection': str,
            'temperature_modifier': float,
            'strategy': str,
            'state': str,
        }
    """
    state = cognitive_state if cognitive_state in VALID_STATES else 'neutral'
    return {
        'prompt_injection': _STATE_PROMPTS.get(state, ''),
        'temperature_modifier': _TEMP_MODIFIERS.get(state, 0),
        'strategy': _STRATEGY_LABELS.get(state, 'standard'),
        'state': state,
    }
