"""import_fixer_seq004_v001.py — Update imports across the project after a split.

Scans all .py files and replaces old import paths with new module paths.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v004 | 60 lines | ~505 tokens
# DESC:   update_imports_across_the_project
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import re
from pathlib import Path


def fix_imports(old_module: str, new_folder: str, init_exports: list,
                project_root: Path, dry_run: bool = False) -> list:
    """Rewrite imports from old_module to new_folder across project.

    old_module: e.g. "codebase_auditor.folder_auditor"
    new_folder: e.g. "codebase_auditor.folder_auditor_v2"
    Returns list of {file, old_line, new_line}.
    """
    changes = []
    old_stem = old_module.split(".")[-1]
    for py in project_root.rglob("*.py"):
        if "__pycache__" in str(py) or ".venv" in str(py):
            continue
        text = _safe_read(py)
        if not text or old_stem not in text:
            continue
        new_text, file_changes = _rewrite(text, old_module, new_folder)
        if file_changes:
            if not dry_run:
                py.write_text(new_text, encoding='utf-8')
            for c in file_changes:
                c["file"] = str(py.relative_to(project_root))
            changes.extend(file_changes)
    return changes


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ""


def _rewrite(text, old_module, new_folder):
    changes = []
    pattern = re.compile(
        rf'^(from\s+){re.escape(old_module)}(\s+import\s+.+)$', re.M)
    def _sub(m):
        old_line = m.group(0)
        new_line = f"{m.group(1)}{new_folder}{m.group(2)}"
        changes.append({"old_line": old_line, "new_line": new_line})
        return new_line
    new_text = pattern.sub(_sub, text)
    return new_text, changes
