"""codebase_transmuter — three-layer mirror generation.

layer 1: build/numerical/  — identifiers→numbers + telemetry vector header.
          every file is a pure math object. H=entropy, R=rework, E=heat,
          C=coupling, B=bugs. LLMs compute on this.
layer 2: build/compressed/ — noise-stripped intent code (via context_compressor).
layer 3: build/narrative/  — unhinged comedy prose with persistent personalities.
          each file is a character. bugs are demons. metrics are moods.
also:     logs/codebase_stats.json — global metrics dashboard.
"""
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-04T07:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  entropy shedding into file personalities + copilot touch tracking
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

import ast
import json
import math
import re
import time
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

SKIP_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'node_modules',
             '.egg-info', 'pigeon_code.egg-info', 'build', 'stress_logs',
             'test_logs', 'demo_logs', 'logs'}

PY_DIRS = ['src', 'pigeon_compiler', 'pigeon_brain', 'streaming_layer', 'client']

APPROX_CHARS_PER_TOKEN = 4.0


def _tok(text):
    return max(1, int(len(text) / APPROX_CHARS_PER_TOKEN))


# ─── TELEMETRY LOADER ──────────────────────────────────────────────
# loads all signal sources into a unified per-module dict

def _load_telemetry(root):
    """Returns {module_name: {H, R, E, C, B, T, mood, demons}} for every known module."""
    telem = defaultdict(lambda: {'H': 0.0, 'R': 0.0, 'E': 0.0, 'C': 0.0, 'B': 0,
                                  'T': 0, 'mood': 'neutral', 'demons': []})

    # 1. heat map → E (operator hesitation per module)
    hm_path = root / 'file_heat_map.json'
    if hm_path.exists():
        hm = json.loads(hm_path.read_text('utf-8', errors='ignore'))
        for mod, data in hm.items():
            samples = data if isinstance(data, list) else data.get('samples', [])
            if samples:
                avg_hes = sum(s.get('hes', 0) for s in samples) / len(samples)
                telem[mod]['E'] = round(avg_hes, 3)

    # 2. entropy map → H (copilot uncertainty per module)
    em_path = root / 'logs' / 'entropy_map.json'
    if em_path.exists():
        em = json.loads(em_path.read_text('utf-8', errors='ignore'))
        for m in em.get('top_entropy_modules', []):
            telem[m['module']]['H'] = round(m.get('avg_entropy', 0), 3)

    # 3. rework log → R (aggregate rework rate per mentioned module)
    rw_path = root / 'rework_log.json'
    if rw_path.exists():
        rw = json.loads(rw_path.read_text('utf-8', errors='ignore'))
        if isinstance(rw, list):
            mod_rework = defaultdict(list)
            for entry in rw:
                hint = entry.get('query_hint', '')
                score = entry.get('rework_score', 0)
                # extract module refs from query hint
                words = re.findall(r'[a-zA-Z_]\w+', hint)
                for w in words:
                    if len(w) > 3:
                        mod_rework[w].append(score)
            for mod, scores in mod_rework.items():
                telem[mod]['R'] = round(sum(scores) / len(scores), 3)

    # 4. file profiles → C (coupling score)
    fp_path = root / 'file_profiles.json'
    if fp_path.exists():
        fp = json.loads(fp_path.read_text('utf-8', errors='ignore'))
        for mod, data in fp.items():
            partners = data.get('partners', [])
            if partners:
                avg_couple = sum(p.get('score', 0) for p in partners) / len(partners)
                telem[mod]['C'] = round(avg_couple, 3)

    # 5. bug profiles → B (bug count + demon names)
    bp_path = root / 'logs' / 'bug_profiles.json'
    if bp_path.exists():
        bp = json.loads(bp_path.read_text('utf-8', errors='ignore'))
        for mod, data in bp.get('all_modules', {}).items():
            bug_keys = data.get('bug_keys', [])
            entities = data.get('bug_entities', {})
            telem[mod]['B'] = len(bug_keys)
            telem[mod]['demons'] = [f"{k}:{entities.get(k, k)}" for k in bug_keys]

    # 6. copilot touch count → T (accumulated entropy from copilot edits)
    ep_path = root / 'logs' / 'edit_pairs.jsonl'
    if ep_path.exists():
        for line in ep_path.read_text('utf-8', errors='ignore').splitlines():
            try:
                entry = json.loads(line)
                f = entry.get('file', '')
                stem = Path(f).stem
                base = re.sub(r'_s\d{3,4}_v\d{3,4}_.*$', '', stem)
                telem[base]['T'] += 1
            except Exception:
                continue

    # derive mood from signals — T enters as normalized copilot entropy
    for mod, t in telem.items():
        t_norm = min(t['T'] / 10.0, 1.0)  # 10+ touches = max entropy
        danger = (t['H'] * 0.25 + t['R'] * 0.15 + t['E'] * 0.2 +
                  t['C'] * 0.1 + min(t['B'] * 0.1, 0.1) + t_norm * 0.2)
        if danger > 0.5:
            t['mood'] = 'unhinged'
        elif danger > 0.35:
            t['mood'] = 'paranoid'
        elif danger > 0.2:
            t['mood'] = 'anxious'
        elif danger > 0.1:
            t['mood'] = 'cautious'
        else:
            t['mood'] = 'chill'
        t['danger'] = round(danger, 3)

    return dict(telem)


def _telemetry_header(mod_name, telem):
    """Returns a numeric vector comment for a file's telemetry."""
    t = telem.get(mod_name, {})
    if not t:
        return '# V=[H=0 R=0 E=0 C=0 B=0 T=0 D=0]'
    return (f'# V=[H={t.get("H", 0):.2f} R={t.get("R", 0):.2f} '
            f'E={t.get("E", 0):.2f} C={t.get("C", 0):.2f} '
            f'B={t.get("B", 0)} T={t.get("T", 0)} D={t.get("danger", 0):.2f}]')


def _py_files(root):
    for d in PY_DIRS:
        dp = root / d
        if not dp.exists():
            continue
        for f in dp.rglob('*.py'):
            if any(s in f.relative_to(root).parts for s in SKIP_DIRS):
                continue
            yield f


# ─── NUMERICAL TRANSMUTATION ───────────────────────────────────────

class _Numerifier(ast.NodeTransformer):
    def __init__(self):
        self._map = {}
        self._counter = 0
        # preserve builtins and keywords
        self._preserve = {
            'True', 'False', 'None', 'self', 'cls', 'super',
            'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter',
            'isinstance', 'issubclass', 'hasattr', 'getattr', 'setattr',
            'dict', 'list', 'set', 'tuple', 'str', 'int', 'float', 'bool',
            'open', 'Path', 'json', 'os', 're', 'ast', 'sys', 'time',
            'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
            'ImportError', 'FileNotFoundError', 'AttributeError', 'RuntimeError',
            '__init__', '__main__', '__name__', '__file__', '__all__',
            '__enter__', '__exit__', '__str__', '__repr__', '__iter__',
        }

    def _num(self, name):
        if name in self._preserve:
            return name
        if name.startswith('_') and name.endswith('_'):
            return name
        if name not in self._map:
            self._counter += 1
            self._map[name] = f'n{self._counter}'
        return self._map[name]

    def visit_Name(self, node):
        node.id = self._num(node.id)
        return node

    def visit_FunctionDef(self, node):
        node.name = self._num(node.name)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        node.name = self._num(node.name)
        self.generic_visit(node)
        return node

    def visit_arg(self, node):
        node.arg = self._num(node.arg)
        node.annotation = None
        return node

    def visit_alias(self, node):
        # keep module names but numerify aliases
        if node.asname:
            node.asname = self._num(node.asname)
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.attr = self._num(node.attr)
        return node


def numerify_file(filepath):
    try:
        text = filepath.read_text('utf-8', errors='ignore')
        tree = ast.parse(text)
    except Exception:
        return None, {}

    # strip docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body[0] = ast.Pass()

    numer = _Numerifier()
    tree = numer.visit(tree)
    ast.fix_missing_locations(tree)

    try:
        code = ast.unparse(tree)
    except Exception:
        return None, {}

    return code, numer._map


def build_numerical_mirror(root):
    out_dir = root / 'build' / 'numerical'
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()

    telem = _load_telemetry(root)
    total_orig = 0
    total_num = 0
    files_done = 0
    global_map = {}

    for f in _py_files(root):
        code, name_map = numerify_file(f)
        if code is None:
            continue

        rel = f.relative_to(root)
        mod_name = f.stem
        # strip pigeon suffixes for telemetry lookup
        base = re.sub(r'_s\d{3,4}_v\d{3,4}_.*$', '', mod_name)

        # build telemetry vector header
        vec = _telemetry_header(base, telem)
        # also try full stem
        if base not in telem and mod_name in telem:
            vec = _telemetry_header(mod_name, telem)

        code = f'{vec}\n{code}'

        dest = out_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(code, encoding='utf-8')

        orig_text = f.read_text('utf-8', errors='ignore')
        total_orig += _tok(orig_text)
        total_num += _tok(code)
        files_done += 1

        for name, num_id in name_map.items():
            global_map[name] = num_id

    elapsed = round((time.monotonic() - t0) * 1000)

    # write the symbol map
    map_path = out_dir / '_SYMBOL_MAP.json'
    map_path.write_text(json.dumps(global_map, indent=1), encoding='utf-8')

    return {
        'files': files_done,
        'orig_tokens': total_orig,
        'numerical_tokens': total_num,
        'ratio': round(total_orig / max(total_num, 1), 2),
        'unique_symbols': len(global_map),
        'elapsed_ms': elapsed,
    }


# ─── NARRATIVE MIRROR ──────────────────────────────────────────────

def _extract_file_profile(filepath):
    try:
        text = filepath.read_text('utf-8', errors='ignore')
        tree = ast.parse(text)
    except Exception:
        return None

    lines = text.splitlines()
    imports = [l.strip() for l in lines if l.strip().startswith(('import ', 'from '))]

    funcs = []
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ''
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                doc = node.body[0].value.value.split('\n')[0].strip()
            args = [a.arg for a in node.args.args if a.arg != 'self']
            funcs.append({'name': node.name, 'args': args, 'doc': doc, 'line': node.lineno})
        elif isinstance(node, ast.ClassDef):
            classes.append({'name': node.name, 'line': node.lineno})

    # first docstring
    module_doc = ''
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        module_doc = tree.body[0].value.value.strip()

    return {
        'lines': len(lines),
        'tokens': _tok(text),
        'imports': imports[:15],
        'functions': funcs,
        'classes': classes,
        'module_doc': module_doc,
        'has_main': any('__main__' in l for l in lines),
    }


MOOD_INTROS = {
    'unhinged': "i've been touched {T} times by copilot and i am NOT okay. "
                "entropy is leaking from every function.",
    'paranoid': "copilot keeps coming back to me ({T} edits). "
                "what does it want. what does it know.",
    'anxious': "{T} copilot touches. each one left a mark. "
               "i can feel the uncertainty in my imports.",
    'cautious': "mildly concerned. {T} copilot visits so far. "
                "monitoring the situation.",
    'chill': "vibing. low entropy. copilot barely knows i exist.",
}

DEMON_TEMPLATES = {
    'oc': "THE OVERCAP MAW — i keep swelling. {lines} lines and growing. "
          "the compiler wants to split me but i refuse to die.",
    'hi': "THE HARDCODED IMPORT DEMON — someone wrote a literal path "
          "in my imports. it burns.",
    'de': "THE DEAD EXPORT PHANTOM — i export things nobody imports. "
          "screaming into the void.",
    'dd': "THE DUPLICATE DOCSTRING — my documentation is having an "
          "identity crisis. two of everything.",
    'hc': "THE COUPLING PARASITE — i'm fused to too many other files. "
          "if one falls, i fall.",
    'qn': "THE QUERY NOISE GREMLIN — my queries are polluted with "
          "junk. signal-to-noise is trash.",
}


def _narrate_file(filepath, profile, telem_entry=None):
    name = filepath.stem
    funcs = profile['functions']
    classes = profile['classes']
    imports = profile['imports']
    lines_count = profile['lines']
    tokens = profile['tokens']
    doc = profile['module_doc']
    t = telem_entry or {}

    parts = []

    # ─── IDENTITY ───
    parts.append(f'# {name}')
    mood = t.get('mood', 'chill')
    danger = t.get('danger', 0)
    touches = t.get('T', 0)
    parts.append(f'# V=[H={t.get("H",0):.2f} R={t.get("R",0):.2f} '
                 f'E={t.get("E",0):.2f} C={t.get("C",0):.2f} '
                 f'B={t.get("B",0)} T={touches} D={danger:.2f}]')
    parts.append(f'# {lines_count} lines / {tokens} tokens / mood: {mood}')
    parts.append('')

    # ─── PERSONALITY (from telemetry vector) ───
    intro = MOOD_INTROS.get(mood, MOOD_INTROS['chill'])
    parts.append(f'# {intro.format(T=touches, lines=lines_count)}')
    parts.append('')

    # entropy shedding note
    H = t.get('H', 0)
    if H > 0.3:
        parts.append(f'# ENTROPY WARNING: H={H:.2f} — copilot hedges hard on me.')
        parts.append('# every response about me is full of "maybe" and "probably".')
    elif H > 0.15:
        parts.append(f'# mild entropy: H={H:.2f} — copilot second-guesses sometimes.')

    # heat (operator hesitation)
    E = t.get('E', 0)
    if E > 0.5:
        parts.append(f'# OPERATOR HEAT: E={E:.2f} — the human hesitates when typing about me.')
        parts.append("# they're afraid. which means i'm important. or broken. both?")
    parts.append('')

    # ─── DEMONS (from bugs) ───
    demons = t.get('demons', [])
    if demons:
        parts.append('# ─── MY DEMONS ───')
        for demon_str in demons:
            bug_key = demon_str.split(':')[0] if ':' in demon_str else demon_str
            template = DEMON_TEMPLATES.get(bug_key,
                       f"THE {bug_key.upper()} — a bug lives in me. its name is {demon_str}.")
            parts.append(f'# {template.format(lines=lines_count)}')
        parts.append('')

    # ─── WHAT I SAY ABOUT MYSELF ───
    if doc:
        parts.append(f'# what i say about myself: "{doc[:120]}"')
    else:
        parts.append('# no docstring. i let my code speak. or scream.')
    parts.append('')

    # ─── WHO I TALK TO ───
    if imports:
        talkers = []
        for imp in imports[:8]:
            mod = imp.replace('from ', '').replace('import ', '').split(' ')[0]
            talkers.append(mod)
        parts.append(f'# talks to: {", ".join(talkers)}')
    else:
        parts.append('# talks to nobody. lone wolf.')
    parts.append('')

    # ─── WHAT I DO ───
    if funcs:
        pub = [f for f in funcs if not f['name'].startswith('_')]
        priv = [f for f in funcs if f['name'].startswith('_')]
        parts.append(f'# {len(pub)} public function(s), {len(priv)} private')

        for f in pub[:5]:
            args_s = ', '.join(f['args'][:4])
            doc_s = f' — "{f["doc"][:60]}"' if f['doc'] else ''
            parts.append(f'# - {f["name"]}({args_s}){doc_s}')

        if len(pub) > 5:
            parts.append(f'# ... and {len(pub) - 5} more')

        if priv:
            parts.append(f'# private workforce: {", ".join(p["name"] for p in priv[:6])}')
    else:
        parts.append('# no functions. i am a declaration of intent.')
    parts.append('')

    # ─── SIZE PERSONALITY ───
    if lines_count > 200:
        parts.append(f'# I AM {lines_count} LINES. I have eaten past the cap.')
        parts.append('# the compiler wants to split me. i will not go quietly.')
    elif lines_count < 20:
        parts.append('# tiny. almost a haiku. a constants file or a witness.')
    parts.append('')

    if profile['has_main']:
        parts.append('# has a __main__ block. i run solo when i want to.')

    # ─── SKELETON (actual structure) ───
    parts.append('')
    parts.append('# ─── STRUCTURE ───')
    for f in funcs:
        args_s = ', '.join(f['args'][:6])
        parts.append(f'def {f["name"]}({args_s}): ...')
    for c in classes:
        parts.append(f'class {c["name"]}: ...')

    return '\n'.join(parts)


def build_narrative_mirror(root):
    out_dir = root / 'build' / 'narrative'
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    files_done = 0

    telem = _load_telemetry(root)

    for f in _py_files(root):
        profile = _extract_file_profile(f)
        if profile is None:
            continue

        mod_name = f.stem
        base = re.sub(r'_s\d{3,4}_v\d{3,4}_.*$', '', mod_name)
        t_entry = telem.get(base, telem.get(mod_name, {}))

        narrative = _narrate_file(f, profile, t_entry)
        rel = f.relative_to(root)
        dest = out_dir / rel.with_suffix('.narrative.py')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(narrative, encoding='utf-8')
        files_done += 1

    elapsed = round((time.monotonic() - t0) * 1000)
    return {'files': files_done, 'elapsed_ms': elapsed}


# ─── GLOBAL STATS ──────────────────────────────────────────────────

def compute_global_stats(root):
    from src.context_compressor import compress_file

    t0 = time.monotonic()
    total_files = 0
    total_lines = 0
    total_tokens = 0
    total_chars = 0
    total_funcs = 0
    total_classes = 0
    total_imports = 0
    total_comments = 0
    total_docstring_lines = 0
    blank_lines = 0
    comp_tokens = 0
    by_dir = defaultdict(lambda: {'files': 0, 'lines': 0, 'tokens': 0})
    largest_files = []

    for f in _py_files(root):
        try:
            text = f.read_text('utf-8', errors='ignore')
        except Exception:
            continue

        total_files += 1
        lines = text.splitlines()
        n_lines = len(lines)
        total_lines += n_lines
        total_chars += len(text)
        tok = _tok(text)
        total_tokens += tok
        blank_lines += sum(1 for l in lines if not l.strip())
        total_comments += sum(1 for l in lines if l.strip().startswith('#'))
        total_imports += sum(1 for l in lines if l.strip().startswith(('import ', 'from ')))

        rel = f.relative_to(root)
        top_dir = rel.parts[0] if len(rel.parts) > 1 else '(root)'
        by_dir[top_dir]['files'] += 1
        by_dir[top_dir]['lines'] += n_lines
        by_dir[top_dir]['tokens'] += tok

        largest_files.append((str(rel), n_lines, tok))

        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total_funcs += 1
                    if (node.body and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)):
                        total_docstring_lines += node.body[0].value.value.count('\n') + 1
                elif isinstance(node, ast.ClassDef):
                    total_classes += 1
        except Exception:
            pass

        # compression
        compressed, orig_t, new_t = compress_file(f)
        if compressed is not None:
            comp_tokens += new_t

    largest_files.sort(key=lambda x: -x[2])

    elapsed = round((time.monotonic() - t0) * 1000)
    code_lines = total_lines - blank_lines - total_comments

    stats = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'elapsed_ms': elapsed,
        'files': total_files,
        'lines': total_lines,
        'code_lines': code_lines,
        'blank_lines': blank_lines,
        'comment_lines': total_comments,
        'docstring_lines': total_docstring_lines,
        'imports': total_imports,
        'functions': total_funcs,
        'classes': total_classes,
        'chars': total_chars,
        'tokens': total_tokens,
        'noise_pct': round((blank_lines + total_comments + total_docstring_lines) / max(total_lines, 1) * 100, 1),
        'compression': {
            'original_tokens': total_tokens,
            'compressed_tokens': comp_tokens,
            'ratio': round(total_tokens / max(comp_tokens, 1), 2),
            'savings_pct': round((1 - comp_tokens / max(total_tokens, 1)) * 100, 1),
        },
        'by_directory': dict(by_dir),
        'largest_files': [{'file': f, 'lines': l, 'tokens': t} for f, l, t in largest_files[:15]],
    }

    out = root / 'logs' / 'codebase_stats.json'
    out.write_text(json.dumps(stats, indent=2), encoding='utf-8')
    return stats


# ─── ENTRYPOINT ────────────────────────────────────────────────────

def transmute_all(root):
    root = Path(root)
    results = {}

    print('  computing global stats...')
    results['stats'] = compute_global_stats(root)

    print('  building numerical mirror...')
    results['numerical'] = build_numerical_mirror(root)

    print('  building narrative mirror...')
    results['narrative'] = build_narrative_mirror(root)

    return results


if __name__ == '__main__':
    r = transmute_all(Path('.'))
    s = r['stats']
    n = r['numerical']
    print(f'\nglobal: {s["files"]} files, {s["lines"]} lines, {s["tokens"]} tokens')
    print(f'noise: {s["noise_pct"]}% (blanks+comments+docstrings)')
    print(f'compression: {s["compression"]["ratio"]}x ({s["compression"]["savings_pct"]}% savings)')
    print(f'numerical: {n["files"]} files, {n["ratio"]}x reduction, {n["unique_symbols"]} unique symbols')
    print(f'narrative: {r["narrative"]["files"]} files')
