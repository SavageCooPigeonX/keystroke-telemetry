"""对p_tp_s027_v003_d0402_缩分话_λVR_βoc_intent_classifiers_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _classify_user_intent(journal_entry: dict) -> dict:
    """Extract structured user intent from prompt journal entry."""
    signals = journal_entry.get('signals', {})
    return {
        'raw_prompt': journal_entry.get('msg', '')[:300],
        'classified_intent': journal_entry.get('intent', 'unknown'),
        'cognitive_state': journal_entry.get('cognitive_state', 'unknown'),
        'wpm': signals.get('wpm', 0),
        'deletion_ratio': signals.get('deletion_ratio', 0),
        'hesitation_count': signals.get('hesitation_count', 0),
        'rewrite_count': signals.get('rewrite_count', 0),
        'deleted_words': journal_entry.get('deleted_words', []),
        'composition_time_ms': signals.get('duration_ms', 0),
    }


def _classify_copilot_intent(edit_pair: dict, copilot_edits: list[dict]) -> dict:
    """Extract structured Copilot intent from edit pair + copilot edit logs."""
    # Find copilot_edits matching this file near the edit timestamp
    file_key = edit_pair.get('file', '')
    edit_ts = edit_pair.get('edit_ts', '')
    matching_edits = [
        e for e in copilot_edits
        if e.get('file', '') == file_key
    ]
    total_chars = sum(e.get('chars_inserted', 0) for e in matching_edits)
    total_replaced = sum(e.get('chars_replaced', 0) for e in matching_edits)
    total_lines = sum(e.get('lines_added', 0) for e in matching_edits)
    edit_sources = list({e.get('edit_source', 'unknown') for e in matching_edits})
    had_physical = any(e.get('had_physical_keystroke', False) for e in matching_edits)

    return {
        'edit_why': edit_pair.get('edit_why', ''),
        'file': file_key,
        'edit_ts': edit_ts,
        'chars_inserted': total_chars,
        'chars_replaced': total_replaced,
        'lines_added': total_lines,
        'edit_sources': edit_sources,
        'had_physical_keystroke': had_physical,
        'latency_ms': edit_pair.get('latency_ms', 0),
    }
