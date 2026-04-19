"""Glyph compiler v2: AST-based token-optimal Python compression.

Full AST transform — not regex. Output is valid Python.
All meaning lives in the companion dictionary.

Strategy:
  - Strip docstrings, comments, type annotations, blank lines
  - Rename ALL functions/classes/params/variables to short ASCII
  - Keep Python builtins and keywords untouched
  - self -> S (consistent)
  - Cross-file context chains in dictionary
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──


from __future__ import annotations
import ast
import builtins
import json
import re
import sys
import keyword
from pathlib import Path
from collections import OrderedDict

_LETTERS = list('abcdefghijklmnopqrstuvwxyz')

def _pool_name(idx: int) -> str:
    if idx < 26:
        return _LETTERS[idx]
    q, r = divmod(idx, 26)
    return _LETTERS[q - 1] + _LETTERS[r]

_BUILTIN_NAMES = set(dir(builtins))
_RESERVED = set(keyword.kwlist) | _BUILTIN_NAMES | {
    'self', 'cls', 'S', 'super',
    '__init__', '__str__', '__repr__', '__enter__', '__exit__',
    '__len__', '__getitem__', '__setitem__', '__delitem__',
    '__iter__', '__next__', '__call__', '__eq__', '__hash__',
    '__contains__', '__bool__', '__lt__', '__gt__', '__le__', '__ge__',
    '__add__', '__sub__', '__mul__', '__truediv__', '__mod__',
    '__name__', '__file__', '__main__', '__all__', '__doc__',
    '__class__', '__dict__', '__slots__', '__new__', '__del__',
    'dataclass', 'field',
}

def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class NameCollector(ast.NodeVisitor):
    """Walk AST, collect all user-defined names by category."""

    def __init__(self):
        self.functions = []
        self.classes = []
        self.params = {}
        self.locals = {}
        self._current_func = None

    def visit_FunctionDef(self, node):
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_func(node)

    def _visit_func(self, node):
        if node.name not in _RESERVED:
            self.functions.append(node.name)
        old = self._current_func
        self._current_func = node.name
        self.params[node.name] = []
        self.locals.setdefault(node.name, [])
        for a in node.args.args + node.args.kwonlyargs:
            if a.arg not in ('self', 'cls') and a.arg not in _RESERVED:
                self.params[node.name].append(a.arg)
        if node.args.vararg and node.args.vararg.arg not in _RESERVED:
            self.params[node.name].append(node.args.vararg.arg)
        if node.args.kwarg and node.args.kwarg.arg not in _RESERVED:
            self.params[node.name].append(node.args.kwarg.arg)
        self.generic_visit(node)
        self._current_func = old

    def visit_ClassDef(self, node):
        if node.name not in _RESERVED:
            self.classes.append(node.name)
        old = self._current_func
        self._current_func = None
        self.generic_visit(node)
        self._current_func = old

    def visit_Assign(self, node):
        self._collect_targets(node.targets)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if isinstance(node.target, ast.Name) and self._current_func:
            self._add_local(node.target.id)
        self.generic_visit(node)

    def visit_For(self, node):
        self._collect_target(node.target)
        self.generic_visit(node)

    visit_AsyncFor = visit_For

    def visit_With(self, node):
        for item in node.items:
            if item.optional_vars:
                self._collect_target(item.optional_vars)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.name and self._current_func:
            self._add_local(node.name)
        self.generic_visit(node)

    def _collect_targets(self, targets):
        for t in targets:
            self._collect_target(t)

    def _collect_target(self, t):
        if isinstance(t, ast.Name) and self._current_func:
            self._add_local(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                self._collect_target(e)

    def _add_local(self, name):
        if name not in _RESERVED and self._current_func:
            self.locals.setdefault(self._current_func, [])
            if name not in self.locals[self._current_func]:
                self.locals[self._current_func].append(name)


class NameTransformer(ast.NodeTransformer):
    """Renames all user-defined identifiers using short ASCII names."""

    def __init__(self, func_map, class_map, per_func_maps):
        self.func_map = func_map
        self.class_map = class_map
        self.per_func_maps = per_func_maps
        self._current_func = None
        self._current_class = None

    def visit_FunctionDef(self, node):
        return self._transform_func(node)

    def visit_AsyncFunctionDef(self, node):
        return self._transform_func(node)

    def _transform_func(self, node):
        old_func = self._current_func
        self._current_func = node.name
        node.name = self.func_map.get(node.name, node.name)
        vmap = self.per_func_maps.get(self._current_func, {})
        for a in node.args.args + node.args.kwonlyargs:
            a.arg = 'S' if a.arg == 'self' else vmap.get(a.arg, a.arg)
            a.annotation = None
        if node.args.vararg:
            node.args.vararg.arg = vmap.get(node.args.vararg.arg, node.args.vararg.arg)
            node.args.vararg.annotation = None
        if node.args.kwarg:
            node.args.kwarg.arg = vmap.get(node.args.kwarg.arg, node.args.kwarg.arg)
            node.args.kwarg.annotation = None
        node.returns = None
        # Strip docstring
        if (node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            node.body = node.body[1:] or [ast.Pass()]
        self.generic_visit(node)
        self._current_func = old_func
        return node

    def visit_ClassDef(self, node):
        old_class = self._current_class
        self._current_class = node.name
        node.name = self.class_map.get(node.name, node.name)
        if (node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            node.body = node.body[1:] or [ast.Pass()]
        self.generic_visit(node)
        self._current_class = old_class
        return node

    def visit_Name(self, node):
        vmap = self.per_func_maps.get(self._current_func, {}) if self._current_func else {}
        if node.id == 'self':
            node.id = 'S'
        elif node.id in vmap:
            node.id = vmap[node.id]
        elif node.id in self.func_map:
            node.id = self.func_map[node.id]
        elif node.id in self.class_map:
            node.id = self.class_map[node.id]
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        if node.value:
            return ast.Assign(
                targets=[node.target],
                value=node.value,
                lineno=node.lineno, col_offset=node.col_offset
            )
        return node

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        self.generic_visit(node)
        return node

    def visit_Import(self, node):
        return node

    def visit_ImportFrom(self, node):
        return node

    def visit_ExceptHandler(self, node):
        if node.name and self._current_func:
            vmap = self.per_func_maps.get(self._current_func, {})
            node.name = vmap.get(node.name, node.name)
        self.generic_visit(node)
        return node


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
    lines = source.splitlines()
    out = []
    prev_blank = False
    for line in lines:
        if not line.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        out.append(line)
    return '\n'.join(out)


def build_import_graph(root):
    skip = {'.git', '__pycache__', '.venv', 'venv', 'node_modules',
            '.egg-info', 'pigeon_code.egg-info'}
    graph = {}
    py_files = [py for py in root.rglob('*.py')
                if not any(s in py.parts for s in skip)]

    for py in py_files:
        stem = py.stem
        base = re.sub(r'_seq\d+.*$', '', stem)
        try:
            src = py.read_text('utf-8', errors='ignore')
            tree = ast.parse(src)
        except Exception:
            continue

        outbound = []
        imported_names = {}
        exported = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                leaf = node.module.split('.')[-1]
                leaf_base = re.sub(r'_seq\d+.*$', '', leaf)
                outbound.append(leaf_base)
                names = [a.name for a in (node.names or [])]
                imported_names[leaf_base] = names
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    leaf = alias.name.split('.')[-1]
                    leaf_base = re.sub(r'_seq\d+.*$', '', leaf)
                    outbound.append(leaf_base)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                exported.append(node.name)
            elif isinstance(node, ast.ClassDef):
                exported.append(node.name)

        graph[base] = {
            'outbound': sorted(set(outbound)),
            'inbound': [],
            'exported_names': exported,
            'imported_names': imported_names,
            'path': str(py.relative_to(root)),
        }

    for stem, info in graph.items():
        for dep in info['outbound']:
            if dep in graph:
                graph[dep]['inbound'].append(stem)
    for info in graph.values():
        info['inbound'] = sorted(set(info['inbound']))

    return graph


class GlyphCompilerV2:

    def __init__(self, root, import_graph=None):
        self.root = root
        self.import_graph = import_graph or {}
        self.mod_glyphs = self._load_mod_glyphs()

    def _load_mod_glyphs(self):
        pgd = self.root / 'dictionary.pgd'
        if not pgd.exists():
            return {}
        data = json.loads(pgd.read_text('utf-8'))
        mg = data.get('module_glyphs', {})
        return {v: k for k, v in mg.items()}

    def compile_file(self, filepath):
        try:
            text = filepath.read_text('utf-8')
        except Exception:
            return '', {}, 0, 0

        orig_tokens = _approx_tokens(text)
        cleaned = _strip_comments(text)

        try:
            tree = ast.parse(cleaned)
        except SyntaxError:
            return '', {}, 0, 0

        collector = NameCollector()
        collector.visit(tree)

        func_map = OrderedDict()
        class_map = OrderedDict()
        per_func_maps = {}

        idx = 0
        for fname in collector.functions:
            if fname not in _RESERVED and fname not in func_map:
                func_map[fname] = _pool_name(idx)
                idx += 1

        cidx = 0
        for cname in collector.classes:
            if cname not in _RESERVED and cname not in class_map:
                g = _pool_name(cidx).upper()
                class_map[cname] = g
                cidx += 1

        for func_name in list(collector.params.keys()):
            vmap = {}
            vidx = 0
            for p in collector.params.get(func_name, []):
                if p not in _RESERVED and p not in vmap:
                    vmap[p] = _pool_name(vidx)
                    vidx += 1
            for v in collector.locals.get(func_name, []):
                if v not in _RESERVED and v not in vmap:
                    vmap[v] = _pool_name(vidx)
                    vidx += 1
            per_func_maps[func_name] = vmap

        transformer = NameTransformer(func_map, class_map, per_func_maps)
        transformed = transformer.visit(tree)
        ast.fix_missing_locations(transformed)

        try:
            compressed = ast.unparse(transformed)
        except Exception:
            return '', {}, 0, 0

        compressed = _collapse_blanks(compressed)
        new_tokens = _approx_tokens(compressed)

        stem = filepath.stem
        base = re.sub(r'_seq\d+.*$', '', stem)
        mod_g = self.mod_glyphs.get(base, base)
        dict_entries = self._build_context_dict(
            filepath, base, mod_g, func_map, class_map, per_func_maps
        )

        return compressed, dict_entries, orig_tokens, new_tokens

    def _build_context_dict(self, filepath, base, mod_g,
                            func_map, class_map, per_func_maps):
        entries = OrderedDict()
        ig = self.import_graph.get(base, {})

        inbound = ig.get('inbound', [])
        outbound = ig.get('outbound', [])
        in_glyphs = [self.mod_glyphs.get(m, m) for m in inbound[:8]]
        out_glyphs = [self.mod_glyphs.get(m, m) for m in outbound[:8]]

        ctx = []
        if in_glyphs:
            ctx.append('in:' + ','.join(in_glyphs))
        if out_glyphs:
            ctx.append('out:' + ','.join(out_glyphs))
        entries['__' + mod_g] = (base + ' [' + ' | '.join(ctx) + ']') if ctx else base

        imported_by = {}
        for importer, info in self.import_graph.items():
            for dep_mod, names in info.get('imported_names', {}).items():
                if dep_mod == base:
                    for n in names:
                        imported_by.setdefault(n, []).append(importer)

        for fname, fid in func_map.items():
            consumers = imported_by.get(fname, [])
            consumer_glyphs = [self.mod_glyphs.get(c, c) for c in consumers[:5]]
            parts = [fname]
            if consumer_glyphs:
                parts.append('used_by:' + ','.join(consumer_glyphs))
            scope = per_func_maps.get(fname, {})
            if scope:
                params = [gid + '=' + name for name, gid in list(scope.items())[:6]]
                parts.append('(' + ', '.join(params) + ')')
            entries[mod_g + '.' + fid] = ' | '.join(parts)

        for cname, cid in class_map.items():
            consumers = imported_by.get(cname, [])
            consumer_glyphs = [self.mod_glyphs.get(c, c) for c in consumers[:5]]
            parts = [cname]
            if consumer_glyphs:
                parts.append('used_by:' + ','.join(consumer_glyphs))
            entries[mod_g + '.' + cid] = ' | '.join(parts)

        return entries


def compile_codebase(root, out_dir=None):
    if out_dir is None:
        out_dir = root / 'build' / 'compressed'
    out_dir.mkdir(parents=True, exist_ok=True)

    print('Building cross-file import graph...')
    ig = build_import_graph(root)
    print(f'  {len(ig)} modules mapped')

    skip = {'.git', '__pycache__', '.venv', 'venv', 'node_modules',
            '.egg-info', 'pigeon_code.egg-info', 'build'}
    py_files = [py for py in root.rglob('*.py')
                if not any(s in py.parts for s in skip)]

    compiler = GlyphCompilerV2(root, ig)
    total_orig = 0
    total_new = 0
    total_dict_entries = OrderedDict()
    file_stats = []

    print(f'Compiling {len(py_files)} files...')
    for py in sorted(py_files):
        compressed, entries, orig_tok, new_tok = compiler.compile_file(py)
        if not compressed:
            continue
        total_orig += orig_tok
        total_new += new_tok
        total_dict_entries.update(entries)
        rel = py.relative_to(root)
        out_path = out_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(compressed, 'utf-8')
        ratio = orig_tok / new_tok if new_tok > 0 else 0
        file_stats.append({
            'file': str(rel),
            'orig_tokens': orig_tok,
            'new_tokens': new_tok,
            'ratio': round(ratio, 2),
        })

    dict_path = out_dir / 'DICTIONARY.txt'
    dict_lines = ['[PIGEON DICTIONARY — CONTEXT-CHAINED]', '']
    for key, val in total_dict_entries.items():
        dict_lines.append(key + ' = ' + val)
    dict_text = '\n'.join(dict_lines)
    dict_path.write_text(dict_text, 'utf-8')
    dict_tokens = _approx_tokens(dict_text)

    overall_ratio = total_orig / (total_new + dict_tokens) if (total_new + dict_tokens) > 0 else 0
    stats = {
        'files_compiled': len(file_stats),
        'total_orig_tokens': total_orig,
        'total_compressed_tokens': total_new,
        'dictionary_tokens': dict_tokens,
        'effective_tokens': total_new + dict_tokens,
        'compression_ratio': round(overall_ratio, 2),
        'all_files': sorted(file_stats, key=lambda x: -x['ratio']),
        'top_compressed': sorted(file_stats, key=lambda x: -x['ratio'])[:20],
    }
    stats_path = out_dir / 'STATS.json'
    stats_path.write_text(json.dumps(stats, indent=2), 'utf-8')

    print(f'\n=== COMPRESSION RESULTS ===')
    print(f'Files:      {len(file_stats)}')
    print(f'Original:   {total_orig:,} tokens')
    print(f'Compressed: {total_new:,} tokens')
    print(f'Dictionary: {dict_tokens:,} tokens')
    print(f'Effective:  {total_new + dict_tokens:,} tokens (compressed + dict)')
    print(f'Ratio:      {overall_ratio:.2f}x')
    print(f'\nOutput: {out_dir}')
    print(f'Dictionary: {dict_path}')

    return stats


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    compile_codebase(root)
