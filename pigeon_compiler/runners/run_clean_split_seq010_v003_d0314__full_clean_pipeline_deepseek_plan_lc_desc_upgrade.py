"""run_clean_split_seq010_v001.py — Full clean pipeline: DeepSeek plan → split → resplit until compliant.

Usage:
    python codebase_auditor/run_clean_split_seq010_v001.py folder_auditor.py
    python codebase_auditor/run_clean_split_seq010_v001.py master_auditor.py
    python codebase_auditor/run_clean_split_seq010_v001.py --all
"""
import json, sys, argparse, shutil, traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pigeon_compiler.state_extractor import build_ether_map
from pigeon_compiler.weakness_planner.deepseek_plan_prompt_seq004_v003_d0314__build_and_send_deepseek_cut_lc_desc_upgrade import (
    request_cut_plan)
from pigeon_compiler.cut_executor.plan_parser_seq001_v003_d0314__parse_deepseek_json_from_raw_lc_desc_upgrade import parse_plan
from pigeon_compiler.cut_executor.source_slicer_seq002_v003_d0314__extract_functions_constants_from_source_lc_desc_upgrade import slice_source
from pigeon_compiler.cut_executor.file_writer_seq003_v003_d0314__write_new_pigeon_compliant_files_lc_desc_upgrade import write_cut_files
from pigeon_compiler.cut_executor.init_writer_seq007_v003_d0314__generate_init_py_for_split_lc_desc_upgrade import write_init
from pigeon_compiler.cut_executor.manifest_writer_seq005_v003_d0314__generate_manifest_md_for_a_lc_desc_upgrade import write_manifest
from pigeon_compiler.cut_executor.resplit_seq009_v003_d0314__deterministic_ast_bin_packing_re_lc_desc_upgrade import (
    scan_violations, resplit_file)
from pigeon_compiler.cut_executor.resplit_binpack_seq010_v003_d0314__bin_packing_file_writing_for_lc_desc_upgrade import (
    bin_pack, write_splits)
from pigeon_compiler.cut_executor.resplit_helpers_seq011_v003_d0314__shared_helpers_for_re_splitter_lc_desc_upgrade import (
    line_count, collect_imports)
from pigeon_compiler.runners.run_clean_split_helpers_seq011_v003_d0314__helpers_for_run_clean_split_lc_desc_upgrade import (
    decompose_oversized)
from pigeon_compiler.runners.run_clean_split_init_seq012_v003_d0314__init_manifest_writers_for_clean_lc_desc_upgrade import (
    write_clean_init, write_clean_manifest)
from pigeon_compiler.runners.manifest_bridge_seq013_v003_d0314__update_master_manifest_md_after_lc_desc_upgrade import (
    update_master_manifest)

from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED
MAX_RESPLIT_ROUNDS = 5
OUT_DIR = Path(__file__).parent / "compiler_output"


def run(source_file: Path, target_name: str = None):
    """Full pipeline on one source file."""
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

    print(f"  Source: {work_file.name} ({em['total_lines']} lines, "
          f"{len(em['functions'])} funcs)")

    print(f"\n{'='*60}")
    print(f"  PHASE 2: DeepSeek cut plan")
    print(f"{'='*60}")

    src = work_file.read_text(encoding="utf-8")
    raw = request_cut_plan(em, src, target_name)
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


def _next_seq(folder: Path, stem: str) -> int:
    """Find next available sequence number for a stem in folder."""
    import re as _re
    highest = 0
    for py in folder.glob(f"{stem}_seq*_v*.py"):
        m = _re.search(r"_seq(\d+)_v", py.name)
        if m:
            highest = max(highest, int(m.group(1)))
    return highest + 1


def main():
    parser = argparse.ArgumentParser(description="Pigeon Compiler — Clean Split")
    parser.add_argument("target", nargs="?",
                        help="Source file (relative to codebase_auditor/)")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--name", help="Target folder name override")
    args = parser.parse_args()

    ca = PROJECT_ROOT / "codebase_auditor"
    targets = []
    if args.all:
        targets = [(ca / "folder_auditor.py", "folder_auditor"),
                   (ca / "master_auditor.py", "master_auditor")]
    elif args.target:
        t = ca / args.target
        targets = [(t, args.name or t.stem)]
    else:
        parser.print_help()
        return

    for src, name in targets:
        try:
            run(src, name)
        except Exception as e:
            print(f"FATAL: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()