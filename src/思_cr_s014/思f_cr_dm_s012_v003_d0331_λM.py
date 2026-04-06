"""cognitive_reactor_seq014_decision_maker_seq012 — Patch safety gating.

Decides whether a cognitive patch is safe to auto-apply to source code.
Checks: AST validity, line count cap, no import breakage, no logic changes
on high-coupling modules. Returns a verdict dict.
"""


from __future__ import annotations
import ast
from pathlib import Path

HARD_CAP = 200
COUPLING_FAN_IN_LIMIT = 6


def should_apply_patch(
    root: Path,
    target_path: str,
    new_source: str,
    original_source: str,
    import_graph: dict | None = None,
) -> dict:
    """Decide whether a generated patch is safe to auto-apply.

    Returns:
        {'allow': bool, 'reason': str, 'risk': 'low'|'medium'|'high'}
    """
    fp = Path(root) / target_path

    # 1. AST validity — patch must parse
    try:
        ast.parse(new_source)
    except SyntaxError as e:
        return {'allow': False, 'reason': f'patch has syntax error: {e}', 'risk': 'high'}

    # 2. Line count — must not exceed hard cap
    new_lines = len(new_source.strip().splitlines())
    if new_lines > HARD_CAP:
        return {'allow': False, 'reason': f'patch is {new_lines} lines (cap {HARD_CAP})', 'risk': 'medium'}

    # 3. Size delta — reject patches that change more than 40% of lines
    orig_lines = len(original_source.strip().splitlines()) if original_source else 0
    if orig_lines > 0:
        delta = abs(new_lines - orig_lines)
        if delta / orig_lines > 0.4:
            return {'allow': False, 'reason': f'patch changes {delta}/{orig_lines} lines (>40%)', 'risk': 'high'}

    # 4. Import preservation — new source must keep all original imports
    orig_imports = _extract_imports(original_source)
    new_imports = _extract_imports(new_source)
    dropped = orig_imports - new_imports
    if dropped:
        return {'allow': False, 'reason': f'patch drops imports: {dropped}', 'risk': 'high'}

    # 5. High-coupling guard — don't auto-patch modules with many dependents
    if import_graph:
        dependents = sum(1 for deps in import_graph.values()
                         if target_path in deps or fp.stem in str(deps))
        if dependents >= COUPLING_FAN_IN_LIMIT:
            return {'allow': False, 'reason': f'module has {dependents} dependents (limit {COUPLING_FAN_IN_LIMIT})', 'risk': 'medium'}

    return {'allow': True, 'reason': 'patch passed all safety checks', 'risk': 'low'}


def _extract_imports(source: str) -> set[str]:
    """Extract import module names from source."""
    names = set()
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split('.')[0])
    except Exception:
        pass
    return names

