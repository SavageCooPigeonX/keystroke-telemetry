"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_bug_voices_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _build_bug_voices_block(root: Path, registry: dict | None) -> str:
    if registry is None:
        registry = _load_json(root / 'pigeon_registry.json')
    items = [
        (path, entry)
        for path, entry in _registry_items(registry)
        if entry.get('bug_keys')
    ]
    lines = [
        '<!-- pigeon:bug-voices -->',
        '## Bug Voices',
        '',
        '*Persistent bug demons minted from registry scars - active filename bugs first.*',
        '',
    ]
    if not items:
        lines.append('- No active bug demons. The trapdoors are quiet for now.')
        lines.append('<!-- /pigeon:bug-voices -->')
        return '\n'.join(lines)

    items.sort(key=lambda item: (-_bug_voice_score(item[1]), item[1].get('name', '')))
    for _, entry in items[:5]:
        key = _primary_bug(entry)
        persona_name, voice = _BUG_PERSONAS.get(key, ('Bug Imp', 'I keep coming back.'))
        entity = (entry.get('bug_entities') or {}).get(key) or persona_name
        recur = int((entry.get('bug_counts') or {}).get(key, 1) or 1)
        others = [bug for bug in entry.get('bug_keys', []) if bug != key]
        others_s = f' other={"+".join(others)}' if others else ''
        mark = entry.get('last_bug_mark', 'unmarked')
        last_change = entry.get('last_change', '')
        last_s = f' last={last_change}' if last_change else ''
        lines.append(
            f'- `{entry.get("name", "?")}` {mark} · {key} `{entity}` x{recur}{others_s}: "{voice}"{last_s}'
        )

    lines.append('<!-- /pigeon:bug-voices -->')
    return '\n'.join(lines)
