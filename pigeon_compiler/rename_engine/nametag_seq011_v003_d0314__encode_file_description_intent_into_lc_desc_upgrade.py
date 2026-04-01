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

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v003 | ~280 lines | ~2,200 tokens
# DESC:   encode_file_description_intent_into
# INTENT: glyph_filename_encoding
# LAST:   2026-04-01
# ──────────────────────────────────────────────
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
    from pigeon_compiler.rename_engine.scanner_seq001_v004_d0315__扫_walk_the_project_tree_and_lc_verify_pigeon_plugin import (
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


# ── Glyph filename encoding ──────────────────

def _extract_internal_imports(py_path: Path) -> list[str]:
    """AST-parse a file's imports, return internal module root names.

    Returns de-duped list like ['dynamic_prompt', 'cognitive_reactor', 'file_heat_map'].
    If the file has a decomposed package directory alongside it, aggregates
    imports from all children too.
    """
    paths_to_scan = [py_path]

    # Check for decomposed package directory
    # e.g. self_fix_seq013_v011_d0328__*.py → self_fix_seq013/ directory
    stem = py_path.stem
    seq_match = re.match(r'^(.+_seq\d{3})', stem)
    if seq_match:
        pkg_prefix = seq_match.group(1)
        pkg_dir = py_path.parent / pkg_prefix
        if pkg_dir.is_dir():
            paths_to_scan.extend(pkg_dir.rglob('*.py'))
        # Also check for directory patterns like name_seq013/
        for d in py_path.parent.iterdir():
            if d.is_dir() and d.name.startswith(pkg_prefix) and d != pkg_dir:
                paths_to_scan.extend(d.rglob('*.py'))

    KNOWN_ROOTS = {
        'src', 'pigeon_compiler', 'pigeon_brain', 'streaming_layer',
        'client', 'vscode_extension',
    }
    all_modules = []
    for p in paths_to_scan:
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(text)
        except Exception:
            continue
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ''
            if not mod:
                continue
            parts = mod.split('.')
            if not parts:
                continue
            top = parts[0]
            if top not in KNOWN_ROOTS:
                continue
            for p_part in parts[1:]:
                root_name = re.sub(r'_seq\d{3}.*$', '', p_part).lstrip('.')
                if root_name and root_name not in KNOWN_ROOTS:
                    all_modules.append(root_name)
                    break

    # De-dupe preserving order
    seen = set()
    result = []
    for m in all_modules:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def build_glyph_prefix(
    py_path: Path,
    module_name: str,
    glyph_map: dict[str, str],
    confidence_map: dict[str, str],
    partners: dict[str, list[dict]] | None = None,
    max_deps: int = 3,
) -> str:
    """Build a glyph prefix encoding identity + confidence + dependencies.

    Example: '修!推思热' = self_fix(degraded), deps: dynamic_prompt, cognitive_reactor, file_heat_map

    Args:
        py_path: path to the .py file (for import extraction fallback)
        module_name: root module name (e.g. 'self_fix')
        glyph_map: {module_name: chinese_char} from symbol dictionary
        confidence_map: {module_name: state_symbol} from confidence scorer
        partners: {module_name: [{name, score, reason}]} from file_profiles.json
        max_deps: maximum dependency glyphs to include
    """
    # Module's own glyph
    own_glyph = glyph_map.get(module_name, '')
    if not own_glyph:
        return ''

    # Confidence state — NOT included in filename (symbols like ✓!~? break Python imports)
    # State is stored in the symbol dictionary only, not in filenames.
    state = ''

    # Dependency glyphs — from partners (coupling data) first, AST fallback
    dep_chars = []
    if partners and module_name in partners:
        # Partners are sorted by coupling score. Take top-N that have glyphs.
        for p in partners[module_name]:
            pname = p.get('name', '')
            g = glyph_map.get(pname, '')
            if g and g != own_glyph and g not in dep_chars:
                dep_chars.append(g)
            if len(dep_chars) >= max_deps:
                break

    # AST fallback if no partner data
    if not dep_chars and py_path and py_path.exists():
        imports = _extract_internal_imports(py_path)
        for imp in imports:
            if imp == module_name:
                continue
            g = glyph_map.get(imp, '')
            if g and g != own_glyph and g not in dep_chars:
                dep_chars.append(g)
            if len(dep_chars) >= max_deps:
                break

    dep_glyphs = ''.join(dep_chars)
    return f'{own_glyph}{state}{dep_glyphs}'


def build_nametag_with_glyphs(
    stem: str,
    desc_slug: str,
    intent_slug: str = '',
    glyph_prefix: str = '',
) -> str:
    """Like build_nametag but prepends glyph encoding to desc slug.

    'noise_filter_seq007_v001' + '修!推思' + 'filter_live_noise' + 'added_drift'
    → 'noise_filter_seq007_v001__修!推思_filter_live_noise_lc_added_drift.py'
    """
    if glyph_prefix and desc_slug:
        full_desc = f'{glyph_prefix}_{desc_slug}'
    elif glyph_prefix:
        full_desc = glyph_prefix
    else:
        full_desc = desc_slug
    return build_nametag(stem, full_desc, intent_slug)


# ── Glyph drift detection ────────────────────

# Matches glyph prefix at start of desc slug: one or more CJK chars then underscore
# State symbols (✓~!?) are NOT included — they break Python identifiers
_GLYPH_PREFIX_RE = re.compile(
    r'^([\u4e00-\u9fff]+)(?:_|$)'
)


def _extract_glyph_prefix_from_name(filename: str) -> str:
    """Extract the existing glyph prefix from a filename's desc slug.

    'self_fix_seq013_v011_d0328__修!叙算思_one_shot...' → '修!叙算思'
    'logger_seq003_v004__core_keystroke...' → ''
    """
    parsed = parse_nametag(filename)
    slug = parsed.get('desc_slug', '')
    if not slug:
        return ''
    m = _GLYPH_PREFIX_RE.match(slug)
    return m.group(1) if m else ''


def detect_glyph_drift(
    py_path: Path,
    glyph_map: dict[str, str],
    confidence_map: dict[str, str],
    partners: dict[str, list[dict]] | None = None,
) -> dict:
    """Check if a file's glyph prefix is stale.

    Returns {drifted, current_prefix, expected_prefix, suggested_name}
    """
    parsed = parse_nametag(py_path.name)
    if not parsed['seq']:
        return {'drifted': False, 'current_prefix': '', 'expected_prefix': '',
                'suggested_name': py_path.name}

    mod_root = re.sub(r'_seq\d{3}.*$', '', py_path.stem).lstrip('.')
    current_prefix = _extract_glyph_prefix_from_name(py_path.name)
    expected_prefix = build_glyph_prefix(
        py_path, mod_root, glyph_map, confidence_map,
        partners=partners,
    )

    drifted = current_prefix != expected_prefix

    suggested = py_path.name
    if drifted:
        # Rebuild filename with updated glyph prefix
        desc_slug = parsed['desc_slug']
        # Strip old glyph prefix from desc slug
        if current_prefix and desc_slug.startswith(current_prefix):
            desc_slug = desc_slug[len(current_prefix):].lstrip('_')
        suggested = build_nametag_with_glyphs(
            parsed['base_stem'], desc_slug, parsed['intent_slug'],
            expected_prefix,
        )

    return {
        'drifted': drifted,
        'current_prefix': current_prefix,
        'expected_prefix': expected_prefix,
        'suggested_name': suggested,
    }


def scan_glyph_drift(
    root: Path,
    glyph_map: dict[str, str],
    confidence_map: dict[str, str],
    partners: dict[str, list[dict]] | None = None,
    folders: list[str] | None = None,
) -> list[dict]:
    """Scan all pigeon files for stale glyph prefixes.

    Returns list of {path, current, suggested, current_prefix, expected_prefix}.
    Flows into the heal pipeline's rename path (rollback + import rewrite).
    """
    from pigeon_compiler.rename_engine.scanner_seq001_v004_d0315__扫_walk_the_project_tree_and_lc_verify_pigeon_plugin import (
        scan_project,
    )

    catalog = scan_project(root, folders)
    drifts = []

    for f in catalog['files']:
        if f['is_init'] or not f.get('is_pigeon', False):
            continue
        py = root / f['path']
        if not py.exists():
            continue

        result = detect_glyph_drift(
            py, glyph_map, confidence_map, partners=partners,
        )
        if result['drifted']:
            drifts.append({
                'path': f['path'],
                'current': py.name,
                'suggested': result['suggested_name'],
                'current_prefix': result['current_prefix'],
                'expected_prefix': result['expected_prefix'],
            })

    return drifts
