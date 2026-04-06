"""manifest_bridge_seq013_v001.py — Update MASTER_MANIFEST.md after compiler runs.

Handles two operations:
1. Update the folder tree structure (insert new v2 folder)
2. Append a versioned changelog entry for the compilation
"""

import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
MASTER_MANIFEST = PROJECT_ROOT / "documentation" / "manifests" / "MASTER_MANIFEST.md"


def _build_tree_entry(target_dir: Path) -> str:
    """Build a folder tree block for the new compilation output."""
    name = target_dir.name
    files = sorted(target_dir.glob("*.py"))
    lines = [f"|   +-- /{name}"]
    for f in files[:8]:
        lines.append(f"|   |   +-- {f.name}")
    if len(files) > 8:
        lines.append(f"|   |   +-- ... ({len(files)} files total)")
    return "\n".join(lines)


def _find_folder_section(content: str, parent: str) -> tuple:
    """Find the codebase_auditor section in the folder tree."""
    pattern = rf"(\+-- /{re.escape(parent)}[^\n]*\n)"
    m = re.search(pattern, content)
    if not m:
        return None, None
    start = m.start()
    # Find the end of this folder's entries (next +-- / at same indent)
    rest = content[m.end():]
    block_end = m.end()
    for line in rest.split("\n"):
        if line.strip().startswith("+-- /") and not line.strip().startswith(f"+-- /{parent}"):
            break
        block_end += len(line) + 1
    return start, block_end


def update_master_manifest(target_dir: Path, source_stem: str,
                           file_count: int, violation_count: int,
                           cost: float = 0.0):
    """Update MASTER_MANIFEST.md with new folder tree + changelog."""
    if not MASTER_MANIFEST.exists():
        print("  MASTER_MANIFEST.md not found — skipping")
        return

    content = MASTER_MANIFEST.read_text(encoding="utf-8")
    ts = datetime.now().strftime("%Y-%m-%d")
    name = target_dir.name
    status = "ALL COMPLIANT" if violation_count == 0 else f"{violation_count} violations"

    # --- 1. Update folder tree: insert v2 folder under /codebase_auditor ---
    tree_entry = _build_tree_entry(target_dir)

    # Check if already registered
    if f"/{name}" not in content:
        start, end = _find_folder_section(content, "codebase_auditor")
        if start is not None:
            # Insert new folder entry before the section ends
            insert_point = end
            content = (content[:insert_point] +
                       tree_entry + "\n" +
                       content[insert_point:])
            print(f"  Inserted /{name} into folder tree")
    else:
        print(f"  /{name} already in folder tree")

    # --- 2. Append changelog entry ---
    changelog_entry = (
        f"\n### Compiler: {name} ({ts})\n"
        f"- **Source**: `{source_stem}.py` → `{name}/` "
        f"({file_count} files)\n"
        f"- **Status**: {status}\n"
        f"- **Cost**: ${cost:.4f}\n"
        f"- **Pipeline**: Pigeon Compiler v0.2.0 "
        f"(clean-split + bin-pack)\n"
    )

    # Find the CHANGELOG section at the bottom and prepend after header
    changelog_header = "## CHANGELOG"
    # Also try the table-based change log
    change_log_header = "## CHANGE LOG"
    
    for header in [changelog_header, change_log_header]:
        idx = content.find(header)
        if idx != -1:
            # Insert after the header line
            header_end = content.index("\n", idx) + 1
            content = (content[:header_end] +
                       changelog_entry +
                       content[header_end:])
            print(f"  Appended changelog entry under {header}")
            break
    else:
        print("  No CHANGELOG section found in MASTER_MANIFEST.md")

    MASTER_MANIFEST.write_text(content, encoding="utf-8")
