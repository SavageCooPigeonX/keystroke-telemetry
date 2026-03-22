"""compliance_seq008_audit_wrapper_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re
from .compliance_seq008_constants_seq001_v001 import MAX_LINES, WARN_LINES, SKIP_DIRS
from .compliance_seq008_helpers_seq002_v001 import _should_skip
from .compliance_seq008_classify_seq003_v001 import _classify
from .compliance_seq008_recommend_wrapper_seq006_v001 import _recommend_splits

def audit_compliance(root: Path) -> dict:
    """Full codebase line-count audit.

    Returns {
        'total': int,
        'compliant': int,
        'oversize': [{path, lines, status, splits}],
        'by_folder': {folder: {total, compliant, files}},
    }
    """
    root = Path(root)
    total = 0
    compliant = 0
    oversize = []
    by_folder = {}

    for py in sorted(root.rglob('*.py')):
        if _should_skip(py, root):
            continue
        if py.name == '__init__.py':
            continue

        try:
            text = py.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        lc = len(text.splitlines())
        total += 1
        rel = str(py.relative_to(root)).replace('\\', '/')
        folder = str(py.parent.relative_to(root)).replace('\\', '/')

        # Track by folder
        if folder not in by_folder:
            by_folder[folder] = {'total': 0, 'compliant': 0, 'files': []}
        by_folder[folder]['total'] += 1
        by_folder[folder]['files'].append({'name': py.name, 'lines': lc})

        if lc <= MAX_LINES:
            compliant += 1
            by_folder[folder]['compliant'] += 1
        else:
            status = _classify(lc)
            splits = _recommend_splits(text, lc) if lc > WARN_LINES else []
            oversize.append({
                'path': rel,
                'lines': lc,
                'status': status,
                'splits': splits,
            })

    oversize.sort(key=lambda x: -x['lines'])

    return {
        'total': total,
        'compliant': compliant,
        'compliance_pct': round(compliant / max(total, 1) * 100, 1),
        'oversize': oversize,
        'by_folder': by_folder,
    }
