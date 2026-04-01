"""self_fix_seq013_run_self_fix_decomposed_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v002 | 63 lines | ~547 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import os
import re

def run_self_fix(
    root: Path,
    registry: dict,
    changed_py: list[str] | None = None,
    intent: str = '',
) -> dict:
    """One-shot cross-file analysis. Returns problem report dict.

    Does NOT loop or auto-fix — produces a report with targeted resolutions.
    """
    reg_list = registry if isinstance(registry, list) else list(registry.values())
    if isinstance(registry, dict) and 'files' in registry:
        reg_list = registry['files']

    all_problems = []
    registry_paths = {e.get('path', '') for e in reg_list}

    # 1. Hardcoded imports (critical — breaks on next rename)
    all_problems.extend(_scan_hardcoded_pigeon_imports(root, registry_paths))

    # 2. Dead exports (unused public functions)
    all_problems.extend(_scan_dead_exports(root, reg_list))

    # 3. Duplicate docstrings
    all_problems.extend(_scan_duplicate_docstrings(root, reg_list))

    # 4. Cross-file coupling
    coupling_problems, import_graph = _scan_cross_file_coupling(root, reg_list)
    all_problems.extend(coupling_problems)

    # 5. Query memory noise
    all_problems.extend(_scan_query_noise(root))

    # 6. Over-hard-cap files (need auto-compile)
    all_problems.extend(_scan_over_hard_cap(root, reg_list))

    # Sort by severity
    sev_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    all_problems.sort(key=lambda p: sev_order.get(p.get('severity', 'info'), 5))

    # Build cross-file context for changed files
    cross_context = {}
    if changed_py:
        for rel in changed_py:
            deps = import_graph.get(rel, set())
            dependents = [f for f, d in import_graph.items() if rel in d]
            if deps or dependents:
                cross_context[rel] = {
                    'imports_from': sorted(deps),
                    'imported_by': sorted(dependents),
                }

    return {
        'problems': all_problems,
        'cross_context': cross_context,
        'total_files_scanned': len(reg_list),
        'import_graph_size': len(import_graph),
    }
