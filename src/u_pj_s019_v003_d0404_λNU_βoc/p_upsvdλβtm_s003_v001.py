"""u_pj_s019_v003_d0404_λNU_βoc_text_matching_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 38 lines | ~286 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _normalize_prompt_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r'\s+', ' ', value)
    return value


def _token_set(value: str) -> set[str]:
    return {token for token in re.findall(r'[a-z0-9]+', value.lower()) if token}


def _text_match_score(msg: str, comp: dict) -> float:
    msg_norm = _normalize_prompt_text(msg)
    if not msg_norm:
        return 0.0

    comp_text = comp.get('final_text') or comp.get('peak_buffer') or ''
    comp_norm = _normalize_prompt_text(comp_text)
    if not comp_norm:
        return 0.0

    if msg_norm == comp_norm:
        return 1.0

    msg_tokens = _token_set(msg_norm)
    comp_tokens = _token_set(comp_norm)
    if not msg_tokens or not comp_tokens:
        return 0.0

    overlap = len(msg_tokens & comp_tokens) / max(len(msg_tokens | comp_tokens), 1)

    if len(msg_norm) <= 24 or len(msg_tokens) <= 3:
        return overlap

    containment = 1.0 if msg_norm in comp_norm or comp_norm in msg_norm else 0.0
    return max(overlap, containment)
