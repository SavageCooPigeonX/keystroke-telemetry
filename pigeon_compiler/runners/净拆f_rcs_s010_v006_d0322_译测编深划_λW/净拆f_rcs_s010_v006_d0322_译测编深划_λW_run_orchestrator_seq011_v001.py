"""净拆f_rcs_s010_v006_d0322_译测编深划_λW_run_orchestrator_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 188 lines | ~1,701 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from pigeon_compiler.cut_executor.写w_fw_s003_v005_d0322_译改名踪_λμ import write_cut_files
from pigeon_compiler.cut_executor.切p_ss_s002_v004_d0315_重箱重助重拆_λν import slice_source
from pigeon_compiler.cut_executor.析p_pp_s001_v004_d0315_测编深划鸽环_λν import parse_plan
from pigeon_compiler.cut_executor.织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7 import (
    decompose_oversized_classes)
from pigeon_compiler.cut_executor.重助p_rehe_s011_v004_d0315_重箱重拆切_λν import (
    line_count, collect_imports)
from pigeon_compiler.cut_executor.重拆f_res_s009_v004_d0315_重箱谱建织_λν import (
    scan_violations, resplit_file)
from pigeon_compiler.cut_executor.重箱f_rebi_s010_v004_d0315_重拆谱建织_λν import (
    bin_pack, write_splits)
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED
from pigeon_compiler.runners.净初w_rcsi_s012_v004_d0315_追跑净助鸽环_λν import (
    write_clean_init, write_clean_manifest)
from pigeon_compiler.runners.净助f_rcsh_s011_v004_d0315_追跑净初鸽环_λν import (
    decompose_oversized)
from pigeon_compiler.runners.谱桥p_mbr_s013_v004_d0315_册谱建环检_λν import (
    update_master_manifest)
from pigeon_compiler.state_extractor import build_ether_map
import json, sys, argparse, shutil, traceback, importlib.util, glob as _glob

def run(source_file: Path, target_name: str = None,
        exclude_symbols: list[str] | None = None):
    """Full pipeline on one source file.

    exclude_symbols: confirmed dead exports to prune from the split output.
    These are passed into the DeepSeek cut plan prompt so they are omitted
    from every cut and never appear in __init__.py exports.
    """
    stem = source_file.stem
    target_name = target_name or stem
    target_dir = source_file.parent / target_name
    total_cost = 0.0

    # Clean previous output
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir()
    OUT_DIR.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  PHASE 1: Decompose oversized functions")
    print(f"{'='*60}")

    em = build_ether_map(source_file)
    work_file, dcost = decompose_oversized(source_file, em)
    total_cost += dcost

    if work_file != source_file:
        em = build_ether_map(work_file)

    # Phase 1b: Decompose oversized CLASSES
    work_file2, ccost = decompose_oversized_classes(work_file, em)
    total_cost += ccost
    if work_file2 != work_file:
        work_file = work_file2
        em = build_ether_map(work_file)

    print(f"  Source: {work_file.name} ({em['total_lines']} lines, "
          f"{len(em['functions'])} funcs)")

    print(f"\n{'='*60}")
    print(f"  PHASE 2: DeepSeek cut plan")
    print(f"{'='*60}")

    src = work_file.read_text(encoding="utf-8")
    raw = request_cut_plan(em, src, target_name, exclude_symbols=exclude_symbols or [])
    cost = raw.get("response", {}).get("cost", 0)
    total_cost += cost
    print(f"  DeepSeek cost: ${cost:.4f}")

    plan = parse_plan(raw)
    print(f"  Strategy: {plan.get('strategy', '?')}")
    print(f"  Cuts: {len(plan['cuts'])}")

    print(f"\n{'='*60}")
    print(f"  PHASE 3: Initial file creation")
    print(f"{'='*60}")

    all_names = set()
    for cut in plan["cuts"]:
        for key in ("functions", "constants", "classes", "contents"):
            all_names.update(cut.get(key, []))

    sliced = slice_source(work_file, list(all_names))
    results = write_cut_files(plan, sliced, work_file, target_dir)

    for r in results:
        s = "✅" if r["status"] == "OK" else "❌"
        print(f"  {s} {r['file']} — {r['lines']} lines")

    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"  Initial: {ok}/{len(results)} compliant")

    print(f"\n{'='*60}")
    print(f"  PHASE 4: Deterministic re-split loop")
    print(f"{'='*60}")

    for round_num in range(1, MAX_RESPLIT_ROUNDS + 1):
        violations = scan_violations(target_dir)
        if not violations:
            print(f"  Round {round_num}: ALL FILES ≤{PIGEON_MAX} ✅")
            break

        print(f"  Round {round_num}: {len(violations)} violations")
        for vf in violations:
            lc = line_count(vf)
            print(f"    Splitting {vf.name} ({lc} lines)...")
            items = resplit_file(vf)
            orig_src = vf.read_text(encoding="utf-8")
            orig_imports = collect_imports(orig_src)

            # Determine stem for naming
            base_stem = vf.stem
            # Strip trailing _seqNNN_vNNN for re-naming
            import re as _re
            m = _re.match(r"(.+?)_seq\d+_v\d+$", base_stem)
            if m:
                base_stem = m.group(1)

            bins = bin_pack(items)
            written = write_splits(
                bins, base_stem, orig_imports, target_dir,
                start_seq=_next_seq(target_dir, base_stem))

            for w in written:
                s = "✅" if w["status"] == "OK" else "❌"
                print(f"      {s} {w['file']} — {w['lines']} lines")

            # Remove the original oversized file
            vf.unlink()
            print(f"      Removed {vf.name}")
    else:
        print(f"  ⚠️ Still violations after {MAX_RESPLIT_ROUNDS} rounds")

    # Phase 5: Write __init__.py + MANIFEST
    print(f"\n{'='*60}")
    print(f"  PHASE 5: Write __init__.py + MANIFEST.md")
    print(f"{'='*60}")

    write_clean_init(target_dir, target_name)
    write_clean_manifest(target_dir, stem, cost=total_cost)

    # Final count
    final_files = sorted(target_dir.glob("*.py"))
    violations = [f for f in final_files
                  if f.name != "__init__.py" and line_count(f) > PIGEON_MAX]

    print(f"\n{'='*60}")
    print(f"  RESULT: {len(final_files)} files, "
          f"{len(violations)} violations, ${total_cost:.4f} spent")
    print(f"{'='*60}")

    for f in final_files:
        lc = line_count(f)
        s = "✅" if lc <= PIGEON_MAX or f.name == "__init__.py" else "❌"
        print(f"  {s} {f.name}: {lc} lines")

    # Phase 6: Update MASTER_MANIFEST.md
    print(f"\n{'='*60}")
    print(f"  PHASE 6: Update MASTER_MANIFEST.md")
    print(f"{'='*60}")

    try:
        update_master_manifest(
            target_dir=target_dir,
            source_stem=stem,
            file_count=len(final_files),
            violation_count=len(violations),
            cost=total_cost,
        )
        print(f"  MASTER_MANIFEST.md updated ✅")
    except Exception as e:
        print(f"  ⚠️ Master manifest update failed: {e}")

    # Cleanup temp
    temp = source_file.parent / f".{source_file.stem}_decomposed.py"
    if temp.exists():
        temp.unlink()

    return {
        "target": target_name,
        "files": len(final_files),
        "violations": len(violations),
        "cost": total_cost,
    }
