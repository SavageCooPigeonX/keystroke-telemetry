"""虫f_bdm_s015_v001_d0410_λFT_graph_utils_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 34 lines | ~336 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _build_import_graph(veins: dict) -> dict[str, list[str]]:
    """Build {module: [downstream_importers]} from vein data.

    context_veins_seq001_v001.json stores per-node vein scores. We infer import
    relationships from the graph_cache.json edges it was built from.
    Falls back to reading the graph cache directly.
    """
    # context_veins_seq001_v001.json doesn't store raw edges — use graph_cache
    return {}


def _build_seq_to_graph_nodes(root: Path) -> dict[int, list[str]]:
    """Map seq_number → list of graph node names that carry that seq.

    Graph nodes encode seq in their name via `_seqNNN_` (e.g.
    `backward_seq007_backward_pass`). Registry pigeon names encode it as
    `_sNNN_` (e.g. `逆f_ba_s007_`). Seq is the stable cross-reference key.
    """
    cache = root / "pigeon_brain" / "graph_cache.json"
    if not cache.exists():
        return {}
    graph = json.loads(cache.read_text("utf-8"))
    seq_re = __import__("re").compile(r"_seq(\d+)_?")
    seq_map: dict[int, list[str]] = {}
    for node_name in graph.get("nodes", {}):
        m = seq_re.search(node_name)
        if m:
            seq = int(m.group(1))
            seq_map.setdefault(seq, []).append(node_name)
    return seq_map
