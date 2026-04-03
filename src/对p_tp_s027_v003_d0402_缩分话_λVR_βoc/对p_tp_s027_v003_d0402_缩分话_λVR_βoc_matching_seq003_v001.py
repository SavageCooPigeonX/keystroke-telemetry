"""对p_tp_s027_v003_d0402_缩分话_λVR_βoc_matching_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _find_response_for_prompt(prompt_msg: str, response_entries: list[dict]) -> dict | None:
    prompt_norm = _normalize_text(prompt_msg)
    if not prompt_norm:
        return None
    prompt_head = prompt_norm[:80]
    for entry in reversed(response_entries):
        response_prompt = _normalize_text(entry.get('prompt', ''))
        if not response_prompt:
            continue
        if response_prompt == prompt_norm:
            return entry
        if prompt_head and response_prompt[:80] == prompt_head:
            return entry
        if len(prompt_head) >= 24 and (prompt_head in response_prompt or response_prompt[:48] in prompt_norm):
            return entry
    return None


def _find_rework_for_prompt(prompt_msg: str, rework_entries: list[dict]) -> dict | None:
    """Find rework score matching this prompt (by hint prefix)."""
    if not prompt_msg:
        return None
    prefix = prompt_msg[:80].lower()
    for entry in reversed(rework_entries):
        hint = (entry.get('query_hint', '') or '').lower()
        if hint and prefix[:40] in hint:
            return entry
    return None
