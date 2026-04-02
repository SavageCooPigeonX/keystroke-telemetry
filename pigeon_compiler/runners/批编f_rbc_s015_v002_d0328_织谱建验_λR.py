"""run_batch_compile_seq015_v001.py — Compile entire codebase to pigeon compliance.

Scans all .py files in the project, identifies oversized files (>PIGEON_MAX),
orders them by dependency depth (leaves first), and runs the clean-split
pipeline on each. Skips the compiler itself to avoid self-destruct.

Usage:
    python -m pigeon_compiler.runners.run_batch_compile_seq015_v001
    python -m pigeon_compiler.runners.run_batch_compile_seq015_v001 --dry-run
    python -m pigeon_compiler.runners.run_batch_compile_seq015_v001 --include-compiler
"""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v002 | 232 lines | ~1,999 tokens
# DESC:   compile_entire_codebase_to_pigeon
# INTENT: dynamic_import_resolvers
# LAST:   2026-03-28 @ b1971c0
# SESSIONS: 1
# ──────────────────────────────────────────────
import sys, argparse, traceback, re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pigeon_compiler.pigeon_limits import PIGEON_MAX, is_excluded


# ── scanner ──────────────────────────────────

# Files that should never be auto-compiled (root scripts, test harness, etc.)
SKIP_NAMES = frozenset({
    "setup.py", "conftest.py", "manage.py", "wsgi.py", "asgi.py",
    "test_all.py", "stress_test.py",  # test harness — not modules
})

# Directories whose files should not be compiled in batch mode
SKIP_DIRS = frozenset({
    "__pycache__", ".git", ".venv", "node_modules",
    ".pytest_cache", "pigeon_code.egg-info", "dist",
})

# Pigeon compiler's own directories — skip unless --include-compiler
COMPILER_DIRS = frozenset({
    "pigeon_compiler",
})


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


# ── batch executor ───────────────────────────

def batch_compile(root: Path, dry_run: bool = False,
                  include_compiler: bool = False) -> dict:
    """Compile all oversized files in the project."""
    import importlib as _il
    _runner_dir = Path(__file__).parent
    _hits = list(_runner_dir.glob("run_clean_split_seq010_v*.py"))
    if not _hits:
        raise ImportError("净拆f_rcs_s010* not found in runners/")
    _rcs = _il.import_module("pigeon_compiler.runners." + _hits[0].stem)
    run = _rcs.run

    targets = scan_oversized(root, include_compiler=include_compiler)
    total = len(targets)
    total_cost = 0.0
    compiled = []
    skipped = []
    failed = []

    print(f"\n{'='*60}")
    print(f"  🐦 PIGEON BATCH COMPILER v1.0")
    print(f"  Project root: {root}")
    print(f"  Oversized files: {total}")
    print(f"  Dry run: {dry_run}")
    print(f"  Include compiler: {include_compiler}")
    print(f"{'='*60}\n")

    for i, target in enumerate(targets, 1):
        source = target["path"]
        base = target["base"]
        target_dir = source.parent / base
        print(f"\n{'─'*60}")
        print(f"  [{i}/{total}] {target['rel']}")
        print(f"  Lines: {target['lines']} | Target: {target['folder']}/{base}/")
        print(f"{'─'*60}")

        # Skip if target folder already exists and looks compiled
        if target_dir.exists() and (target_dir / "__init__.py").exists():
            existing = list(target_dir.glob("*.py"))
            if len(existing) > 1:
                print(f"  ⏩ Already compiled ({len(existing)} files in {base}/)")
                skipped.append(target)
                continue

        # Also check if a compiled package exists elsewhere (e.g. root streaming_layer/)
        alt_dir = root / base
        if alt_dir != target_dir and alt_dir.exists() and (alt_dir / "__init__.py").exists():
            existing = list(alt_dir.glob("*.py"))
            if len(existing) > 2:
                print(f"  ⏩ Already compiled at {base}/ ({len(existing)} files)")
                skipped.append(target)
                continue

        if dry_run:
            print(f"  [DRY RUN] Would compile {target['rel']} → {base}/")
            skipped.append(target)
            continue

        try:
            result = run(source, target_name=base)
            total_cost += result.get("cost", 0)
            compiled.append({
                **target,
                "result": result,
            })
            if result.get("violations", 0) > 0:
                print(f"  ⚠️ {result['violations']} files still oversized")
            else:
                print(f"  ✅ Compiled to {result.get('files', '?')} files")
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            traceback.print_exc()
            failed.append({**target, "error": str(e)})

        # Cleanup temp files
        for temp in source.parent.glob(f".{source.stem}*_decomposed.py"):
            temp.unlink(missing_ok=True)

    # ── summary ──
    print(f"\n{'='*60}")
    print(f"  BATCH COMPILE SUMMARY")
    print(f"{'='*60}")
    print(f"  Total targets:  {total}")
    print(f"  Compiled:       {len(compiled)}")
    print(f"  Skipped:        {len(skipped)}")
    print(f"  Failed:         {len(failed)}")
    print(f"  Total cost:     ${total_cost:.4f}")
    print()

    if compiled:
        print("  COMPILED:")
        for c in compiled:
            r = c.get("result", {})
            v = r.get("violations", 0)
            s = "✅" if v == 0 else f"⚠️ {v} violations"
            print(f"    {c['rel']:60s} → {c['base']}/  ({r.get('files', '?')} files) {s}")

    if failed:
        print("\n  FAILED:")
        for f in failed:
            print(f"    {f['rel']:60s}  {f['error'][:50]}")

    if skipped:
        print(f"\n  SKIPPED: {len(skipped)} files (already compiled or dry-run)")

    return {
        "total": total,
        "compiled": len(compiled),
        "skipped": len(skipped),
        "failed": len(failed),
        "cost": total_cost,
        "details": compiled,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Pigeon Batch Compiler — compile entire codebase")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scan and plan but don't compile")
    parser.add_argument("--include-compiler", action="store_true",
                        help="Also compile pigeon_compiler's own oversized files")
    parser.add_argument("--root", default=str(PROJECT_ROOT),
                        help="Project root directory")
    args = parser.parse_args()

    batch_compile(
        root=Path(args.root),
        dry_run=args.dry_run,
        include_compiler=args.include_compiler,
    )


if __name__ == "__main__":
    main()
