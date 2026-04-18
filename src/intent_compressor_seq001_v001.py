"""intent_compressor_seq001_v001 — maximum compression with maximum meaning retention.

goes beyond context_compressor_seq001_v001:
  layer 0: strip pigeon headers, pulse blocks, decorative borders (metadata noise)
  layer 1: strip docstrings, type annotations, comments (syntactic noise)
  layer 2: collapse imports to single-line grouped form
  layer 3: skeleton mode — function signatures + first meaningful line only
  layer 4: intent map — pure {name: purpose} extraction, no code at all

each layer is independently measurable. the compressor reports:
  - tokens at each layer
  - meaning retention score (functions preserved / functions original)
  - intent density (functions per 1K tokens)
  - compression ratio vs baseline

designed to run on every push via post-commit hook.
"""

import ast
import json
import math
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── CONSTANTS ─────────────────────────────────────────────────────

APPROX_CHARS_PER_TOKEN = 4.0

SKIP_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'node_modules',
             '.egg-info', 'pigeon_code.egg-info', 'build', 'stress_logs',
             'test_logs', 'demo_logs', 'logs'}

PY_DIRS = ['src', 'pigeon_compiler', 'pigeon_brain', 'streaming_layer', 'client']

# regex patterns for strippable metadata
PIGEON_HEADER_RE = re.compile(
    r'^# @pigeon:.*$|'
    r'^# ── pigeon ─+$|'
    r'^# SEQ:.*$|^# VER:.*$|^# DESC:.*$|^# INTENT:.*$|'
    r'^# LAST:.*$|^# SESSIONS:.*$|'
    r'^# ─+$',
    re.MULTILINE,
)

PULSE_BLOCK_RE = re.compile(
    r'^# ── telemetry:pulse ──\n'
    r'(?:# .*\n)*'
    r'# ── /pulse ──$',
    re.MULTILINE,
)

BORDER_RE = re.compile(r'^# ─{3,}.*$', re.MULTILINE)


def _tok(text: str) -> int:
    return max(1, int(len(text) / APPROX_CHARS_PER_TOKEN))


# ─── LAYER 0: METADATA STRIP ──────────────────────────────────────

def strip_metadata(source: str) -> str:
    """Remove pigeon headers, pulse blocks, decorative borders."""
    result = PULSE_BLOCK_RE.sub('', source)
    result = PIGEON_HEADER_RE.sub('', result)
    result = BORDER_RE.sub('', result)
    # collapse resulting blank runs
    lines = []
    prev_blank = False
    for line in result.splitlines():
        if not line.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        lines.append(line)
    return '\n'.join(lines)


# ─── LAYER 1: SYNTACTIC STRIP ─────────────────────────────────────

def strip_syntactic_noise(source: str) -> str:
    """Remove docstrings, type annotations, inline comments."""
    # strip comments first (preserves parseable code)
    lines = []
    for line in source.splitlines():
        s = line.lstrip()
        if s.startswith('#'):
            if s.startswith('#!') or 'coding' in s:
                lines.append(line)
            continue
        if '  #' in line:
            idx = line.index('  #')
            before = line[:idx]
            if before.count("'") % 2 == 0 and before.count('"') % 2 == 0:
                line = before.rstrip()
        lines.append(line)
    cleaned = '\n'.join(lines)

    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return cleaned

    # strip docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body[0] = ast.Pass()

    # strip type annotations
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.returns = None
            for arg in (node.args.args + node.args.posonlyargs +
                        node.args.kwonlyargs):
                arg.annotation = None
            if node.args.vararg:
                node.args.vararg.annotation = None
            if node.args.kwarg:
                node.args.kwarg.annotation = None
        elif isinstance(node, ast.AnnAssign):
            node.annotation = ast.Constant(value=0)

    ast.fix_missing_locations(tree)
    try:
        result = ast.unparse(tree)
    except Exception:
        return cleaned

    # collapse blanks
    out = []
    prev_blank = False
    for line in result.splitlines():
        if not line.strip():
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        out.append(line)
    return '\n'.join(out)


# ─── LAYER 2: IMPORT COLLAPSE ─────────────────────────────────────

def collapse_imports(source: str) -> str:
    """Group imports into single-line form, dedup."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    imports = []
    from_imports = defaultdict(set)
    non_import_lines = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ''
            for alias in node.names:
                from_imports[mod].add(alias.name)
        else:
            non_import_lines.append(ast.unparse(node))

    lines = []
    if imports:
        lines.append(f"import {', '.join(sorted(set(imports)))}")
    for mod in sorted(from_imports):
        names = ', '.join(sorted(from_imports[mod]))
        lines.append(f"from {mod} import {names}")
    lines.append('')
    lines.extend(non_import_lines)
    return '\n'.join(lines)


# ─── LAYER 3: SKELETON MODE ───────────────────────────────────────

def skeleton(source: str) -> str:
    """Extract function/class signatures + first meaningful statement only."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    lines = []

    # imports (collapsed)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            lines.append(ast.unparse(node))

    if lines:
        lines.append('')

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            bases = ', '.join(ast.unparse(b) for b in node.bases) if node.bases else ''
            base_s = f'({bases})' if bases else ''
            lines.append(f'class {node.name}{base_s}:')
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sig = _func_sig(item)
                    first = _first_meaningful(item)
                    lines.append(f'  {sig}')
                    if first:
                        lines.append(f'    {first}')
            lines.append('')

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sig = _func_sig(node)
            first = _first_meaningful(node)
            lines.append(sig)
            if first:
                lines.append(f'  {first}')
            lines.append('')

        elif isinstance(node, ast.Assign):
            # top-level constants
            try:
                lines.append(ast.unparse(node))
            except Exception:
                pass

    return '\n'.join(lines)


def _func_sig(node) -> str:
    prefix = 'async def' if isinstance(node, ast.AsyncFunctionDef) else 'def'
    args = ast.unparse(node.args) if node.args else ''
    return f'{prefix} {node.name}({args}):'


def _first_meaningful(node) -> str:
    """Get first non-pass, non-docstring statement."""
    for stmt in node.body:
        if isinstance(stmt, ast.Pass):
            continue
        if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)):
            continue
        try:
            unparsed = ast.unparse(stmt)
            if len(unparsed) > 120:
                return unparsed[:117] + '...'
            return unparsed
        except Exception:
            return '...'
    return '...'


# ─── LAYER 4: INTENT MAP ──────────────────────────────────────────

def intent_map(source: str, filename: str = '') -> dict:
    """Pure intent extraction — no code, just {name: purpose, calls, returns}."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {'error': 'parse_failed', 'file': filename}

    intents = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = set()
            returns_vals = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        calls.add(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        calls.add(child.func.attr)
                if isinstance(child, ast.Return) and child.value:
                    try:
                        returns_vals.append(ast.unparse(child.value)[:60])
                    except Exception:
                        pass
            intents.append({
                'name': node.name,
                'args': [a.arg for a in node.args.args],
                'calls': sorted(calls)[:10],
                'returns': returns_vals[:3],
                'lines': node.end_lineno - node.lineno + 1 if node.end_lineno else 0,
            })

    return {
        'file': filename,
        'functions': len(intents),
        'intents': intents,
    }


# ─── FULL PIPELINE ────────────────────────────────────────────────

@dataclass
class CompressionResult:
    file: str = ''
    original_tokens: int = 0
    layer0_tokens: int = 0  # metadata stripped
    layer1_tokens: int = 0  # syntactic stripped
    layer2_tokens: int = 0  # imports collapsed
    layer3_tokens: int = 0  # skeleton only
    layer4_entries: int = 0  # intent map entries
    functions: int = 0
    classes: int = 0
    imports: int = 0
    semantic_density: float = 0.0
    intent_density_original: float = 0.0  # funcs per 1K tok
    intent_density_skeleton: float = 0.0  # funcs per 1K tok (compressed)
    max_compression_ratio: float = 0.0
    noise_pct: float = 0.0


def compress_file(filepath: Path, root: Path | None = None) -> CompressionResult:
    """Run full 5-layer compression pipeline on a single file."""
    try:
        source = filepath.read_text('utf-8', errors='ignore')
    except Exception:
        return CompressionResult(file=str(filepath))

    rel = str(filepath.relative_to(root)) if root else str(filepath)
    orig_tok = _tok(source)

    # layer 0: metadata
    l0 = strip_metadata(source)
    l0_tok = _tok(l0)

    # layer 1: syntactic
    l1 = strip_syntactic_noise(l0)
    l1_tok = _tok(l1)

    # layer 2: import collapse
    l2 = collapse_imports(l1)
    l2_tok = _tok(l2)

    # layer 3: skeleton
    l3 = skeleton(source)  # from original — skeleton is independent
    l3_tok = _tok(l3)

    # layer 4: intent map
    imap = intent_map(source, rel)
    l4_entries = len(imap.get('intents', []))

    # count AST elements
    try:
        tree = ast.parse(source)
        funcs = sum(1 for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        imports = sum(1 for n in ast.walk(tree)
                      if isinstance(n, (ast.Import, ast.ImportFrom)))
    except SyntaxError:
        funcs = classes = imports = 0

    sem_density = l1_tok / max(orig_tok, 1)
    i_orig = (funcs / max(orig_tok / 1000, 0.001))
    i_skel = (funcs / max(l3_tok / 1000, 0.001))
    max_ratio = orig_tok / max(l3_tok, 1)
    noise = 1.0 - sem_density

    return CompressionResult(
        file=rel,
        original_tokens=orig_tok,
        layer0_tokens=l0_tok,
        layer1_tokens=l1_tok,
        layer2_tokens=l2_tok,
        layer3_tokens=l3_tok,
        layer4_entries=l4_entries,
        functions=funcs,
        classes=classes,
        imports=imports,
        semantic_density=round(sem_density, 4),
        intent_density_original=round(i_orig, 3),
        intent_density_skeleton=round(i_skel, 3),
        max_compression_ratio=round(max_ratio, 2),
        noise_pct=round(noise * 100, 1),
    )


# ─── BATCH RUNNER ──────────────────────────────────────────────────

def compress_all(root: Path, write_output: bool = True) -> dict:
    """Run compression analysis on all Python files in the repo."""
    root = Path(root)
    t0 = time.monotonic()

    results: list[CompressionResult] = []
    for d in PY_DIRS:
        dpath = root / d
        if not dpath.exists():
            continue
        for f in sorted(dpath.rglob('*.py')):
            if any(s in f.parts for s in SKIP_DIRS):
                continue
            results.append(compress_file(f, root))

    elapsed = time.monotonic() - t0

    # aggregates
    total_orig = sum(r.original_tokens for r in results)
    total_l0 = sum(r.layer0_tokens for r in results)
    total_l1 = sum(r.layer1_tokens for r in results)
    total_l2 = sum(r.layer2_tokens for r in results)
    total_l3 = sum(r.layer3_tokens for r in results)
    total_funcs = sum(r.functions for r in results)
    total_classes = sum(r.classes for r in results)
    total_imports = sum(r.imports for r in results)

    summary = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'elapsed_ms': round(elapsed * 1000),
        'files_scanned': len(results),
        'total_original_tokens': total_orig,
        'compression_layers': {
            'layer0_metadata_strip': {
                'tokens': total_l0,
                'ratio': round(total_orig / max(total_l0, 1), 3),
                'saved_pct': round((total_orig - total_l0) / max(total_orig, 1) * 100, 1),
            },
            'layer1_syntactic_strip': {
                'tokens': total_l1,
                'ratio': round(total_orig / max(total_l1, 1), 3),
                'saved_pct': round((total_orig - total_l1) / max(total_orig, 1) * 100, 1),
            },
            'layer2_import_collapse': {
                'tokens': total_l2,
                'ratio': round(total_orig / max(total_l2, 1), 3),
                'saved_pct': round((total_orig - total_l2) / max(total_orig, 1) * 100, 1),
            },
            'layer3_skeleton': {
                'tokens': total_l3,
                'ratio': round(total_orig / max(total_l3, 1), 3),
                'saved_pct': round((total_orig - total_l3) / max(total_orig, 1) * 100, 1),
            },
        },
        'intent_stats': {
            'total_functions': total_funcs,
            'total_classes': total_classes,
            'total_imports': total_imports,
            'intents_per_1K_original': round(total_funcs / max(total_orig / 1000, 1), 3),
            'intents_per_1K_skeleton': round(total_funcs / max(total_l3 / 1000, 1), 3),
            'intent_amplification': round(
                (total_funcs / max(total_l3, 1)) / max(total_funcs / max(total_orig, 1), 0.0001), 2),
            'meaning_efficiency': round(total_l3 / max(total_orig, 1) * 100, 1),
        },
        'top_compressible': sorted(
            [asdict(r) for r in results if r.original_tokens > 100],
            key=lambda x: -x['noise_pct']
        )[:15],
        'top_dense': sorted(
            [asdict(r) for r in results if r.original_tokens > 100],
            key=lambda x: x['semantic_density']
        )[:15],
        'all_files': [asdict(r) for r in results],
    }

    if write_output:
        out_path = root / 'build' / 'compressed' / 'INTENT_COMPRESSION.json'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')

    return summary


# ─── CLI ───────────────────────────────────────────────────────────

def _print_report(summary: dict) -> None:
    cl = summary['compression_layers']
    ist = summary['intent_stats']

    print(f"{'='*65}")
    print(f"INTENT COMPRESSION REPORT — {summary['files_scanned']} files")
    print(f"{'='*65}")
    print()
    print(f"ORIGINAL:  {summary['total_original_tokens']:>10,} tokens")
    print()
    print("COMPRESSION LAYERS:")
    for name, data in cl.items():
        print(f"  {name:30s} → {data['tokens']:>10,} tok  "
              f"({data['ratio']:.2f}x, -{data['saved_pct']}%)")
    print()
    print("INTENT PAYLOAD:")
    print(f"  Functions:                {ist['total_functions']}")
    print(f"  Classes:                  {ist['total_classes']}")
    print(f"  Imports:                  {ist['total_imports']}")
    print(f"  Intent/Ktok (original):   {ist['intents_per_1K_original']}")
    print(f"  Intent/Ktok (skeleton):   {ist['intents_per_1K_skeleton']}")
    print(f"  Intent amplification:     {ist['intent_amplification']}x")
    print(f"  Meaning efficiency:       {ist['meaning_efficiency']}% of tokens carry all intent")
    print()
    print("MOST COMPRESSIBLE (highest noise):")
    for f in summary['top_compressible'][:10]:
        print(f"  {f['noise_pct']:5.1f}% noise | {f['max_compression_ratio']:5.1f}x max | {f['file'][:55]}")
    print()
    print("MOST DENSE (least compressible — already lean):")
    for f in summary['top_dense'][:10]:
        sd = f['semantic_density']
        print(f"  {sd:.3f} density | {f['intent_density_original']:.2f} i/Kt | {f['file'][:55]}")
    print()
    print(f"Elapsed: {summary['elapsed_ms']}ms")
    print(f"Report: build/compressed/INTENT_COMPRESSION.json")


if __name__ == '__main__':
    summary = compress_all(Path('.'))
    _print_report(summary)
