"""run_pigeon_loop_seq009_v001.py — The Loop: refactor until Pigeon-compliant.

Full pipeline:
  1. Build ether map (AST)
  2. Send to DeepSeek for cut plan
  3. Validate plan
  4. Execute: slice source → write files → write __init__ → write manifest
  5. Check compliance (all files ≤50 lines)
  6. If violations remain → re-run on violating files
  7. Fix imports project-wide

Usage:
    python codebase_auditor/run_pigeon_loop_seq009_v001.py folder_auditor.py
    python codebase_auditor/run_pigeon_loop_seq009_v001.py --all
"""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v004 | 269 lines | ~2,858 tokens
# DESC:   the_loop_refactor_until_pigeon
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import json, sys, argparse, traceback
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pigeon_compiler.state_extractor import build_ether_map
from pigeon_compiler.state_extractor.ether_map_builder_seq006_v004_d0315__assemble_full_ether_map_json_lc_verify_pigeon_plugin import save_ether_map
from pigeon_compiler.weakness_planner.deepseek_plan_prompt_seq004_v003_d0314__build_and_send_deepseek_cut_lc_desc_upgrade import request_cut_plan
from pigeon_compiler.cut_executor.plan_parser_seq001_v004_d0315__parse_deepseek_json_from_raw_lc_verify_pigeon_plugin import parse_plan
from pigeon_compiler.cut_executor.plan_validator_seq006_v004_d0315__validate_cut_plan_before_execution_lc_verify_pigeon_plugin import validate_plan
from pigeon_compiler.cut_executor.source_slicer_seq002_v004_d0315__extract_functions_constants_from_source_lc_verify_pigeon_plugin import slice_source
from pigeon_compiler.cut_executor.file_writer_seq003_v005_d0322__写_write_new_pigeon_compliant_files_lc_multi_line_import import write_cut_files
from pigeon_compiler.cut_executor.init_writer_seq007_v007_d0322__generate_init_py_for_split_lc_stage_78_hook import write_init
from pigeon_compiler.cut_executor.manifest_writer_seq005_v004_d0315__generate_manifest_md_for_a_lc_verify_pigeon_plugin import write_manifest
from pigeon_compiler.cut_executor.import_fixer_seq004_v004_d0315__update_imports_across_the_project_lc_verify_pigeon_plugin import fix_imports
from pigeon_compiler.cut_executor.func_decomposer_seq008_v005_d0322__decompose_oversized_functions_via_deepseek_lc_stage_78_hook import (
    find_oversized, decompose_function)
from pigeon_compiler.cut_executor.source_slicer_seq002_v004_d0315__extract_functions_constants_from_source_lc_verify_pigeon_plugin import _node_name, _node_range

from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED
MAX_ITERATIONS = 3
OUT_DIR = Path(__file__).parent / "compiler_output"


def _pre_decompose(source_file: Path, em: dict) -> tuple[Path, float]:
    """Decompose oversized functions via DeepSeek before planning.
    Returns (new_source_path, total_cost).
    """
    big = find_oversized(em)
    if not big:
        return source_file, 0.0

    print(f"  [PRE] Decomposing {len(big)} oversized functions...")
    src = source_file.read_text(encoding='utf-8')
    lines = src.splitlines(keepends=True)
    import ast
    tree = ast.parse(src)

    # Sort by line number descending so replacements don't shift offsets
    replacements = []
    total_cost = 0.0
    for func_info in sorted(big, key=lambda f: -f["start_line"]):
        name = func_info["name"]
        # Find the AST node
        for node in ast.iter_child_nodes(tree):
            if _node_name(node) == name:
                start, end = _node_range(node, lines)
                func_src = "".join(lines[start:end])
                print(f"      Decomposing {name}() ({func_info['line_count']} lines)...")
                try:
                    from pigeon_compiler.integrations.deepseek_adapter_seq001_v006_d0322__deepseek_api_client_lc_stage_78_hook import deepseek_query
                    decomposed = decompose_function(func_src, name, func_info["line_count"])
                    total_cost += 0.002  # approximate
                    replacements.append((start, end, decomposed))
                    print(f"      → Got {decomposed.count(chr(10))+1} lines of decomposed code")
                except Exception as e:
                    print(f"      ⚠️  Decomposition failed for {name}: {e}")
                break

    if not replacements:
        return source_file, total_cost

    # Apply replacements (already sorted descending)
    for start, end, new_code in replacements:
        lines[start:end] = [new_code + "\n\n"]

    new_src = "".join(lines)
    temp_path = source_file.parent / f".{source_file.stem}_decomposed.py"
    temp_path.write_text(new_src, encoding='utf-8')
    print(f"  [PRE] Wrote decomposed source: {temp_path.name} "
          f"({new_src.count(chr(10))+1} lines)")
    return temp_path, total_cost


def pigeon_loop(source_file: Path, target_folder: str = None,
                dry_run: bool = False) -> dict:
    """Run the full refactor loop on a single source file."""
    OUT_DIR.mkdir(exist_ok=True)
    stem = source_file.stem
    folder_name = target_folder or stem
    log = {"source": str(source_file), "iterations": [], "final_status": "?"}

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'='*60}")
        print(f"  ITERATION {iteration}/{MAX_ITERATIONS}: {stem}")
        print(f"{'='*60}")

        # Step 0: Decompose oversized functions (every iteration)
        work_file = source_file
        decompose_cost = 0.0
        print("  [1] Building ether map...")
        em = build_ether_map(work_file)

        work_file, decompose_cost = _pre_decompose(source_file, em)
        if work_file != source_file:
            # Re-build ether map on decomposed source
            em = build_ether_map(work_file)
        
        save_ether_map(em, OUT_DIR / f"{stem}_ether_map_i{iteration}.json")
        print(f"      {em['total_lines']} lines, {len(em['functions'])} funcs, "
              f"resistance={em['resistance']['score']}")

        # Step 2: DeepSeek cut plan
        print("  [2] Requesting DeepSeek cut plan...")
        src = work_file.read_text(encoding='utf-8')
        raw = request_cut_plan(em, src, folder_name)
        cost = raw.get("response", {}).get("cost", 0) + decompose_cost
        print(f"      Cost: ${cost:.4f}")

        # Step 3: Parse + validate
        print("  [3] Parsing & validating plan...")
        plan = parse_plan(raw)
        val = validate_plan(plan, em)
        print(f"      Valid: {val['valid']}, Errors: {len(val['errors'])}, "
              f"Warnings: {len(val['warnings'])}")
        for e in val['errors']:
            print(f"      ❌ {e}")
        for w in val['warnings']:
            print(f"      ⚠️  {w}")

        # Step 4: Slice + write
        target_dir = source_file.parent / folder_name
        all_names = []
        for cut in plan["cuts"]:
            all_names += cut.get("functions", [])
            all_names += cut.get("constants", [])
            all_names += cut.get("contents", [])
        print(f"  [4] Slicing {len(set(all_names))} names from source...")
        sliced = slice_source(work_file, list(set(all_names)))
        print(f"      Got {len(sliced)} slices")

        print(f"  [5] Writing files to {folder_name}/...")
        results = write_cut_files(plan, sliced, work_file, target_dir,
                                  dry_run=dry_run)
        for r in results:
            status = "✅" if r["status"] == "OK" else "❌"
            print(f"      {status} {r['file']} — {r['lines']} lines ({r['status']})")

        # Step 5: Write __init__.py + MANIFEST.md
        if not dry_run:
            write_init(target_dir, plan)
            write_manifest(target_dir, plan, results)
            print("  [6] Wrote __init__.py + MANIFEST.md")

        # Save plan artifact
        plan_out = OUT_DIR / f"{stem}_plan_i{iteration}.json"
        plan_out.write_text(json.dumps(plan, indent=2), encoding='utf-8')

        # Check compliance
        violations = [r for r in results if r["status"] != "OK"]
        iter_log = {
            "iteration": iteration,
            "cost": cost,
            "files_created": len(results),
            "violations": len(violations),
            "validation": val,
        }
        log["iterations"].append(iter_log)

        if not violations:
            print(f"\n  ✅ ALL {len(results)} FILES PIGEON-COMPLIANT")
            log["final_status"] = "COMPLIANT"
            break
        else:
            print(f"\n  ❌ {len(violations)} violations remain")
            if iteration < MAX_ITERATIONS:
                print("  → Re-running with tighter constraints...")

    # Step 7: Fix imports (dry_run first to show what would change)
    if not dry_run:
        old_mod = _module_path(source_file)
        new_mod = _module_path(source_file.parent / folder_name)
        print(f"\n  [7] Fixing imports: {old_mod} → {new_mod}")
        changes = fix_imports(old_mod, new_mod, plan.get("init_exports", []),
                              PROJECT_ROOT, dry_run=True)
        for c in changes:
            print(f"      {c['file']}: {c['old_line'][:60]}...")
        log["import_changes"] = changes

    # Cleanup temp files
    temp = source_file.parent / f".{source_file.stem}_decomposed.py"
    if temp.exists():
        temp.unlink()

    # Save log
    log_path = OUT_DIR / f"{stem}_loop_log.json"
    log_path.write_text(json.dumps(log, indent=2, default=str), encoding='utf-8')
    print(f"\n  Log: {log_path}")
    return log


def _module_path(path: Path) -> str:
    """Convert filesystem path to Python module path."""
    try:
        rel = path.relative_to(PROJECT_ROOT)
        return str(rel.with_suffix('')).replace('\\', '.').replace('/', '.')
    except ValueError:
        return path.stem


def main():
    parser = argparse.ArgumentParser(description="Pigeon Compiler Loop")
    parser.add_argument("target", nargs="?",
                        help="Source file to refactor (relative to codebase_auditor/)")
    parser.add_argument("--all", action="store_true",
                        help="Refactor both folder_auditor.py and master_auditor.py")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't write files, just show what would happen")
    parser.add_argument("--folder", help="Target folder name override")
    args = parser.parse_args()

    targets = []
    ca = PROJECT_ROOT / "codebase_auditor"
    if args.all:
        targets = [ca / "folder_auditor.py", ca / "master_auditor.py"]
    elif args.target:
        targets = [ca / args.target]
    else:
        parser.print_help()
        return

    print("=" * 60)
    print("  🐦 PIGEON COMPILER LOOP v0.2.0")
    print(f"  Targets: {[t.name for t in targets]}")
    print(f"  Dry run: {args.dry_run}")
    print("=" * 60)

    total_cost = 0
    for t in targets:
        try:
            log = pigeon_loop(t, target_folder=args.folder, dry_run=args.dry_run)
            for it in log.get("iterations", []):
                total_cost += it.get("cost", 0)
        except Exception as e:
            print(f"\n  FATAL: {e}")
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"  Total DeepSeek cost: ${total_cost:.4f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
