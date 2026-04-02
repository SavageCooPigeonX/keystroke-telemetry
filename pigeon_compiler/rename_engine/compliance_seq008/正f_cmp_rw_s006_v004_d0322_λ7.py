"""compliance_seq008_recommend_wrapper_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v004 | 69 lines | ~602 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 3
# ──────────────────────────────────────────────
import ast
import re
from .compliance_seq008_helpers_seq002_v004_d0322__正审图_auto_extracted_by_pigeon_compiler_lc_stage_78_hook import _snake

def _recommend_splits(text: str, total_lines: int) -> list[dict]:
    """Find natural split points in a file.

    Returns [{line: int, reason: str, suggested_name: str}]
    """
    splits = []
    lines = text.splitlines()

    # Find class boundaries
    try:
        tree = ast.parse(text)
        classes = [n for n in ast.iter_child_nodes(tree)
                   if isinstance(n, ast.ClassDef)]
        if len(classes) >= 2:
            for cls in classes:
                splits.append({
                    'line': cls.lineno,
                    'reason': f'class {cls.name}',
                    'suggested_name': _snake(cls.name),
                })

        # Find function clusters (groups of 3+ top-level functions)
        funcs = [n for n in ast.iter_child_nodes(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if len(funcs) >= 6:
            # Split at midpoint
            mid = len(funcs) // 2
            split_func = funcs[mid]
            splits.append({
                'line': split_func.lineno,
                'reason': f'function cluster at {split_func.name}()',
                'suggested_name': split_func.name,
            })
    except SyntaxError:
        pass

    # Find section comments (# ── Section ── or # === Section ===)
    section_pat = re.compile(r'^#\s*[═─=\-]{3,}\s*(.+?)\s*[═─=\-]*\s*$')
    for i, line in enumerate(lines, 1):
        m = section_pat.match(line.strip())
        if m:
            splits.append({
                'line': i,
                'reason': f'section: {m.group(1).strip()}',
                'suggested_name': _snake(m.group(1).strip()),
            })

    # Dedupe and sort
    seen_lines = set()
    unique = []
    for s in sorted(splits, key=lambda x: x['line']):
        if s['line'] not in seen_lines:
            seen_lines.add(s['line'])
            unique.append(s)

    return unique
