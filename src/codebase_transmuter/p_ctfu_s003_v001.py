"""codebase_transmuter_seq001_v001_file_utils_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 26 lines | ~213 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _py_files(root):
    for d in PY_DIRS:
        dp = root / d
        if not dp.exists():
            continue
        for f in dp.rglob('*.py'):
            if any(s in f.relative_to(root).parts for s in SKIP_DIRS):
                continue
            yield f


def _tok(text):
    return max(1, int(len(text) / APPROX_CHARS_PER_TOKEN))


def _telemetry_header(mod_name, telem):
    """Returns a numeric vector comment for a file's telemetry."""
    t = telem.get(mod_name, {})
    if not t:
        return '# V=[H=0 R=0 E=0 C=0 B=0 T=0 D=0]'
    return (f'# V=[H={t.get("H", 0):.2f} R={t.get("R", 0):.2f} '
            f'E={t.get("E", 0):.2f} C={t.get("C", 0):.2f} '
            f'B={t.get("B", 0)} T={t.get("T", 0)} D={t.get("danger", 0):.2f}]')
