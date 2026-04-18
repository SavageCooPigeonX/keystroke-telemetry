"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_version_bump_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def bump_version(entry: dict, new_desc: str = '',
                 new_intent: str = '', action: str = 'mutated') -> dict:
    """Bump an entry's version, update date + desc + intent, append history.

    Returns the updated entry (mutates in place).
    new_desc defaults to existing desc if empty.
    new_intent is required for meaningful tracking.
    """
    today = _today()
    entry['ver'] += 1
    entry['date'] = today
    if new_desc:
        entry['desc'] = new_desc
    if new_intent:
        entry['intent'] = new_intent
    entry['history'].append({
        'ver': entry['ver'],
        'date': today,
        'desc': entry['desc'],
        'intent': entry['intent'],
        'action': action,
    })
    folder = str(Path(entry['path']).parent).replace('\\', '/')
    if folder == '.':
        folder = ''
    new_filename = build_pigeon_filename(
        entry['name'], entry['seq'], entry['ver'],
        entry['date'], entry['desc'], entry['intent'],
    )
    entry['path'] = f'{folder}/{new_filename}' if folder else new_filename
    return entry


def bump_all_versions(entries: dict, intent: str = 'mass_rename',
                      action: str = 'mass_rename') -> dict:
    """Bump every entry's version by 1 (mass version increment).

    Used when a codebase-wide mutation happens (e.g., adding registry).
    intent is set on all entries to describe the mass action.
    """
    today = _today()
    for entry in entries.values():
        if entry['seq'] == 0:
            continue  # skip non-pigeon
        entry['ver'] += 1
        entry['date'] = today
        entry['intent'] = intent
        entry['history'].append({
            'ver': entry['ver'],
            'date': today,
            'desc': entry['desc'],
            'intent': intent,
            'action': action,
        })
        folder = str(Path(entry['path']).parent).replace('\\', '/')
        if folder == '.':
            folder = ''
        new_filename = build_pigeon_filename(
            entry['name'], entry['seq'], entry['ver'],
            entry['date'], entry['desc'], entry['intent'],
        )
        entry['path'] = f'{folder}/{new_filename}' if folder else new_filename
    return entries
