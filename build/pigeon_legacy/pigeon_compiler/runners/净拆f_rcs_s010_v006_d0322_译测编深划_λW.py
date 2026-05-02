"""run_clean_split_seq010_v001.py — Full clean pipeline: DeepSeek plan → split → resplit until compliant.

Usage:
    python codebase_auditor/run_clean_split_seq010_v001.py folder_auditor.py
    python codebase_auditor/run_clean_split_seq010_v001.py master_auditor.py
    python codebase_auditor/run_clean_split_seq010_v001.py --all
"""

import json, sys, argparse, shutil, traceback, importlib.util, glob as _glob
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pigeon_compiler.state_extractor import build_ether_map

# Dynamic import for deepseek_plan_prompt (pigeon name mutates)
def _load_request_cut_plan():
    matches = sorted(PROJECT_ROOT.glob('weakness_planner/核w_dspp_s004*.py'))
    if not matches:
        raise ImportError('deepseek_plan_prompt_seq004 not found')
    spec = importlib.util.spec_from_file_location('_dsp', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.request_cut_plan

request_cut_plan = _load_request_cut_plan()


def _node_name(node: dict) -> str:
    return str(node.get("name") or "")


def _node_lines(node: dict) -> int:
    if "line_count" in node:
        return int(node.get("line_count") or 0)
    return int(node.get("end_line", 0) or 0) - int(node.get("start_line", 0) or 0) + 1


def _fallback_cut_plan(
    em: dict,
    source_name: str,
    target_name: str,
    exclude_symbols: list[str] | None = None,
) -> dict:
    """Build a deterministic cut plan when DeepSeek is unavailable."""
    excluded = set(exclude_symbols or [])
    budget = max(40, PIGEON_MAX - 35)
    cuts: list[dict] = []
    seq = 1

    def add_cut(kind: str, names: list[str], line_total: int) -> None:
        nonlocal seq
        if not names:
            return
        safe_target = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in target_name)[:36]
        cuts.append({
            "new_file": f"{safe_target}_{kind}_seq{seq:03d}_v001.py",
            kind: names,
            "reason": f"deterministic fallback group, measured {line_total} source lines",
        })
        seq += 1

    for kind, nodes in (("classes", em.get("classes", [])), ("constants", em.get("constants", []))):
        for node in nodes:
            name = _node_name(node)
            if name and name not in excluded:
                add_cut(kind, [name], _node_lines(node))

    bucket: list[str] = []
    bucket_lines = 0
    for fn in sorted(em.get("functions", []), key=lambda item: (item.get("start_line", 0), item.get("name", ""))):
        name = _node_name(fn)
        if not name or name in excluded:
            continue
        lines = max(1, _node_lines(fn))
        if bucket and bucket_lines + lines > budget:
            add_cut("functions", bucket, bucket_lines)
            bucket = []
            bucket_lines = 0
        bucket.append(name)
        bucket_lines += lines
    add_cut("functions", bucket, bucket_lines)

    exports = [
        _node_name(node)
        for node in [*em.get("functions", []), *em.get("classes", []), *em.get("constants", [])]
        if _node_name(node) and not _node_name(node).startswith("_") and _node_name(node) not in excluded
    ]
    return {
        "source_file": source_name,
        "strategy": "deterministic_ast_line_budget_fallback",
        "cuts": cuts,
        "init_exports": exports,
    }
from pigeon_compiler.cut_executor.析p_pp_s001_v004_d0315_测编深划鸽环_λν import parse_plan
from pigeon_compiler.cut_executor.切p_ss_s002_v004_d0315_重箱重助重拆_λν import slice_source
from pigeon_compiler.cut_executor.写w_fw_s003_v005_d0322_译改名踪_λμ import write_cut_files
from pigeon_compiler.cut_executor.初写p_iw_s007_v007_d0322_净拆译_λ7 import write_init
from pigeon_compiler.cut_executor.稿p_mw_s005_v004_d0315_册追跑谱桥_λν import write_manifest
from pigeon_compiler.cut_executor.重拆f_res_s009_v004_d0315_重箱谱建织_λν import (
    scan_violations, resplit_file)
from pigeon_compiler.cut_executor.重箱f_rebi_s010_v004_d0315_重拆谱建织_λν import (
    bin_pack, write_splits)
from pigeon_compiler.cut_executor.重助p_rehe_s011_v004_d0315_重箱重拆切_λν import (
    line_count, collect_imports)
from pigeon_compiler.runners.净助f_rcsh_s011_v004_d0315_追跑净初鸽环_λν import (
    decompose_oversized)
from pigeon_compiler.cut_executor.织f_cdp_s013_v002_d0322_谱建重箱重拆_λ7 import (
    decompose_oversized_classes)
from pigeon_compiler.runners.净初w_rcsi_s012_v004_d0315_追跑净助鸽环_λν import (
    write_clean_init, write_clean_manifest)
from pigeon_compiler.runners.谱桥p_mbr_s013_v004_d0315_册谱建环检_λν import (
    update_master_manifest)

from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED
MAX_RESPLIT_ROUNDS = 5
OUT_DIR = Path(__file__).parent / "compiler_output"


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
    try:
        raw = request_cut_plan(em, src, target_name, exclude_symbols=exclude_symbols or [])
        cost = raw.get("response", {}).get("cost", 0)
        total_cost += cost
        print(f"  DeepSeek cost: ${cost:.4f}")
        plan = parse_plan(raw)
    except Exception as exc:
        print(f"  DeepSeek unavailable: {exc}")
        print("  Falling back to deterministic AST line-budget split")
        plan = _fallback_cut_plan(em, source_file.name, target_name, exclude_symbols)
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

    ok = sum(1 for r in results if not str(r["status"]).startswith("OVER"))
    print(f"  Initial: {ok}/{len(results)} hard-cap compliant")

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
