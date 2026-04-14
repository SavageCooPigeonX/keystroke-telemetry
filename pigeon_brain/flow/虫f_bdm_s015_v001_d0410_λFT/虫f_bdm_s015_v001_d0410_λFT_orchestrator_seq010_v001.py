"""虫f_bdm_s015_v001_d0410_λFT_orchestrator_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

def run_propagation(root: Path) -> dict[str, Any]:
    """Full pipeline: load bugs → propagate → write to node_memory.

    Returns a summary dict suitable for verification.
    """
    manifests = load_active_bugs(root)
    if not manifests:
        return {"status": "no_bugs", "manifests": 0}

    manifests = propagate_through_veins(root, manifests)

    electron_id = "bdm_" + uuid.uuid4().hex[:8]
    nodes_touched: set[str] = set()

    for m in manifests:
        # Write to origin node
        write_to_node_memory(root, m.origin_module, manifests, electron_id)
        nodes_touched.add(m.origin_module)
        # Write to each downstream node
        for node in m.affected_chain:
            write_to_node_memory(root, node, manifests, electron_id)
            nodes_touched.add(node)

    summary = {
        "electron_id": electron_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "manifests_built": len(manifests),
        "nodes_touched": sorted(nodes_touched),
        "nodes_touched_count": len(nodes_touched),
        "by_type": {
            bk: sum(1 for m in manifests if m.bug_type == bk)
            for bk in BUG_SEVERITY
        },
        "top_severity": sorted(
            [{"bug_id": m.bug_id, "sev": m.severity, "chain_len": len(m.affected_chain)}
             for m in manifests],
            key=lambda x: -x["sev"],
        )[:10],
    }
    _log_chain(root, summary)
    return summary
