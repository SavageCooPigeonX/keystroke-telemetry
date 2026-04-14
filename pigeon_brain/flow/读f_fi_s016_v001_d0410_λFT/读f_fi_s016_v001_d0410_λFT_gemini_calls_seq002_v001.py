"""读f_fi_s016_v001_d0410_λFT_gemini_calls_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 30 lines | ~345 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, os, re, hashlib, urllib.request, urllib.error

def _call_gemini_model(prompt: str, api_key: str, model: str) -> tuple[str, bool]:
    """Returns (text, ok). ok=False on network/API error."""
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
    }
    url = _API_URL.format(model=model, key=api_key)
    req = urllib.request.Request(
        url, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            r = json.loads(resp.read())
            parts = r.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            return (parts[0].get("text", "") if parts else ""), True
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:100]
        return f"ERR:{e.code}:{body}", (e.code not in (503, 429, 500, 404))
    except Exception as e:
        return f"ERR:{e}", False


def _call_gemini(prompt: str, api_key: str) -> str:
    text, ok = _call_gemini_model(prompt, api_key, _MODEL)
    if not ok:  # overloaded — try fallback
        text, ok = _call_gemini_model(prompt, api_key, _MODEL_FALLBACK)
    return text
