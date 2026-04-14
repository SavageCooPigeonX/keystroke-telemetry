"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_utils_b_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 12 lines | ~115 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

def _normalize_unsaid_text(text: str) -> str:
    return re.sub(r'\W+', ' ', (text or '').lower()).strip()


def _is_novel_unsaid_reconstruction(text: str) -> bool:
    norm = _normalize_unsaid_text(text)
    if len(norm) < 30:
        return False
    return not any(norm.startswith(prefix) for prefix in _GENERIC_UNSAID_PREFIXES)
