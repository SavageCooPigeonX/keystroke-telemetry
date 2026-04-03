"""u_pj_s019_v002_d0402_λC_intent_extraction_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _classify_intent(msg: str) -> str:
    """Classify prompt intent from first matching keyword."""
    low = msg.lower()
    for kw, cat in INTENT_MAP.items():
        if kw in low:
            return cat
    return 'unknown'


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
