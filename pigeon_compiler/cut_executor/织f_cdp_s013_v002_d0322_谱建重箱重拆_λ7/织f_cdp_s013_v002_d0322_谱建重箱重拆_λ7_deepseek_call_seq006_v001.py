"""织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7_deepseek_call_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 14 lines | ~157 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _call_deepseek(prompt: str) -> str:
    """Call DeepSeek and strip any markdown fences from the response."""
    from pigeon_compiler.integrations.谱p_dsa_s001_v006_d0322_读_λ7 import (
        deepseek_query)

    result = deepseek_query(prompt, max_tokens=8000)
    code = result.get("content", "")
    if code.startswith("```"):
        lines = code.split("\n")
        end = -1 if lines[-1].strip().startswith("```") else len(lines)
        code = "\n".join(lines[1:end])
    return code.strip(), result.get("cost", 0)
