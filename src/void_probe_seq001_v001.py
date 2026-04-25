"""void_probe — counterfactual contract analysis for a single file.

Given a target python file, enumerate its public contracts (top-level defs/classes
and `from X import Y` exports) and measure, for each contract C:

  blast_radius  = number of other files in src/ that import or reference C
  fragility     = heuristic score — high when C is referenced without a
                  try/except/fallback by any caller
  survivors     = callers that would still work if C disappeared (have fallback)

Output is a list of probe records that can be injected into a DeepSeek prompt
as "here are the things most likely to break if you touch this file".

No LLM calls — pure AST/text analysis. Deterministic. ~<100ms per target.
"""
from __future__ import annotations
import ast
import json
import re
from pathlib import Path
from typing import Any


def _public_symbols(src: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            if name.startswith('_'):
                continue
            kind = 'class' if isinstance(node, ast.ClassDef) else 'func'
            out.append({'name': name, 'kind': kind, 'lineno': node.lineno})
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith('_') and t.id.isupper():
                    out.append({'name': t.id, 'kind': 'const', 'lineno': node.lineno})
    return out


def _find_callers(symbol: str, target_stem: str, search_roots: list[Path]) -> list[dict[str, Any]]:
    """Files that reference `symbol` (excluding the target itself)."""
    pat = re.compile(r'\b' + re.escape(symbol) + r'\b')
    hits: list[dict[str, Any]] = []
    for root in search_roots:
        if not root.exists():
            continue
        for f in root.rglob('*.py'):
            if target_stem in f.name:
                continue
            try:
                txt = f.read_text('utf-8', errors='ignore')
            except Exception:
                continue
            if symbol not in txt:
                continue
            count = len(pat.findall(txt))
            if count == 0:
                continue
            # fragility: references wrapped in try/except?
            has_guard = False
            # cheap check: symbol appears on a line inside a try block
            lines = txt.split('\n')
            in_try = False
            for ln in lines:
                s = ln.strip()
                if s.startswith('try:'):
                    in_try = True
                elif s.startswith(('except', 'finally:')):
                    in_try = False
                if in_try and pat.search(ln):
                    has_guard = True
                    break
            hits.append({
                'file': str(f.relative_to(f.parents[len(f.parts) - len(root.parts) - 1])) if False else f.name,
                'path': str(f),
                'refs': count,
                'guarded': has_guard,
            })
    return hits


def probe_file(target: Path, root: Path, max_symbols: int = 8) -> dict[str, Any]:
    """Run void probes for a single file. Returns a transcript-ready dict."""
    target = Path(target).resolve()
    root = Path(root).resolve()
    if not target.exists():
        return {'error': f'target not found: {target}', 'target': str(target)}

    try:
        src = target.read_text('utf-8', errors='ignore')
    except Exception as e:
        return {'error': f'read failed: {e}', 'target': str(target)}

    symbols = _public_symbols(src)
    target_stem = target.stem
    # search src + scripts + pigeon_compiler + client for callers
    search_roots = [root / 'src', root / 'scripts', root / 'pigeon_compiler', root / 'client']

    probes: list[dict[str, Any]] = []
    for sym in symbols[:max_symbols]:
        callers = _find_callers(sym['name'], target_stem, search_roots)
        blast = sum(c['refs'] for c in callers)
        unguarded = sum(1 for c in callers if not c['guarded'])
        fragility = round(unguarded / max(len(callers), 1), 3) if callers else 0.0
        probes.append({
            'symbol': sym['name'],
            'kind': sym['kind'],
            'lineno': sym['lineno'],
            'blast_radius': blast,
            'caller_files': len(callers),
            'unguarded_callers': unguarded,
            'fragility': fragility,
            'top_callers': [{'file': c['file'], 'refs': c['refs'], 'guarded': c['guarded']}
                            for c in sorted(callers, key=lambda x: -x['refs'])[:5]],
        })

    # sort probes by blast radius * fragility — most fragile high-blast first
    probes.sort(key=lambda p: -(p['blast_radius'] * (0.5 + p['fragility'])))

    total_blast = sum(p['blast_radius'] for p in probes)
    avg_frag = round(sum(p['fragility'] for p in probes) / max(len(probes), 1), 3)

    return {
        'target': str(target.relative_to(root)) if target.is_relative_to(root) else str(target),
        'symbols_probed': len(probes),
        'total_blast_radius': total_blast,
        'avg_fragility': avg_frag,
        'void_stability': round(1.0 - min(avg_frag + min(total_blast / 50.0, 0.5), 1.0), 3),
        'probes': probes,
    }


def format_probe_summary(probe: dict[str, Any]) -> str:
    """Human/LLM-readable summary — fits in a prompt."""
    if 'error' in probe:
        return f"void_probe error: {probe['error']}"
    lines = [
        f"VOID PROBE — {probe['target']}",
        f"  symbols_probed: {probe['symbols_probed']}",
        f"  total_blast_radius: {probe['total_blast_radius']} refs across callers",
        f"  avg_fragility: {probe['avg_fragility']} (0=all guarded, 1=none guarded)",
        f"  void_stability: {probe['void_stability']} (higher = safer to touch)",
        "",
        "  TOP AT-RISK CONTRACTS (what breaks if removed):",
    ]
    for p in probe['probes'][:5]:
        lines.append(
            f"    * {p['kind']} {p['symbol']}:{p['lineno']} "
            f"blast={p['blast_radius']} unguarded={p['unguarded_callers']}/{p['caller_files']} "
            f"frag={p['fragility']}"
        )
        for tc in p['top_callers'][:3]:
            guard = 'guarded' if tc['guarded'] else 'RAW'
            lines.append(f"        <- {tc['file']} ({tc['refs']} refs, {guard})")
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('usage: python void_probe_seq001_v001.py <file.py> [root]')
        sys.exit(1)
    tgt = Path(sys.argv[1])
    rt = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('.').resolve()
    result = probe_file(tgt, rt)
    print(format_probe_summary(result))
    print()
    print(json.dumps(result, indent=2)[:2000])
