"""Unsaid intent reconstruction via Gemini — fires on high-deletion prompts."""

# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v003 | 149 lines | ~1,328 tokens
# DESC:   fires_on_high_deletion_prompts
# INTENT: intent_deletion_pipeline
# LAST:   2026-03-31 @ 7e0ecab
# SESSIONS: 2
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-02T05:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  fix gemini truncation + quality filter
# EDIT_STATE: harvested
# ── /pulse ──
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

DELETION_THRESHOLD = 0.15  # 15%+ deletion = uncertainty signal — fires reconstruction
INTENT_DELETE_MIN_RUN = 5  # 5+ consecutive backspaces = intent change (matches composition analyzer)
GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_TIMEOUT = 8  # seconds — must be fast, runs synchronously on Enter

SYSTEM_PROMPT = (
    "You are an unsaid-thought completion engine. The operator typed a prompt to an AI coding assistant "
    "but deleted some words/phrases before submitting. You see:\n"
    "- The SUBMITTED text (what they actually sent)\n"
    "- DELETED words/phrases (what they typed then backspaced away)\n"
    "- PEAK BUFFER (the longest the text got before they started deleting)\n"
    "- REWRITES (old→new text replacements)\n\n"
    "Your job: COMPLETE THE DELETED THOUGHT. What was the operator about to say before they pivoted?\n\n"
    "Rules:\n"
    "- Output format: ONE COMPLETE sentence finishing the deleted thought, then '---', then ONE sentence "
    "explaining why they probably deleted it\n"
    "- You MUST write at least 2 full sentences total. NEVER stop mid-sentence.\n"
    "- Focus on the DELETED content — what thought was abandoned?\n"
    "- If the peak buffer shows a longer sentence that was trimmed, complete that sentence\n"
    "- If deleted words are fragments (e.g. 'proce'), complete the word AND the full thought: "
    "'The operator was about to ask about the process of compilation and whether it handles edge cases.'\n"
    "- Be specific and complete — 'The operator wanted to ask about the compilation process and its error handling' "
    "NOT 'The user was about to type'\n"
    "- If deleted words are clearly just typos of what was retyped, say 'typo correction only'\n"
    "- No preamble. Start directly with the completed thought. No 'The user was...' — just state what they meant."
)


def _load_api_key(root: Path) -> str | None:
    env = root / '.env'
    if not env.exists():
        return None
    for line in env.read_text('utf-8').splitlines():
        if line.startswith('GEMINI_API_KEY='):
            return line.split('=', 1)[1].strip()
    return None


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


def reconstruct_if_needed(root: Path, composition: dict) -> dict | None:
    """Reconstruct unsaid intent when operator deletes significant text.

    Triggers on:
      1. intent_deleted_words exist (8+ consecutive backspaces = line-of-thinking change)
      2. Fallback: deletion_ratio > 30% with any deleted words (legacy path)

    Short backspace runs (1-7) are typo/habit noise and don't trigger.

    Args:
        root: project root
        composition: the composition dict from analyze_and_log

    Returns:
        reconstruction dict or None if not triggered
    """
    # Primary signal: intent deletions (8+ consecutive backspaces or selection ops)
    intent_deleted = composition.get('intent_deleted_words', [])
    # Fallback: raw deletion ratio for legacy compositions without intent tracking
    dr = composition.get('deletion_ratio', 0)
    all_deleted = composition.get('deleted_words', [])

    if intent_deleted:
        deleted = intent_deleted
    elif dr >= DELETION_THRESHOLD and all_deleted:
        deleted = all_deleted
    else:
        return None

    api_key = _load_api_key(root)
    if not api_key:
        return None

    intent = _call_gemini(
        api_key,
        composition.get('final_text', ''),
        deleted,
        composition.get('rewrites', []),
        composition.get('peak_buffer', ''),
    )
    if not intent:
        return None

    # Parse thought completion (line 1) and deletion reason (line 2, after ---)
    parts = intent.split('---', 1)
    thought = parts[0].strip()
    reason = parts[1].strip() if len(parts) > 1 else ''

    # Quality gate: reject truncated garbage (< 30 chars = Gemini stopped mid-sentence)
    if len(thought) < 30 and thought.lower() != 'typo correction only':
        return None

    intent_dr = composition.get('intent_deletion_ratio', dr)
    recon = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'final_text': composition.get('final_text', ''),
        'deleted_words': [
            w.get('word', str(w)) if isinstance(w, dict) else str(w)
            for w in deleted
        ],
        'peak_buffer': composition.get('peak_buffer', ''),
        'deletion_ratio': intent_dr,
        'reconstructed_intent': intent,
        'thought_completion': thought,
        'deletion_reason': reason,
        'trigger': 'intent_deletion' if intent_deleted else 'high_ratio',
    }

    # Append to log
    log_path = root / 'logs' / 'unsaid_reconstructions.jsonl'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(recon, ensure_ascii=False) + '\n')
    except OSError:
        pass

    return recon
