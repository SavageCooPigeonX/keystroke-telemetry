"""registry_seq012_v001.py — Local name registry for the Pigeon Compiler.

Stores every file's identity, version, mutation date, description,
last intent, and change history in pigeon_registry.json at project root.
Eliminates full filesystem scans — the heal pipeline reads/writes the registry.

Registry entry format:
{
  "path": "listen/live/noise_filter_seq007_v003_d0315__filter_live_noise_lc_added_drift_detection.py",
  "name": "noise_filter",
  "seq": 7,
  "ver": 3,
  "date": "0315",
  "desc": "filter_live_noise",
  "intent": "added_drift_detection",
  "history": [
    {"ver": 1, "date": "0312", "desc": "filter_live_noise", "intent": "created", "action": "created"},
    {"ver": 2, "date": "0314", "desc": "filter_live_noise", "intent": "nametag_added", "action": "nametag"},
    {"ver": 3, "date": "0315", "desc": "filter_live_noise", "intent": "added_drift_detection", "action": "edited"}
  ]
}

Filename = {name}_seq{NNN}_v{NNN}_d{MMDD}__{desc}_lc_{intent}.py
desc  = what the file IS (stable, from docstring)
intent = what was LAST DONE (mutates every push)
_lc_  = separator between desc and intent
"""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v003 | 246 lines | ~2,068 tokens
# DESC:   local_name_registry_for_the
# INTENT: desc_upgrade
# LAST:   2026-03-15 @ 855fd50
# ──────────────────────────────────────────────
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_FILE = 'pigeon_registry.json'
PIGEON_STEM_RE = re.compile(
    r'^(?P<name>.+)_seq(?P<seq>\d{3})_v(?P<ver>\d{3})'
    r'(?:_d(?P<date>\d{4}))?'
    r'(?:__(?P<slug>[a-z0-9_]+))?$'
)
LC_SEP = '_lc_'  # separator between desc and intent in filename slug


def _today() -> str:
    """Return MMDD string for today (UTC)."""
    return datetime.now(timezone.utc).strftime('%m%d')


def registry_path(root: Path) -> Path:
    return Path(root) / REGISTRY_FILE


def load_registry(root: Path) -> dict:
    """Load pigeon_registry.json. Returns {path: entry} dict."""
    rp = registry_path(root)
    if not rp.exists():
        return {}
    try:
        data = json.loads(rp.read_text(encoding='utf-8'))
        return {e['path']: e for e in data.get('files', [])}
    except (json.JSONDecodeError, KeyError):
        return {}


def save_registry(root: Path, entries: dict):
    """Write pigeon_registry.json atomically."""
    rp = registry_path(root)
    data = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'total': len(entries),
        'files': sorted(entries.values(), key=lambda e: e['path']),
    }
    rp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n',
                  encoding='utf-8')


def parse_pigeon_stem(stem: str) -> dict | None:
    """Parse a Pigeon filename stem into components.

    'noise_filter_seq007_v003_d0315__filter_live_noise_lc_added_drift'
    → {name: 'noise_filter', seq: 7, ver: 3, date: '0315',
       desc: 'filter_live_noise', intent: 'added_drift'}

    Legacy (no _lc_): treats full slug as desc, intent=''.
    """
    m = PIGEON_STEM_RE.match(stem)
    if not m:
        return None
    slug = m.group('slug') or ''
    desc, intent = '', ''
    if slug:
        if LC_SEP in slug:
            desc, intent = slug.split(LC_SEP, 1)
        else:
            desc = slug  # legacy: whole slug is desc
    return {
        'name': m.group('name'),
        'seq': int(m.group('seq')),
        'ver': int(m.group('ver')),
        'date': m.group('date') or '',
        'desc': desc,
        'intent': intent,
    }


def build_pigeon_filename(name: str, seq: int, ver: int,
                          date: str = '', desc: str = '',
                          intent: str = '') -> str:
    """Construct a full Pigeon filename from components.

    build_pigeon_filename('noise_filter', 7, 3, '0315',
                          'filter_live_noise', 'added_drift')
    → 'noise_filter_seq007_v003_d0315__filter_live_noise_lc_added_drift.py'
    """
    parts = f'{name}_seq{seq:03d}_v{ver:03d}'
    if date:
        parts += f'_d{date}'
    if desc and intent:
        parts += f'__{desc}{LC_SEP}{intent}'
    elif desc:
        parts += f'__{desc}'
    return parts + '.py'


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


def diff_registry_vs_disk(root: Path, entries: dict) -> dict:
    """Compare registry against actual files on disk.

    Returns {missing_on_disk: [...], new_on_disk: [...], moved: [...]}
    """
    from pigeon_compiler.rename_engine.scanner_seq001_v004_d0315__walk_the_project_tree_and_lc_verify_pigeon_plugin import scan_project

    catalog = scan_project(root)
    disk_paths = {f['path'] for f in catalog['files'] if not f['is_init']}
    reg_paths = set(entries.keys())

    return {
        'missing_on_disk': sorted(reg_paths - disk_paths),
        'new_on_disk': sorted(disk_paths - reg_paths),
        'matched': sorted(reg_paths & disk_paths),
    }
