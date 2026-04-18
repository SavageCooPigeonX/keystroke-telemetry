"""缩p_fdt_s006_v002_d0323_描环检意_λP_stats_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 41 lines | ~341 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def load_death_stats(root: Path) -> dict:
    """Aggregate death log → summary for observer synthesis."""
    log_path = root / DEATH_STORE
    if not log_path.exists():
        return {}
    try:
        events = json.loads(log_path.read_text("utf-8"))
    except Exception:
        return {}
    if not events:
        return {}

    total = len(events)
    by_cause = {}
    by_node = {}
    for e in events:
        cause = e.get("cause", "unknown")
        by_cause[cause] = by_cause.get(cause, 0) + 1
        node = e.get("node", "unknown")
        by_node[node] = by_node.get(node, 0) + 1

    # Most lethal nodes
    worst_nodes = sorted(by_node.items(), key=lambda x: x[1], reverse=True)[:5]
    scores = [e.get("score", 0) for e in events]
    avg_score = round(sum(scores) / len(scores), 3)

    # Critical deaths (stale_import, exception, timeout)
    critical = sum(1 for e in events if e.get("severity") in ("critical", "high"))

    return {
        "total_deaths": total,
        "by_cause": by_cause,
        "worst_nodes": [{"node": n, "deaths": c} for n, c in worst_nodes],
        "avg_death_score": avg_score,
        "critical_count": critical,
        "critical_rate": round(critical / max(total, 1), 3),
    }
