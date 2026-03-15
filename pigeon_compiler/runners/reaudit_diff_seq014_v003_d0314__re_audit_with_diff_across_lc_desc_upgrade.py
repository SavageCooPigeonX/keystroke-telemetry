"""reaudit_diff_seq014_v001.py — Re-audit with diff-across-time.

Compares current ether map against prior compiler output to track:
- What changed since last compilation
- Which functions grew/shrank/appeared/disappeared
- Whether prior cuts are still valid
- Manifest drift (files in folder vs files in MANIFEST.md)
"""
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
COMPILER_OUT = Path(__file__).parent / "compiler_output"


def load_prior_ether_map(stem: str) -> dict | None:
    """Load most recent ether map for a given file stem."""
    # Check numbered iterations first (i3, i2, i1), then base
    for suffix in ["_i3", "_i2", "_i1", ""]:
        path = COMPILER_OUT / f"{stem}_ether_map{suffix}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def load_prior_plan(stem: str) -> dict | None:
    """Load most recent cut plan for a given file stem."""
    for suffix in ["_i3", "_i2", "_i1", ""]:
        path = COMPILER_OUT / f"{stem}_cut_plan{suffix}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _func_dict(funcs: list) -> dict:
    """Convert function list to {name: {line_count, start, end}}."""
    return {f['name']: f for f in funcs}


def diff_ether_maps(old: dict, new: dict) -> dict:
    """Compare two ether maps and return structured diff."""
    old_funcs = _func_dict(old.get('functions', []))
    new_funcs = _func_dict(new.get('functions', []))

    added = [n for n in new_funcs if n not in old_funcs]
    removed = [n for n in old_funcs if n not in new_funcs]

    changed = []
    for name in set(old_funcs) & set(new_funcs):
        old_lc = old_funcs[name]['line_count']
        new_lc = new_funcs[name]['line_count']
        if old_lc != new_lc:
            delta = new_lc - old_lc
            changed.append({
                "name": name,
                "old_lines": old_lc,
                "new_lines": new_lc,
                "delta": delta,
                "direction": "grew" if delta > 0 else "shrank",
            })

    return {
        "old_file": old.get('file', '?'),
        "new_file": new.get('file', '?'),
        "old_total": old.get('total_lines', 0),
        "new_total": new.get('total_lines', 0),
        "total_delta": new.get('total_lines', 0) - old.get('total_lines', 0),
        "functions_added": added,
        "functions_removed": removed,
        "functions_changed": changed,
        "old_resistance": old.get('resistance', {}).get('score', 0),
        "new_resistance": new.get('resistance', {}).get('score', 0),
        "timestamp": datetime.now().isoformat(),
    }


def scan_manifest_drift(target_dir: Path) -> dict:
    """Compare actual files in folder vs what MANIFEST.md lists."""
    manifest_path = target_dir / "MANIFEST.md"
    actual_files = {f.name for f in target_dir.glob("*.py")}

    manifest_files = set()
    if manifest_path.exists():
        content = manifest_path.read_text(encoding="utf-8")
        import re
        for m in re.finditer(r"`([^`]+\.py)`", content):
            manifest_files.add(m.group(1))

    return {
        "folder": str(target_dir.name),
        "actual_files": sorted(actual_files),
        "manifest_files": sorted(manifest_files),
        "missing_from_manifest": sorted(actual_files - manifest_files),
        "phantom_in_manifest": sorted(manifest_files - actual_files),
        "aligned": actual_files == manifest_files,
    }


def collect_codebase_manifests(root: Path = None) -> list:
    """Retrieve all MANIFEST.md files in the codebase for context."""
    root = root or PROJECT_ROOT
    manifests = []
    for md in root.rglob("MANIFEST.md"):
        try:
            content = md.read_text(encoding="utf-8")
            # Extract just the header + files table (first 40 lines)
            lines = content.splitlines()[:40]
            manifests.append({
                "path": str(md.relative_to(root)),
                "preview": "\n".join(lines),
                "full_lines": len(content.splitlines()),
            })
        except Exception:
            pass
    return manifests


def run_reaudit(source_file: Path) -> dict:
    """Full re-audit: build new ether map, diff against prior, check manifests."""
    from pigeon_compiler.state_extractor import build_ether_map

    stem = source_file.stem
    print(f"\n  RE-AUDIT: {stem}")

    # Build current ether map
    new_em = build_ether_map(source_file)

    # Load prior
    old_em = load_prior_ether_map(stem)

    # Diff
    diff = None
    if old_em:
        diff = diff_ether_maps(old_em, new_em)
        print(f"  Total lines: {diff['old_total']} → {diff['new_total']} "
              f"({diff['total_delta']:+d})")
        print(f"  Resistance: {diff['old_resistance']} → {diff['new_resistance']}")
        if diff['functions_added']:
            print(f"  + Added: {diff['functions_added']}")
        if diff['functions_removed']:
            print(f"  - Removed: {diff['functions_removed']}")
        for c in diff['functions_changed']:
            print(f"  Δ {c['name']}: {c['old_lines']}→{c['new_lines']} "
                  f"({c['delta']:+d})")
    else:
        print(f"  No prior ether map — first run")
        print(f"  Total lines: {new_em['total_lines']}")
        print(f"  Resistance: {new_em['resistance']['score']}")

    # Check v2 folder manifest drift if exists
    v2_dir = source_file.parent / stem
    manifest_drift = None
    if v2_dir.exists():
        manifest_drift = scan_manifest_drift(v2_dir)
        if not manifest_drift['aligned']:
            print(f"  ⚠️ Manifest drift in {v2_dir.name}/:")
            if manifest_drift['missing_from_manifest']:
                print(f"    Missing from MANIFEST: "
                      f"{manifest_drift['missing_from_manifest']}")
            if manifest_drift['phantom_in_manifest']:
                print(f"    Phantom in MANIFEST: "
                      f"{manifest_drift['phantom_in_manifest']}")
        else:
            print(f"  ✅ Manifest aligned ({len(manifest_drift['actual_files'])} files)")

    # Save new ether map
    COMPILER_OUT.mkdir(exist_ok=True)
    out_path = COMPILER_OUT / f"{stem}_ether_map.json"
    out_path.write_text(json.dumps(new_em, indent=2, default=str),
                        encoding="utf-8")

    # Save diff
    if diff:
        diff_path = COMPILER_OUT / f"{stem}_diff.json"
        diff_path.write_text(json.dumps(diff, indent=2), encoding="utf-8")

    return {
        "ether_map": new_em,
        "diff": diff,
        "manifest_drift": manifest_drift,
    }
