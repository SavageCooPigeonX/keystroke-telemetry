"""读f_fi_s016_v001_d0410_λFT_parsing_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 26 lines | ~252 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, os, re, hashlib, urllib.request, urllib.error

def _parse_json(text: str) -> dict | None:
    if not text or text.startswith("ERR:"):
        return None
    # Strip markdown fences (single-line or multi-line ```json ... ```)
    text = text.strip()
    text = re.sub(r"^```[a-z]*\s*", "", text)  # leading fence
    text = re.sub(r"\s*```\s*$", "", text)      # trailing fence
    text = text.strip()
    try:
        result = json.loads(text)
        if "intent" not in result and "autonomous_directive" not in result:
            return None
        return result
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                candidate = json.loads(m.group())
                if "intent" in candidate or "autonomous_directive" in candidate:
                    return candidate
            except Exception:
                pass
    return None
