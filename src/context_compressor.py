"""context_compressor — incremental Python compression for LLM context on push.

strips comments, docstrings, type annotations, collapse blanks.
leaves bare functional minimum — intent-readable code for human-AI sync.
runs per-push on changed files only, merges into build/compressed/.
"""

import ast
import json
import time
from pathlib import Path

SKIP_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'node_modules',
             '.egg-info', 'pigeon_code.egg-info', 'build', 'stress_logs',
             'test_logs', 'demo_logs', 'logs'}

APPROX_CHARS_PER_TOKEN = 4.0


def _approx_tokens(text):
    return max(1, int(len(text) / APPROX_CHARS_PER_TOKEN))


def _strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                node.body[0] = ast.Pass()


def _strip_type_annotations(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.returns = None
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                arg.annotation = None
            if node.args.vararg:
                node.args.vararg.annotation = None
            if node.args.kwarg:
                node.args.kwarg.annotation = None
        elif isinstance(node, ast.AnnAssign):
            node.annotation = ast.Constant(value=0)


def _strip_comments(source):
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith('#'):
            if stripped.startswith('#!') or 'coding' in stripped:
                lines.append(line)
            continue
        if '  #' in line:
            idx = line.index('  #')
            before = line[:idx]
            if before.count("'") % 2 == 0 and before.count('"') % 2 == 0:
                line = before.rstrip()
        lines.append(line)
    return '\n'.join(lines)


def _collapse_blanks(source):
    out = []
    prev_blank = False
    for line in source.splitlines():
        if not line.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        out.append(line)
    return '\n'.join(out)


def compress_file(filepath):
    try:
        text = filepath.read_text('utf-8', errors='ignore')
    except Exception:
        return None, 0, 0

    orig_tokens = _approx_tokens(text)
    cleaned = _strip_comments(text)

    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return None, orig_tokens, 0

    _strip_docstrings(tree)
    _strip_type_annotations(tree)
    ast.fix_missing_locations(tree)

    try:
        compressed = ast.unparse(tree)
    except Exception:
        return None, orig_tokens, 0

    compressed = _collapse_blanks(compressed)
    new_tokens = _approx_tokens(compressed)
    return compressed, orig_tokens, new_tokens


def compress_changed(root, changed_files=None):
    out_dir = root / 'build' / 'compressed'
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.monotonic()

    if changed_files:
        py_files = [root / f for f in changed_files
                    if f.endswith('.py') and (root / f).exists()
                    and not any(s in Path(f).parts for s in SKIP_DIRS)]
    else:
        py_files = [py for py in root.rglob('*.py')
                    if not any(s in py.parts for s in SKIP_DIRS)]

    total_orig = 0
    total_new = 0
    compressed_count = 0

    for py in py_files:
        compressed, orig_tok, new_tok = compress_file(py)
        if compressed is None:
            continue
        total_orig += orig_tok
        total_new += new_tok
        compressed_count += 1
        rel = py.relative_to(root)
        out_path = out_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(compressed, 'utf-8')

    elapsed = time.monotonic() - t0
    ratio = total_orig / total_new if total_new > 0 else 0

    stats_path = out_dir / 'STATS.json'
    existing_stats = {}
    if stats_path.exists():
        try:
            existing_stats = json.loads(stats_path.read_text('utf-8'))
        except Exception:
            pass

    existing_stats.update({
        'last_incremental': {
            'files': compressed_count,
            'orig_tokens': total_orig,
            'compressed_tokens': total_new,
            'ratio': round(ratio, 2),
            'elapsed_ms': round(elapsed * 1000),
        }
    })
    stats_path.write_text(json.dumps(existing_stats, indent=2), 'utf-8')

    return {
        'files': compressed_count,
        'orig_tokens': total_orig,
        'compressed_tokens': total_new,
        'ratio': round(ratio, 2),
        'elapsed_ms': round(elapsed * 1000),
    }
