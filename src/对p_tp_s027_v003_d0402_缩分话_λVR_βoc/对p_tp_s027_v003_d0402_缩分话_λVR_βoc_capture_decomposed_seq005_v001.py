"""对p_tp_s027_v003_d0402_缩分话_λVR_βoc_capture_decomposed_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re

def capture_training_pair(root: Path) -> dict | None:
    """
    Capture a training pair from the latest edit cycle.

    Reads: latest edit_pair, matching journal entry, copilot_edits, rework.
    Writes: one record to logs/training_pairs.jsonl
    Returns: the training record or None.
    """
    root = Path(root)
    logs = root / 'logs'

    # Load latest edit pair
    edit_pairs = _load_jsonl_tail(logs / 'edit_pairs.jsonl', max_lines=5)
    if not edit_pairs:
        return None
    latest_edit = edit_pairs[-1]

    # Load matching journal entry (by session_n or timestamp proximity)
    journal_entries = _load_jsonl_tail(logs / 'prompt_journal.jsonl', max_lines=20)
    session_n = latest_edit.get('session_n', 0)
    journal_match = None
    for entry in reversed(journal_entries):
        if entry.get('session_n') == session_n:
            journal_match = entry
            break
    if not journal_match and journal_entries:
        journal_match = journal_entries[-1]

    # Load recent copilot edits
    copilot_edits = _load_jsonl_tail(logs / 'copilot_edits.jsonl', max_lines=50)

    # Load recent captured AI responses for this prompt
    ai_responses = _load_jsonl_tail(logs / 'ai_responses.jsonl', max_lines=100)

    # Load rework log
    rework_entries = []
    rework_path = root / 'rework_log.json'
    if rework_path.exists():
        try:
            rework_entries = json.loads(rework_path.read_text(encoding='utf-8'))
            if not isinstance(rework_entries, list):
                rework_entries = []
        except (json.JSONDecodeError, OSError):
            pass

    # Build the training record
    user_intent = _classify_user_intent(journal_match) if journal_match else {}
    copilot_intent = _classify_copilot_intent(latest_edit, copilot_edits)
    rework = _find_rework_for_prompt(
        user_intent.get('raw_prompt', ''), rework_entries
    )
    response_match = _find_response_for_prompt(
        user_intent.get('raw_prompt', '') or latest_edit.get('prompt_msg', ''),
        ai_responses,
    )
    response_summary = _summarize_text((response_match or {}).get('response', ''))
    work_note = _build_work_note(latest_edit, copilot_intent)
    completion_note = _build_completion_note(work_note, response_summary)

    record = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'cycle': 'per_edit',
        'session_n': session_n,
        'user_intent': user_intent,
        'copilot_intent': copilot_intent,
        'alignment': {
            'rework_score': rework.get('rework_score', None) if rework else None,
            'rework_verdict': rework.get('verdict', None) if rework else None,
            'latency_ms': copilot_intent.get('latency_ms', 0),
            'had_physical_keystroke': copilot_intent.get('had_physical_keystroke', False),
            'user_deletion_ratio': user_intent.get('deletion_ratio', 0),
            'user_hesitation': user_intent.get('hesitation_count', 0),
            'response_captured': bool(response_match),
        },
        'completion': {
            'work_note': work_note,
            'completion_note': completion_note,
            'response_summary': response_summary,
            'response_ts': (response_match or {}).get('ts', ''),
            'response_id': (response_match or {}).get('response_id', ''),
        },
    }

    # Write
    out_path = logs / 'training_pairs.jsonl'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')

    return record
