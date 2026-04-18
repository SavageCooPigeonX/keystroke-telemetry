"""对p_tp_s027_v003_d0402_缩分话_λVR_βoc_note_builders_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _build_work_note(edit_pair: dict, copilot_intent: dict) -> str:
    parts = []
    edit_why = str(edit_pair.get('edit_why', '')).strip()
    if edit_why:
        parts.append(edit_why)
    file_name = Path(str(copilot_intent.get('file', '') or edit_pair.get('file', ''))).name
    if file_name:
        parts.append(f'@{file_name}')
    deltas = []
    lines_added = int(copilot_intent.get('lines_added', 0) or 0)
    chars_inserted = int(copilot_intent.get('chars_inserted', 0) or 0)
    if lines_added:
        deltas.append(f'+{lines_added}L')
    if chars_inserted:
        deltas.append(f'+{chars_inserted}c')
    if deltas:
        parts.append(f'({", ".join(deltas)})')
    return ' '.join(parts).strip()[:220]


def _build_completion_note(work_note: str, response_summary: str) -> str:
    if work_note and response_summary:
        return _summarize_text(f'{work_note}. {response_summary}', max_chars=240)
    return work_note or response_summary
