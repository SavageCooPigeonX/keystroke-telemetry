"""虫f_bdm_s015_v001_d0410_λFT_inject_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from dataclasses import dataclass, field, asdict
from typing import Any

def inject_into_packet(
    packet_dict: dict[str, Any],
    manifests: list[BugManifest],
) -> dict[str, Any]:
    """Stamp relevant BugManifests onto a packet dict (in-place).

    Matches manifests against the packet's path. If any node in the path
    is either bug origin OR in the affected_chain, the manifest travels
    with the packet.

    Works with the dict representation (from packet.__dict__ or asdict).
    Does not require modifying ContextPacket's dataclass.
    """
    path_nodes = set(packet_dict.get("path", []))
    relevant: list[dict] = []
    for m in manifests:
        touches = path_nodes & ({m.origin_module} | set(m.affected_chain))
        if touches:
            d = asdict(m)
            d["touches"] = sorted(touches)
            relevant.append(d)

    packet_dict["bug_manifests"] = relevant
    # Also append to fear_chain (existing field — surfaces in task_writer output)
    fear_chain: list[str] = packet_dict.get("fear_chain", [])
    for m in relevant:
        fear_chain.append(
            f"[BUG:{m['bug_type']}] {m['origin_module']} — {m['notes']}"
        )
    packet_dict["fear_chain"] = fear_chain
    return packet_dict
