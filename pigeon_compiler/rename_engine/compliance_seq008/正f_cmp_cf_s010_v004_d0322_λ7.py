"""compliance_seq008_check_file_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
import re
from .compliance_seq008_constants_seq001_v001__正审图 import MAX_LINES, WARN_LINES
from .compliance_seq008_classify_seq003_v004_d0322__正审图_auto_extracted_by_pigeon_compiler_lc_stage_78_hook import _classify
from .compliance_seq008_recommend_wrapper_seq006_v004_d0322__正审图_auto_extracted_by_pigeon_compiler_lc_stage_78_hook import _recommend_splits

def check_file(py: Path) -> dict:
    """Check a single file's compliance."""
    try:
        text = py.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return {'path': str(py), 'lines': 0, 'status': 'ERROR'}

    lc = len(text.splitlines())
    status = 'OK' if lc <= MAX_LINES else _classify(lc)
    splits = _recommend_splits(text, lc) if lc > WARN_LINES else []

    return {
        'path': str(py),
        'lines': lc,
        'status': status,
        'splits': splits,
    }
