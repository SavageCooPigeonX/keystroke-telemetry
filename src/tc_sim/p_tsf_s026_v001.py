"""tc_sim_seq001_v001_fix_seq026_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 026 | VER: v001 | 73 lines | ~1,047 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from src.tc_constants_seq001_v001_seq001_v001 import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT
import os
import re

def apply_fix(bug: dict, dry: bool = False) -> str:
    """Apply a code fix for a diagnosed bug. Returns description of fix."""
    fix_type = bug.get('fix', '')

    if fix_type == 'deduplicate_registry_results':
        target = ROOT / 'src' / 'tc_context_seq001_v001_agent_seq001_v001.py'
        code = target.read_text('utf-8')
        old = "    scored.sort(key=lambda x: x['score'], reverse=True)\n    return scored[:max_files]"
        new = ("    scored.sort(key=lambda x: x['score'], reverse=True)\n"
               "    # Deduplicate by stem name — registry has multiple entries per module\n"
               "    seen_names = set()\n"
               "    deduped = []\n"
               "    for s in scored:\n"
               "        stem = s['name'].split('_seq')[0] if '_seq' in s['name'] else s['name']\n"
               "        if stem not in seen_names:\n"
               "            seen_names.add(stem)\n"
               "            deduped.append(s)\n"
               "    return deduped[:max_files]")
        if old not in code:
            return 'SKIP — code already patched or changed'
        if dry:
            return f'WOULD patch: deduplicate context files in select_context_files()'
        target.write_text(code.replace(old, new), 'utf-8')
        return 'PATCHED: added deduplication by stem name in select_context_files()'

    if fix_type == 'reduce_stopwords':
        target = ROOT / 'src' / 'tc_context_seq001_v001_agent_seq001_v001.py'
        code = target.read_text('utf-8')
        # These words are meaningful in this codebase, not generic
        words_to_unblock = ['thought', 'complete', 'completing', 'completion',
                            'select', 'selection', 'profile', 'natural', 'naturally',
                            'context', 'agent', 'prompt']
        removed = []
        for w in words_to_unblock:
            if f"'{w}'" in code or f" {w} " in code:
                removed.append(w)
        # The fix: add an allowlist that overrides stopwords for this codebase
        old_extract = ("def _extract_mentions(buffer: str) -> list[str]:\n"
                       "    \"\"\"Extract module/file names mentioned in the buffer text.\n"
                       "    \n"
                       "    Strongly prefers underscore_names (likely module refs) over single words.\n"
                       "    \"\"\"")
        new_extract = ("# Words that ARE meaningful in this codebase despite looking generic\n"
                       "_CODEBASE_TERMS = frozenset(\n"
                       "    'thought completer completion context select selection agent '\n"
                       "    'profile prompt entropy drift reactor pulse harvest '\n"
                       "    'pigeon compiler rename registry manifest '\n"
                       "    'buffer keyboard keystroke typing pause popup '\n"
                       "    'narrative organism consciousness shard memory '.split()\n"
                       ")\n\n\n"
                       "def _extract_mentions(buffer: str) -> list[str]:\n"
                       "    \"\"\"Extract module/file names mentioned in the buffer text.\n"
                       "    \n"
                       "    Strongly prefers underscore_names (likely module refs) over single words.\n"
                       "    \"\"\"")
        if old_extract not in code:
            return 'SKIP — _extract_mentions signature changed'
        if dry:
            return f'WOULD patch: add codebase-specific term allowlist to bypass stopwords'
        code = code.replace(old_extract, new_extract)
        # Also patch the filter condition to check allowlist
        old_filter = ("        if len(w) > 4 and w not in _STOPWORDS and w not in seen:")
        new_filter = ("        if len(w) > 4 and (w in _CODEBASE_TERMS or w not in _STOPWORDS) and w not in seen:")
        code = code.replace(old_filter, new_filter)
        target.write_text(code, 'utf-8')
        return f'PATCHED: added _CODEBASE_TERMS allowlist — {len(removed)} words unblocked'

    return f'UNKNOWN fix type: {fix_type}'
