"""nametag_seq011_v001.py — Encode file description + intent into filenames.

Each filename becomes a prompt carrying TWO living metadata:
  desc   = what the file IS  (from docstring, stable)
  intent = what was LAST DONE (change context, mutates each push)

Naming convention:
  {name}_seq{NNN}_v{NNN}_d{MMDD}__{desc}_lc_{intent}.py

The double-underscore separates the stable import identity from
the living slug. _lc_ separates description from last-change intent.

Examples:
  noise_filter_seq007_v002_d0615__filter_live_noise_lc_added_drift_detect.py
  email_sender_seq001_v003_d0615__resend_api_client_lc_fixed_retry_logic.py

Rules:
- desc slug: max 5 words, snake_case, from docstring
- intent slug: max 3 words, snake_case, from last mutation context
- Updated by heal engine when docstring or code changes
- Import rewriter handles cascading renames automatically
"""
import ast
import re
from pathlib import Path

MAX_DESC_WORDS = 5
MAX_INTENT_WORDS = 3
MAX_SLUG_CHARS = 50
DESC_SEPARATOR = '__'
LC_SEP = '_lc_'  # separator between desc and intent

# Pattern: name_seqNNN_vNNN[_dMMDD]__description.py
NAMETAG_PATTERN = re.compile(
    r'^(.+_seq\d{3}_v\d{3}(?:_d\d{4})?)(__[a-z0-9_]+)?\.py$'
)


def extract_desc_slug(py_path: Path) -> str:
    """Extract a short description slug from a file's docstring.

    Returns snake_case slug like 'filters_live_stream_noise'
    or empty string if no meaningful docstring found.
    """
    try:
        text = py_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''

    first_line = _docstring_first_line(text)
    if not first_line:
        return ''

    return slugify(first_line)


def slugify(text: str, max_words: int = MAX_DESC_WORDS) -> str:
    """Convert a sentence to a filename-safe slug.

    'Filter background noise from live streams' → 'filter_background_noise'
    'Resend API Client' → 'resend_api_client'
    """
    # Strip filename prefixes like "module.py — "
    if ' — ' in text:
        text = text.split(' — ', 1)[1]
    elif ' - ' in text:
        parts = text.split(' - ', 1)
        if len(parts[0].split()) <= 3:
            text = parts[1]

    # Remove trailing period
    text = text.rstrip('.')

    # Convert to lowercase, replace non-alpha with underscore
    slug = re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

    # Strip leaked seq/ver patterns like "seq007_v001"
    slug = re.sub(r'_?seq\d{3}_v\d{3}_?', '_', slug).strip('_')

    # Trim to max words
    words = slug.split('_')
    words = [w for w in words if w]  # remove empties
    if len(words) > max_words:
        words = words[:max_words]

    slug = '_'.join(words)

    # Hard limit on total chars
    if len(slug) > MAX_SLUG_CHARS:
        slug = slug[:MAX_SLUG_CHARS].rstrip('_')

    return slug


def build_nametag(stem: str, desc_slug: str, intent_slug: str = '') -> str:
    """Combine a Pigeon stem with desc + intent.

    'noise_filter_seq007_v001' + 'filter_live_noise' + 'added_drift'
    → 'noise_filter_seq007_v001__filter_live_noise_lc_added_drift.py'

    Without intent:
    'noise_filter_seq007_v001' + 'filter_live_noise'
    → 'noise_filter_seq007_v001__filter_live_noise.py'
    """
    if not desc_slug:
        return f'{stem}.py'
    if intent_slug:
        return f'{stem}{DESC_SEPARATOR}{desc_slug}{LC_SEP}{intent_slug}.py'
    return f'{stem}{DESC_SEPARATOR}{desc_slug}.py'


def parse_nametag(filename: str) -> dict:
    """Parse a nametag filename into components.

    Returns {stem, seq, ver, desc_slug, intent_slug, base_stem}
    """
    m = NAMETAG_PATTERN.match(filename)
    if not m:
        return {'stem': Path(filename).stem, 'seq': '', 'ver': '',
                'desc_slug': '', 'intent_slug': '', 'base_stem': Path(filename).stem}

    base = m.group(1)  # e.g. 'noise_filter_seq007_v001_d0315'
    slug_raw = m.group(2) or ''  # e.g. '__filter_noise_lc_added_drift'
    slug_raw = slug_raw.lstrip('_')

    desc_slug, intent_slug = '', ''
    if slug_raw:
        if LC_SEP in slug_raw:
            desc_slug, intent_slug = slug_raw.split(LC_SEP, 1)
        else:
            desc_slug = slug_raw  # legacy: no intent yet

    seq_m = re.search(r'_seq(\d{3})_v(\d{3})', base)
    seq = seq_m.group(1) if seq_m else ''
    ver = seq_m.group(2) if seq_m else ''

    return {
        'stem': Path(filename).stem,
        'seq': seq,
        'ver': ver,
        'desc_slug': desc_slug,
        'intent_slug': intent_slug,
        'base_stem': base,
    }


def detect_drift(py_path: Path) -> dict:
    """Check if a file's name-description matches its docstring.

    Returns {drifted: bool, current_slug: str, docstring_slug: str,
             suggested_name: str}
    """
    parsed = parse_nametag(py_path.name)
    current_slug = parsed['desc_slug']
    docstring_slug = extract_desc_slug(py_path)

    if not docstring_slug:
        return {'drifted': False, 'current_slug': current_slug,
                'docstring_slug': '', 'suggested_name': py_path.name}

    drifted = current_slug != docstring_slug
    suggested = build_nametag(parsed['base_stem'], docstring_slug)

    return {
        'drifted': drifted,
        'current_slug': current_slug,
        'docstring_slug': docstring_slug,
        'suggested_name': suggested,
    }


def scan_drift(root: Path, folders: list[str] = None) -> list[dict]:
    """Scan all files for name-description drift.

    Returns list of {path, current, suggested, slug_current, slug_new}
    """
    from pigeon_compiler.rename_engine.scanner_seq001_v003_d0314__walk_the_project_tree_and_lc_desc_upgrade import (
        scan_project,
    )

    catalog = scan_project(root, folders)
    drifts = []

    for f in catalog['files']:
        if f['is_init']:
            continue
        # Skip backup/archive files
        if '_BACKUP' in f['stem'] or '_backup' in f['stem']:
            continue
        py = root / f['path']
        if not py.exists():
            continue

        result = detect_drift(py)
        if result['drifted'] and result['docstring_slug']:
            drifts.append({
                'path': f['path'],
                'current': py.name,
                'suggested': result['suggested_name'],
                'slug_current': result['current_slug'],
                'slug_new': result['docstring_slug'],
            })

    return drifts


def _docstring_first_line(text: str) -> str:
    """Get first meaningful line from module docstring."""
    try:
        tree = ast.parse(text)
        ds = ast.get_docstring(tree)
        if not ds:
            return ''
    except SyntaxError:
        return ''

    for line in ds.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.startswith(('Args:', 'Returns:', '---', 'Usage:')):
            continue
        # Skip lines that are just file paths (e.g. "listen/live/foo.py")
        if line.endswith('.py') and ('/' in line or '\\' in line):
            continue
        # Skip lines that are bare filenames (e.g. "foo_seq001_v001.py")
        if re.match(r'^[\w.]+\.py$', line):
            continue
        # Strip filename prefix like "module.py — description"
        if ' \u2014 ' in line:
            line = line.split(' \u2014 ', 1)[1]
        elif ' - ' in line:
            parts = line.split(' - ', 1)
            if len(parts[0].split()) <= 4:
                line = parts[1]
        return line.rstrip('.')
    return ''
