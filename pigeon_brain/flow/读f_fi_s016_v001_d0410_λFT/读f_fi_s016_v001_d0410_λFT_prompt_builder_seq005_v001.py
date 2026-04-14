"""读f_fi_s016_v001_d0410_λFT_prompt_builder_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 18 lines | ~297 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, os, re, hashlib, urllib.request, urllib.error

def _build_prompt(name: str, source: str, bugs: list, credit_avg: str) -> str:
    src_clip = source[:_MAX_SRC] + ("...[truncated]" if len(source) > _MAX_SRC else "")
    bugs_str = ", ".join(f"{b}(sev={_BUG_SEV.get(b,0)})" for b in bugs) or "none"
    return (
        "You are analyzing a Python module in a self-modifying autonomous codebase.\n"
        f"Module: {name}\nActive bugs: {bugs_str}\nLearning credit trend: {credit_avg}\n\n"
        f"Source:\n```python\n{src_clip}\n```\n\n"
        "Respond ONLY with valid JSON (no markdown fences, no explanation outside JSON):\n"
        '{"intent":"one sentence — what this module\'s core job is",'
        '"critical_path":true_or_false,'
        '"what_to_fix":["concrete action 1","concrete action 2"],'
        '"break_risk":["what breaks if you touch this"],'
        '"autonomous_directive":"the single most impactful code change to make RIGHT NOW — be specific about function name and what to change",'
        '"reasoning":"1-2 sentences why this directive"}'
    )
