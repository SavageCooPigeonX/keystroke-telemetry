"""环检p_ld_s005_v002_d0323_缩描意_λP_load_stats_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 50 lines | ~412 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from pathlib import Path
import json
import re

def load_loop_stats(root: Path) -> dict:
    """Aggregate loop data → summary for observer synthesis."""
    store_path = root / LOOP_STORE
    if not store_path.exists():
        return {}
    try:
        store = json.loads(store_path.read_text("utf-8"))
    except Exception:
        return {}

    paths = store.get("paths", [])
    loops = store.get("detected_loops", [])

    # Find recurring path fingerprints (same path taken 3+ times)
    fps = [p["fingerprint"] for p in paths]
    counts = Counter(fps)
    recurring = [
        {"path": fp, "count": cnt,
         "last_status": next((p["status"] for p in reversed(paths)
                              if p["fingerprint"] == fp), "unknown")}
        for fp, cnt in counts.most_common(5)
        if cnt >= RECUR_THRESH
    ]

    # Most-looped nodes across all detected internal loops
    all_loop_nodes = Counter()
    for entry in loops:
        for lp in entry.get("loops", []):
            all_loop_nodes[lp["node"]] += lp["visits"]
    worst_loop_nodes = [
        {"node": n, "total_revisits": c}
        for n, c in all_loop_nodes.most_common(5)
    ]

    dead_paths = sum(1 for p in paths if p["status"] == "dead")

    return {
        "total_paths": len(paths),
        "recurring_paths": recurring,
        "internal_loops": len(loops),
        "worst_loop_nodes": worst_loop_nodes,
        "dead_path_count": dead_paths,
        "dead_path_rate": round(dead_paths / max(len(paths), 1), 3),
    }
