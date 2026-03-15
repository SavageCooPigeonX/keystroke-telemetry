"""init_writer_seq007_v001.py — Generate __init__.py for split folder.

Re-exports all public functions so external imports don't break.
"""
from pathlib import Path


def write_init(target_dir: Path, plan: dict) -> Path:
    """Write __init__.py with re-exports from all cut files."""
    folder = target_dir.name
    exports = plan.get("init_exports", [])
    cuts = plan.get("cuts", [])

    # Build import map: function → module
    fn_to_mod = {}
    for cut in cuts:
        mod = Path(cut["new_file"]).stem
        names = (cut.get("functions", []) + cut.get("constants", [])
                 + cut.get("contents", []))
        for n in names:
            fn_to_mod[n] = mod

    lines = [f'"""{folder}/ — Pigeon-extracted module. Re-exports all public API."""']
    # Group by module
    mods = {}
    for name in exports:
        mod = fn_to_mod.get(name)
        if mod:
            mods.setdefault(mod, []).append(name)

    for mod in sorted(mods):
        names = ", ".join(sorted(mods[mod]))
        lines.append(f"from {folder}.{mod} import {names}")

    lines.append("")
    out = target_dir / "__init__.py"
    out.write_text("\n".join(lines), encoding='utf-8')
    return out
