"""tc_profile_mine_code_style_compiler_seq029_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 029 | VER: v001 | 149 lines | ~1,583 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from ..tc_constants import ROOT
from collections import Counter
from pathlib import Path
import ast
import re

def _mine_code_style(root: Path | None = None) -> dict:
    """Scan .py files to learn operator's coding style. Zero LLM calls."""
    r = root or ROOT
    style: dict = {
        'preferred_quotes': 'single',
        'uses_type_hints': False,
        'import_style': 'from_x',
        'naming_convention': 'snake_case',
        'avg_func_length': 0,
        'common_patterns': [],
        'top_imports': [],
        'top_decorators': [],
        'top_exceptions': [],
        'var_name_samples': [],
        'func_name_samples': [],
        'error_handling_style': 'bare_except',
        'docstring_rate': 0.0,
        'list_comp_rate': 0.0,
        'fstring_rate': 0.0,
    }
    single_q = 0
    double_q = 0
    type_hint_count = 0
    from_imports = 0
    plain_imports = 0
    func_lengths: list[int] = []
    all_imports: Counter = Counter()
    decorators: Counter = Counter()
    exceptions: Counter = Counter()
    var_names: list[str] = []
    func_names: list[str] = []
    has_doc = 0
    total_funcs = 0
    list_comps = 0
    total_exprs = 0
    fstring_count = 0
    string_count = 0

    # scan src/ files (operator's code, not pigeon_brain/pigeon_compiler infra)
    scan_dirs = [r / 'src', r / 'client']
    py_files = []
    for d in scan_dirs:
        if d.is_dir():
            py_files.extend(f for f in d.iterdir() if f.suffix == '.py' and f.stat().st_size < 20000)
    # also recently modified files at root
    for f in r.iterdir():
        if f.suffix == '.py' and f.stat().st_size < 15000 and f.name.startswith(('test_', '_tmp_')):
            py_files.append(f)
    py_files = py_files[:40]  # cap

    for pf in py_files:
        try:
            src = pf.read_text('utf-8', errors='ignore')
        except Exception:
            continue
        # quote style
        single_q += src.count("'") - src.count("\\'")
        double_q += src.count('"') - src.count('\\"')
        # string patterns
        string_count += len(re.findall(r'["\']', src))
        fstring_count += len(re.findall(r'f["\']', src))
        # list comprehensions
        list_comps += len(re.findall(r'\[.+\bfor\b.+\bin\b', src))
        total_exprs += src.count('\n')
        # parse AST
        try:
            tree = ast.parse(src, filename=str(pf))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                plain_imports += 1
                for alias in node.names:
                    all_imports[alias.name.split('.')[0]] += 1
            elif isinstance(node, ast.ImportFrom):
                from_imports += 1
                if node.module:
                    all_imports[node.module.split('.')[0]] += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_funcs += 1
                func_names.append(node.name)
                # type hints
                if node.returns:
                    type_hint_count += 1
                for arg in node.args.args:
                    if arg.annotation:
                        type_hint_count += 1
                # func length
                if node.body:
                    lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 5
                    func_lengths.append(lines)
                # docstring
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                    has_doc += 1
            elif isinstance(node, ast.ExceptHandler):
                if node.type:
                    if isinstance(node.type, ast.Name):
                        exceptions[node.type.id] += 1
                    elif isinstance(node.type, ast.Attribute):
                        exceptions[node.type.attr] += 1
                else:
                    exceptions['bare'] += 1
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                var_names.append(node.id)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_names.append(target.id)

        # decorators
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators[dec.id] += 1
                    elif isinstance(dec, ast.Attribute):
                        decorators[dec.attr] += 1

    # compile results
    style['preferred_quotes'] = 'double' if double_q > single_q else 'single'
    style['uses_type_hints'] = type_hint_count > total_funcs * 0.3 if total_funcs else False
    if from_imports + plain_imports > 0:
        ratio = from_imports / (from_imports + plain_imports)
        style['import_style'] = 'from_x' if ratio > 0.6 else 'import_x' if ratio < 0.3 else 'mixed'
    # naming convention — check if func_names use camelCase or snake_case
    camel = sum(1 for n in func_names if re.search(r'[a-z][A-Z]', n))
    snake = sum(1 for n in func_names if '_' in n)
    style['naming_convention'] = 'camelCase' if camel > snake else 'snake_case'
    style['avg_func_length'] = round(sum(func_lengths) / len(func_lengths), 1) if func_lengths else 0
    style['top_imports'] = [m for m, _ in all_imports.most_common(10)]
    style['top_decorators'] = [d for d, _ in decorators.most_common(5)]
    style['top_exceptions'] = [e for e, _ in exceptions.most_common(5)]
    style['var_name_samples'] = list(set(var_names))[:20]
    style['func_name_samples'] = list(set(func_names))[:20]
    if exceptions:
        most_exc = exceptions.most_common(1)[0][0]
        style['error_handling_style'] = 'bare_except' if most_exc == 'bare' else f'specific({most_exc})'
    style['docstring_rate'] = round(has_doc / total_funcs, 2) if total_funcs else 0
    style['list_comp_rate'] = round(list_comps / max(total_exprs, 1), 4)
    style['fstring_rate'] = round(fstring_count / max(string_count, 1), 3)
    return style
