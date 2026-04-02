"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_registry_builders_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def build_registry_from_scan(root: Path, catalog: dict) -> dict:
    """Bootstrap a registry from a scanner catalog (first-time setup).

    Reads existing filenames, parses components, creates entries.
    """
    entries = {}
    today = _today()
    for f in catalog['files']:
        if f['is_init']:
            continue
        parsed = parse_pigeon_stem(f['stem'])
        if parsed:
            entry = {
                'path': f['path'],
                'name': parsed['name'],
                'seq': parsed['seq'],
                'ver': parsed['ver'],
                'date': parsed['date'] or today,
                'desc': parsed['desc'],
                'intent': parsed['intent'] or 'registered',
                'history': [{
                    'ver': parsed['ver'],
                    'date': parsed['date'] or today,
                    'desc': parsed['desc'],
                    'intent': parsed['intent'] or 'registered',
                    'action': 'registered',
                }],
            }
        else:
            entry = {
                'path': f['path'],
                'name': f['stem'],
                'seq': 0,
                'ver': 0,
                'date': today,
                'desc': '',
                'intent': '',
                'history': [{'ver': 0, 'date': today, 'desc': '', 'intent': '', 'action': 'discovered'}],
            }
        entries[f['path']] = entry
    return entries
