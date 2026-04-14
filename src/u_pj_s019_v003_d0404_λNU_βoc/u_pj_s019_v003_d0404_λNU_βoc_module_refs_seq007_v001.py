"""u_pj_s019_v003_d0404_λNU_βoc_module_refs_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 14 lines | ~210 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _extract_module_refs(msg: str) -> list[str]:
    """Pull module names mentioned in the prompt text."""
    # Match pigeon module patterns and common module references
    refs = re.findall(r'\b(\w+_seq\d+)\b', msg)
    # Also catch short names from the module map
    short = re.findall(r'\b(dynamic_prompt|task_queue|operator_stats|file_heat|'
                       r'self_fix|push_narrative|cognitive_reactor|pulse_harvest|'
                       r'query_memory|rework_detector|drift_watcher|resistance_bridge|'
                       r'context_budget|streaming_layer|os_hook|git_plugin|'
                       r'prompt_journal|logger|models|timestamp)\b', msg, re.I)
    return list(set(refs + [s.lower() for s in short]))
