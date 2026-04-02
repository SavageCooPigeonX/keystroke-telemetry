"""file_consciousness_seq019_helpers_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 63 lines | ~500 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
import ast
import re

def _safe_hes(hm: dict) -> float:
    """Extract average hesitation from heat map entry (handles both schemas)."""
    if not isinstance(hm, dict) or not hm:
        return 0.0
    samp = hm.get('samples', [])
    if isinstance(samp, list):
        n = len(samp)
        if n == 0:
            return 0.0
        return round(sum(s.get('hes', 0) for s in samp) / n, 3)
    # Numeric samples count (aggregated schema)
    n = max(int(samp), 1)
    return round(hm.get('total_hes', 0) / n, 3)


def _call_target(node: ast.Call) -> str:
    """Extract call target name (handles simple + attribute calls)."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            return f'{node.func.value.id}.{node.func.attr}'
        return node.func.attr
    return ''


def _const_value(node) -> str | None:
    """Try to extract a constant string value from an AST node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _type_hint(node) -> str:
    """Rough type description for a return value AST node."""
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    if isinstance(node, ast.Dict):
        return 'dict'
    if isinstance(node, ast.List):
        return 'list'
    if isinstance(node, ast.Tuple):
        return 'tuple'
    if isinstance(node, ast.JoinedStr):
        return 'str'
    if isinstance(node, ast.Call):
        return _call_target(node) or 'call'
    return 'value'


def _count_flags(lines: list[str]) -> int:
    """Count TODO/FIXME/HACK/BUG/XXX markers."""
    count = 0
    for line in lines:
        for marker in ('TODO', 'FIXME', 'HACK', 'BUG', 'XXX'):
            if marker in line:
                count += 1
                break
    return count
