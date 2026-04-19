"""git_plugin_intent_parsing_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v002 | 47 lines | ~436 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: git_plugin_root
# LAST:   2026-04-19 @ 5567e06
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

_INTENT_CODE_RULES: list[tuple[tuple[str, ...], str]] = [
    (('fix', 'bug', 'repair', 'heal', 'restore', 'wrong', 'broken'), 'FX'),
    (('rename', 'nametag'), 'RN'),
    (('refactor', 'restructure'), 'RF'),
    (('split', 'decompose', 'compile'), 'SP'),
    (('telemetry', 'prompt', 'operator', 'journal', 'context', 'unsaid', 'voice', 'engagement'), 'TL'),
    (('compress', 'glyph', 'dictionary', 'token'), 'CP'),
    (('verify', 'test', 'audit', 'validate', 'check'), 'VR'),
    (('feature', 'add', 'implement', 'build', 'create'), 'FT'),
    (('cleanup', 'chore', 'docs', 'update'), 'CL'),
]

def _parse_intent(msg: str) -> str:
    """Commit message → 3-word intent slug.

    'feat: Hush spy mode + hero image' → 'hush_spy_mode'
    'fix: apply directory hero image'  → 'fix_directory_hero'
    """
    line = msg.split('\n')[0].strip()
    m = re.match(
        r'^(?:feat|fix|chore|refactor|docs|test|ci)(?:\([^)]+\))?:\s*', line)
    if m:
        line = line[m.end():]
    slug = re.sub(r'[^a-z0-9]+', '_', line.lower()).strip('_')
    words = [w for w in slug.split('_') if w][:3]
    return '_'.join(words) or 'manual_edit'


def _intent_code(intent: str) -> str:
    text = (intent or '').lower()
    for needles, code in _INTENT_CODE_RULES:
        if any(needle in text for needle in needles):
            return code
    if not text:
        return 'OT'
    return text[:2].upper()
