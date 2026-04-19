"""引w_ir_s003_v005_d0403_踪稿析_λFX_rewrite_line_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 49 lines | ~562 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
from .p_引isvd踪λetm_s002_v001 import _extract_top_module
from .p_引isvd踪λc_s001_v001 import KNOWN_EXTERNAL

def _rewrite_line(line: str, import_map: dict, stem_map: dict) -> str:
    stripped = line.lstrip()
    if not stripped.startswith(('from ', 'import ')):
        return line
    # SAFETY: never touch external package imports
    top_mod = _extract_top_module(stripped)
    if top_mod and top_mod.lower() in KNOWN_EXTERNAL:
        return line
    # Try each old_module → new_module replacement (dotted path in line)
    for old_mod, new_mod in sorted(import_map.items(),
                                   key=lambda item: len(item[0]),
                                   reverse=True):
        if old_mod not in line or old_mod == new_mod:
            continue
        new_line = _replace_exact_module_path(line, old_mod, new_mod)
        if new_line != line:
            return new_line
    # Try stem-based matching for all import styles
    for stem, (old_mod, new_mod) in stem_map.items():
        new_stem = new_mod.rsplit('.', 1)[-1]
        # Absolute: from auth.forms_seq001_v001 import ...
        pat_abs = re.compile(
            rf'(from\s+\S+\.)({re.escape(stem)})(\s+import\s+)')
        m = pat_abs.search(line)
        if m:
            return line[:m.start(2)] + new_stem + line[m.end(2):]
        # Relative: from .forms_seq001_v001 import ...
        pat_rel = re.compile(
            rf'(from\s+\.)({re.escape(stem)})(\s+import\s+)')
        m = pat_rel.search(line)
        if m:
            return line[:m.start(2)] + new_stem + line[m.end(2):]
        # Package-level: from production_auditor import pipeline_seq015_v005...
        # Handles single and multi-import: from X import a, old_stem, c
        pat_pkg = re.compile(
            rf'(from\s+\w[\w.]*\s+import\s+(?:.*?,\s*)?)(\b{re.escape(stem)}\b)')
        m = pat_pkg.search(line)
        if m:
            return line[:m.start(2)] + new_stem + line[m.end(2):]
        # Bare import: import production_auditor.pipeline_seq015_v005...
        pat_bare = re.compile(
            rf'(import\s+\w[\w.]*\.)({re.escape(stem)})\b')
        m = pat_bare.search(line)
        if m:
            return line[:m.start(2)] + new_stem + line[m.end(2):]
    return line
