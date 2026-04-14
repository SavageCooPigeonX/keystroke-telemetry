"""批编f_rbc_s015_v002_d0328_织谱建验_λR_scanner_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 51 lines | ~444 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from pigeon_compiler.pigeon_limits import PIGEON_MAX, is_excluded
import sys, argparse, traceback, re

def scan_oversized(root: Path, include_compiler: bool = False) -> list[dict]:
    """Find all oversized .py files in the project.

    Returns list of {path, lines, folder, stem, can_compile} sorted by lines ASC
    (smallest first = easiest to compile first).
    """
    results = []
    for py in sorted(root.rglob("*.py")):
        if any(d in py.parts for d in SKIP_DIRS):
            continue
        if py.name in SKIP_NAMES or py.name == "__init__.py":
            continue
        if is_excluded(py, root):
            continue
        if not include_compiler and any(d in py.parts for d in COMPILER_DIRS):
            continue
        # Don't compile the batch compiler itself
        if "run_batch_compile" in py.stem:
            continue

        try:
            lc = len(py.read_text(encoding="utf-8").splitlines())
        except Exception:
            continue
        if lc <= PIGEON_MAX:
            continue

        rel = py.relative_to(root)
        # Derive the target folder name from the base module stem
        stem = py.stem
        # Strip pigeon decorations: _seqNNN_vNNN_dMMDD__desc_lc_intent
        m = re.match(r"(.+?)_seq\d+", stem)
        base = m.group(1) if m else stem

        results.append({
            "path": py,
            "rel": str(rel),
            "lines": lc,
            "folder": str(rel.parent),
            "stem": stem,
            "base": base,
        })

    # Sort: smallest files first (they compile faster and have fewer deps)
    results.sort(key=lambda r: r["lines"])
    return results
