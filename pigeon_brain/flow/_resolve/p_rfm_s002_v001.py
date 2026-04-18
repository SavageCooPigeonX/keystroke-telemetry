"""_resolve_find_module_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 56 lines | ~530 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _find_module(seq_prefix: str, search_dir: Path | None = None) -> str | None:
    """Find the actual module file matching a seq prefix like 'backward_seq007'.

    Supports both old-style names (backward_seq007_v*.py) and pigeon-style
    names (逆f_ba_s007_v*.py where s007 = seq007).
    """
    if seq_prefix in _CACHE:
        return _CACHE[seq_prefix]

    d = search_dir or _FLOW_DIR
    
    # Extract seq number (e.g., "007" from "backward_seq007")
    seq_match = re.search(r"seq(\d+)$", seq_prefix)
    seq_num = seq_match.group(1) if seq_match else None
    
    # Old-style pattern: backward_seq007_v*
    old_pattern = re.compile(rf"^{re.escape(seq_prefix)}_v\d+", re.IGNORECASE)
    
    # Pigeon-style pattern: *_s007_v* (where 007 is the seq number)
    pigeon_pattern = re.compile(rf"_s0*{seq_num}_v\d+", re.IGNORECASE) if seq_num else None

    # Check for subpackage first (directory with __init__.py)
    for child in d.iterdir():
        if child.is_dir():
            if old_pattern.match(child.name):
                if (child / "__init__.py").exists():
                    _CACHE[seq_prefix] = child.name
                    return child.name
            if pigeon_pattern and pigeon_pattern.search(child.name):
                if (child / "__init__.py").exists():
                    _CACHE[seq_prefix] = child.name
                    return child.name

    # Check for single file
    candidates = []
    for child in d.iterdir():
        if child.suffix == ".py" and child.stem != "__init__" and child.stem != "_resolve":
            if old_pattern.match(child.stem):
                candidates.append(child)
            elif pigeon_pattern and pigeon_pattern.search(child.stem):
                candidates.append(child)
    
    if candidates:
        # Pick newest version
        best = sorted(candidates, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        _CACHE[seq_prefix] = best.stem
        return best.stem

    return None


_FLOW_DIR = Path(__file__).parent
