"""run_clean_split_init_seq012_v001.py — Init + manifest writers for clean split.

Generates __init__.py with re-exports and MANIFEST.md with:
- FILES table (file, lines, exported functions)
- Append-only CHANGELOG (preserves prior entries)
- Version stamp + cost tracking
"""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v004 | 199 lines | ~1,663 tokens
# DESC:   init_manifest_writers_for_clean
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import ast, re
from pathlib import Path
from datetime import datetime
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED
CHANGELOG_MARKER = "## CHANGELOG"


def _scan_exports(target_dir: Path):
    """Scan all .py files and return {module_stem: [func_names]}."""
    exports = {}
    for py in sorted(target_dir.glob("*.py")):
        if py.name == "__init__.py":
            continue
        src = py.read_text(encoding="utf-8")
        tree = ast.parse(src)
        mod = py.stem
        fns = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    fns.append(node.name)
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    fns.append(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.isupper():
                        fns.append(t.id)
        if fns:
            exports[mod] = fns
    return exports


def write_clean_init(target_dir: Path, folder_name: str):
    """Scan all .py files and generate __init__.py with re-exports."""
    exports = _scan_exports(target_dir)

    lines = [f'"""{folder_name}/ — Pigeon-compliant module."""']
    for mod in sorted(exports):
        names = ", ".join(sorted(exports[mod]))
        lines.append(f"from {folder_name}.{mod} import {names}")
    lines.append("")

    (target_dir / "__init__.py").write_text("\n".join(lines), encoding="utf-8")
    print(f"  __init__.py: {len(exports)} modules, "
          f"{sum(len(v) for v in exports.values())} exports")
    return exports


def _load_existing_changelog(manifest_path: Path) -> str:
    """Extract existing CHANGELOG entries from a MANIFEST.md (append-only)."""
    if not manifest_path.exists():
        return ""
    content = manifest_path.read_text(encoding="utf-8")
    idx = content.find(CHANGELOG_MARKER)
    if idx == -1:
        return ""
    # Everything after the ## CHANGELOG header
    after = content[idx + len(CHANGELOG_MARKER):]
    # Strip the first newline(s) right after the header
    after = after.lstrip("\n")
    return after.rstrip()


def write_clean_manifest(target_dir: Path, source_stem: str,
                         cost: float = 0.0, version: str = None):
    """Generate MANIFEST.md with FILES table, exports, and append-only CHANGELOG."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    ts_short = datetime.now().strftime("%Y-%m-%d")
    name = target_dir.name
    manifest_path = target_dir / "MANIFEST.md"

    # --- Scan exports per file ---
    exports = _scan_exports(target_dir)

    # --- Build FILES table with actual function names ---
    rows = ["| File | Lines | Functions |", "|------|-------|-----------|"]
    total_files = 0
    total_lines = 0
    violations = 0
    for py in sorted(target_dir.glob("*.py")):
        if py.name == "MANIFEST.md":
            continue
        lc = len(py.read_text(encoding="utf-8").splitlines())
        mod = py.stem
        fn_list = exports.get(mod, [])
        fn_str = ", ".join(fn_list) if fn_list else "—"
        marker = ""
        if py.name != "__init__.py" and lc > PIGEON_MAX:
            marker = " 🔴"
            violations += 1
        elif py.name != "__init__.py" and lc > PIGEON_RECOMMENDED:
            marker = " 🟡"
        rows.append(f"| `{py.name}` | {lc}{marker} | {fn_str} |")
        total_files += 1
        total_lines += lc
    table = "\n".join(rows)

    # --- Version ---
    ver = version or "1.0.0"

    # --- Load existing changelog (append-only) ---
    prior_changelog = _load_existing_changelog(manifest_path)

    # --- Build new changelog entry ---
    status = "✅ ALL COMPLIANT" if violations == 0 else f"❌ {violations} violations"
    new_entry = (
        f"### v{ver} ({ts_short})\n"
        f"- **Source**: `{source_stem}.py` → {total_files} files, "
        f"{total_lines} total lines\n"
        f"- **Status**: {status}\n"
        f"- **Cost**: ${cost:.4f}\n"
        f"- **Timestamp**: {ts}\n"
    )

    # Combine: new entry on top, then prior entries
    if prior_changelog:
        changelog_body = f"{new_entry}\n{prior_changelog}"
    else:
        changelog_body = new_entry

    # --- Assemble full manifest ---
    all_exports = []
    for mod in sorted(exports):
        all_exports.extend(exports[mod])

    exports_section = ""
    if all_exports:
        exports_section = (
            "---\n\n## EXPORTS\n\n"
            f"`{', '.join(sorted(all_exports))}`\n\n"
        )

    # --- Build STRUCTURE section (dependency tree) ---
    structure_lines = [f"{name}/"]
    for py in sorted(target_dir.glob("*.py")):
        mod = py.stem
        fn_list = exports.get(mod, [])
        fn_hint = f"  ({', '.join(fn_list[:3])})" if fn_list else ""
        structure_lines.append(f"  ├── {py.name}{fn_hint}")
    structure_lines.append(f"  └── MANIFEST.md")
    structure_section = "\n".join(structure_lines)

    # --- Build PROMPT BOX section ---
    name_upper = name.upper().replace("-", "_").replace(" ", "_")
    prompt_box = (
        f"## 📦 PROMPT BOX — {name_upper} TASKS\n"
        f"*Generated by Pigeon Compiler | {ts_short}*\n\n"
        f"- [ ] **{name_upper}-001**: Verify all imports resolve correctly\n"
        f"- [ ] **{name_upper}-002**: Run drift watcher on this folder\n"
        f"- [ ] **{name_upper}-003**: Add unit tests for extracted functions\n"
        f"- [ ] **{name_upper}-004**: Verify no circular imports\n"
        f"- [ ] **{name_upper}-005**: Integration test with parent package\n"
    )

    md = f"""# {name}/ MANIFEST.md
## Pigeon-Extracted from `{source_stem}.py`
**Version**: v{ver} | **Last Updated**: {ts_short}

---

## FILES

{table}

{exports_section}---

## STRUCTURE

```
{structure_section}
```

---

{prompt_box}
---

{CHANGELOG_MARKER}

{changelog_body}
"""
    manifest_path.write_text(md, encoding="utf-8")
    print(f"  MANIFEST.md written (v{ver}, {total_files} files, ${cost:.4f})")
