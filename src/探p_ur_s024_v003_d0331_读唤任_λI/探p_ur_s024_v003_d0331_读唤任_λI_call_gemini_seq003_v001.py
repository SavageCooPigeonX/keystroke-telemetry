"""探p_ur_s024_v003_d0331_读唤任_λI_call_gemini_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 40 lines | ~391 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json
import urllib.request

def _call_gemini(api_key: str, final_text: str, deleted_words: list,
                 rewrites: list, peak_buffer: str = '') -> str | None:
    deleted_str = ', '.join(
        w.get('word', str(w)) if isinstance(w, dict) else str(w)
        for w in deleted_words
    )
    rewrite_str = '; '.join(
        f'"{r.get("old", "")}" → "{r.get("new", "")}"'
        for r in (rewrites or [])
    ) or 'none'

    user_msg = (
        f"Submitted prompt: \"{final_text}\"\n"
        f"Deleted words/phrases: [{deleted_str}]\n"
        f"Peak buffer (longest text before deletion): \"{peak_buffer}\"\n"
        f"Rewrites: [{rewrite_str}]\n\n"
        f"Complete the deleted thought:"
    )

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': [{'parts': [{'text': user_msg}]}],
        'generationConfig': {'temperature': 0.4, 'maxOutputTokens': 400},
    }).encode('utf-8')

    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception:
        return None
