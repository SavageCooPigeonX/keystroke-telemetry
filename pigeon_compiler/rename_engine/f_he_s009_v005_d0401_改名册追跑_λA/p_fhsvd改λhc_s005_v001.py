"""f_he_s009_v005_d0401_改名册追跑_λA_heal_core_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 90 lines | ~699 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
from pigeon_compiler.rename_engine.正f_cmp_s008_v004_d0315_踪稿析_λν import (
    audit_compliance,
    check_file,
)
from pigeon_compiler.rename_engine.谱建f_mb_s007_v003_d0314_观重箱重拆_λD import (
    build_all_manifests,
    build_manifest,
)
import re

def heal(root: Path, full: bool = False, dry_run: bool = False) -> dict:
    """Run the self-healing pipeline.

    Args:
        root: project root
        full: if True, rebuild ALL manifests (not just changed folders)
        dry_run: if True, compute but don't write
    Returns:
        heal report dict
    """
    root = Path(root)
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'changed_files': [],
        'affected_folders': [],
        'manifests_updated': [],
        'compliance': {},
        'intent_traces': [],
    }

    # 1. Detect changes
    if full:
        changed = _all_py_files(root)
    else:
        changed = _git_changed_files(root)

    report['changed_files'] = changed

    # 2. Find affected folders
    affected = set()
    for f in changed:
        p = Path(f)
        folder = p.parent
        folder_abs = root / folder
        if folder_abs.exists():
            affected.add(str(folder).replace('\\', '/'))
    report['affected_folders'] = sorted(affected)

    # 3. Extract intent traces from changed files
    for f in changed:
        fpath = root / f
        if not fpath.exists() or not fpath.suffix == '.py':
            continue
        trace = _extract_intent(fpath)
        if trace:
            report['intent_traces'].append({
                'file': f,
                'intent': trace,
            })

    # 4. Rebuild manifests for affected folders
    if full:
        results = build_all_manifests(root, dry_run=dry_run)
        report['manifests_updated'] = list(results.keys()) if isinstance(results, dict) else [r.get('folder', '') for r in results]
    else:
        for folder_rel in affected:
            folder_abs = root / folder_rel
            if folder_abs.is_dir():
                build_manifest(folder_abs, root)
                report['manifests_updated'].append(folder_rel)

    # 5. Run compliance check
    compliance = audit_compliance(root)
    report['compliance'] = {
        'total': compliance['total'],
        'compliant': compliance['compliant'],
        'pct': compliance['compliance_pct'],
        'oversize_count': len(compliance['oversize']),
        'critical': [e['path'] for e in compliance['oversize']
                     if e['status'] == 'CRITICAL'],
    }

    # 6. Write heal log
    if not dry_run:
        _write_heal_log(root, report)

    return report
