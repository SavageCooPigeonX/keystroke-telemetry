"""resplit_binpack_seq010_v001.py — Bin-packing + file writing for re-splitter.

First-fit-decreasing bin packing: largest functions placed first,
each bin ≤ budget lines. Then writes the actual Python files.
"""
import ast
from pathlib import Path
from pigeon_compiler.cut_executor.resplit_helpers_seq011_v003_d0314__shared_helpers_for_re_splitter_lc_desc_upgrade import (
    filter_imports, assemble_file)
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED, FILE_OVERHEAD


def bin_pack(items: list[dict], budget: int = None) -> list[list[dict]]:
    """First-fit-decreasing bin pack items into ≤budget groups.

    Classes (is_class=True) always get their own bin even if oversized,
    since they can't be split across files.
    """
    if budget is None:
        budget = PIGEON_MAX - FILE_OVERHEAD
    sorted_items = sorted(items, key=lambda x: -x["lines"])
    bins: list[list[dict]] = []
    bin_sizes: list[int] = []

    for item in sorted_items:
        # Classes always get their own bin
        if item.get("is_class"):
            bins.append([item])
            bin_sizes.append(item["lines"])
            continue
        placed = False
        for i, b in enumerate(bins):
            # Don't pack functions into a class bin
            if any(it.get("is_class") for it in b):
                continue
            if bin_sizes[i] + item["lines"] <= budget:
                b.append(item)
                bin_sizes[i] += item["lines"]
                placed = True
                break
        if not placed:
            bins.append([item])
            bin_sizes.append(item["lines"])
    return bins


def write_splits(bins: list[list[dict]], stem: str,
                 orig_imports: list[str], target_dir: Path,
                 start_seq: int = 1) -> list[dict]:
    """Write each bin as a Pigeon-compliant file. Returns file info."""
    results = []
    for i, b in enumerate(bins):
        seq = start_seq + i
        fname = f"{stem}_seq{seq:03d}_v001.py"
        body = "\n".join(item["source"].rstrip() for item in b)
        needed = filter_imports(body, orig_imports)
        content = assemble_file(fname, needed, body)
        out = target_dir / fname
        out.write_text(content, encoding="utf-8")
        lc = content.count("\n") + 1
        names = [item["name"] for item in b]
        results.append({
            "file": fname, "lines": lc, "names": names,
            "status": "OK" if lc <= PIGEON_RECOMMENDED else ("WARN" if lc <= PIGEON_MAX else f"OVER({lc})"),
        })
    return results
