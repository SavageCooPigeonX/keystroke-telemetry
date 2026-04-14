"""引w_ir_s003_v005_d0403_踪稿析_λFX_orchestrator_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 48 lines | ~458 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def rewrite_all_imports(root: Path, import_map: dict,
                        dry_run: bool = False) -> list[dict]:
    """Rewrite imports across the entire project.

    Args:
        root: project root
        import_map: {old_module_path: new_module_path}
        dry_run: if True, compute changes but don't write
    Returns:
        list of change records [{file, old_line, new_line}]
    """
    root = Path(root)
    changes = []
    failures = []
    # Build stem map for broader matching
    stem_map = _build_stem_map(import_map)

    for py in sorted(root.rglob('*.py')):
        if _should_skip(py, root):
            continue
        text = _safe_read(py)
        if not text:
            failures.append({'file': str(py), 'reason': 'read_failed'})
            continue
        # Quick check: does this file reference any old module?
        if not _has_any_reference(text, import_map, stem_map):
            continue
        new_text, file_changes = _rewrite_file(text, import_map, stem_map)
        if file_changes:
            rel = str(py.relative_to(root)).replace('\\', '/')
            for c in file_changes:
                c['file'] = rel
            changes.extend(file_changes)
            if not dry_run:
                try:
                    py.write_text(new_text, encoding='utf-8')
                except Exception as e:
                    failures.append({'file': rel, 'reason': f'write_failed: {e}'})
    if failures:
        import json
        fail_log = root / 'logs' / 'import_rewriter_failures.json'
        fail_log.parent.mkdir(parents=True, exist_ok=True)
        fail_log.write_text(json.dumps(failures, indent=2), encoding='utf-8')
    return changes
