"""run_batch_compile_seq015_orchestrator_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import sys, argparse, traceback, re

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
