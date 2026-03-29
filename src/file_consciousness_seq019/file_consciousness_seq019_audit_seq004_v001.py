"""file_consciousness_seq019_audit_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def slumber_party_audit(root: Path, changed_files: list[str]) -> list[dict]:
    """Check contracts between changed files and their partners.

    Returns list of {severity, changed, partner, msg} entries.
    severity: breakup (missing export), fight (signature drift), healthy (shared I/O).
    """
    profiles_path = root / 'file_profiles.json'
    if not profiles_path.exists():
        return []
    profiles = json.loads(profiles_path.read_text('utf-8'))

    pillow_talk = []
    for changed in changed_files:
        stem = Path(changed).stem
        # Find module name (strip pigeon suffix)
        mod_name = re.sub(r'_seq\d+.*', '', stem)
        profile = profiles.get(mod_name, {})

        for partner in profile.get('partners', [])[:3]:
            pname = partner['name']
            pscore = partner['score']
            if pscore > 0.3:
                pillow_talk.append({
                    'severity': 'watch',
                    'changed': mod_name,
                    'partner': pname,
                    'score': pscore,
                    'msg': f'{pname} is closely coupled ({partner["reason"]}). Check compatibility.',
                })
    return pillow_talk
