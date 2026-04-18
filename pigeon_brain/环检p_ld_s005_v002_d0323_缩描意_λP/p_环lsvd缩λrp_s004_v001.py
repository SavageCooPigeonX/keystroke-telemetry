"""环检p_ld_s005_v002_d0323_缩描意_λP_record_path_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 47 lines | ~385 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import re

def record_path(root: Path, job_id: str, path: list[str],
                status: str, death_cause: str = "") -> None:
    """Record a completed electron path for loop analysis."""
    store_path = root / LOOP_STORE
    try:
        store = json.loads(store_path.read_text("utf-8")) if store_path.exists() else {}
    except Exception:
        store = {}

    paths = store.get("paths", [])
    loops = store.get("detected_loops", [])

    fp = _path_fingerprint(path)
    paths.append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id,
        "fingerprint": fp,
        "length": len(path),
        "status": status,
        "death_cause": death_cause,
    })

    # Check for within-path loops (node visited 3+ times)
    node_counts = Counter(path)
    internal_loops = [
        {"node": node, "visits": count}
        for node, count in node_counts.items()
        if count >= RECUR_THRESH
    ]
    if internal_loops:
        loops.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
            "loops": internal_loops,
            "path_length": len(path),
        })

    store["paths"] = paths[-MAX_ENTRIES:]
    store["detected_loops"] = loops[-MAX_ENTRIES:]
    store_path.write_text(json.dumps(store, indent=2), encoding="utf-8")
