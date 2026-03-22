"""heal_seq009_orchestrator_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from pigeon_compiler.rename_engine.compliance_seq008_v004_d0315__line_count_enforcer_split_recommender_lc_verify_pigeon_plugin import (
    audit_compliance,
    check_file,
)
from pigeon_compiler.rename_engine.manifest_builder_seq007_v003_d0314__generate_living_manifest_md_per_lc_desc_upgrade import (
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
