"""Unsaid intent reconstruction via Gemini — fires on high-deletion prompts."""

# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v002 | 131 lines | ~1,112 tokens
# DESC:   fires_on_high_deletion_prompts
# INTENT: selection_aware_os
# LAST:   2026-03-29 @ fd2ab12
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

DELETION_THRESHOLD = 0.15  # 15%+ deletion = uncertainty signal — fires reconstruction
INTENT_DELETE_MIN_RUN = 5  # 5+ consecutive backspaces = intent change (matches composition analyzer)
GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_TIMEOUT = 4  # seconds — must be fast, runs synchronously on Enter

SYSTEM_PROMPT = (
    "You are an intent reconstruction engine. The operator typed a prompt to an AI coding assistant "
    "but deleted some words/phrases before submitting. Your job: reconstruct what they ACTUALLY "
    "wanted to say — the full unfiltered intent combining both the submitted text and deleted fragments.\n\n"
    "Rules:\n"
    "- Output a single sentence: the reconstructed full intent\n"
    "- Be specific and actionable — this will be injected as a custom instruction\n"
    "- If deleted words seem like typos, ignore them\n"
    "- If deleted words reveal a suppressed request, surface it\n"
    "- No explanations, no preamble — just the reconstructed intent sentence"
)


def _load_api_key(root: Path) -> str | None:
    env = root / '.env'
    if not env.exists():
        return None
    for line in env.read_text('utf-8').splitlines():
        if line.startswith('GEMINI_API_KEY='):
            return line.split('=', 1)[1].strip()
    return None


def _call_gemini(api_key: str, final_text: str, deleted_words: list, rewrites: list) -> str | None:
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
        f"Rewrites: [{rewrite_str}]\n\n"
        f"Reconstruct the operator's full intent:"
    )

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': [{'parts': [{'text': user_msg}]}],
        'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 150},
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
    )
    if not intent:
        return None

    intent_dr = composition.get('intent_deletion_ratio', dr)
    recon = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'final_text': composition.get('final_text', ''),
        'deleted_words': [
            w.get('word', str(w)) if isinstance(w, dict) else str(w)
            for w in deleted
        ],
        'deletion_ratio': intent_dr,
        'reconstructed_intent': intent,
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
