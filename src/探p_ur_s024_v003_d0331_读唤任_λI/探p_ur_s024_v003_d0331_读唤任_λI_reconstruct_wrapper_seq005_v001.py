"""探p_ur_s024_v003_d0331_读唤任_λI_reconstruct_wrapper_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 83 lines | ~723 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json

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
