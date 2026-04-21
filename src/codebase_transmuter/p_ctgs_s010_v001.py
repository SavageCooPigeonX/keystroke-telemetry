"""codebase_transmuter_seq001_v001_global_stats_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 103 lines | ~913 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter, defaultdict
from datetime import datetime, timezone
import ast
import json
import re
import time

def compute_global_stats(root):
    from src.context_compressor_seq001_v001 import compress_file

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
