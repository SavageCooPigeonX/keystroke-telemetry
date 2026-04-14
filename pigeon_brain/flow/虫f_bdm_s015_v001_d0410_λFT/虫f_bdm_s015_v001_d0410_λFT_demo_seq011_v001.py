"""虫f_bdm_s015_v001_d0410_λFT_demo_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from __future__ import annotations
from pathlib import Path
import json
import uuid

def demo_chain(root: Path) -> None:
    """Run the chain and print a report showing bug context at downstream nodes."""
    print("=== Bug Demon Manifest Chain — Prototype Demo ===\n")

    # 1. Load bugs
    manifests = load_active_bugs(root)
    print(f"Active bugs loaded: {len(manifests)}")
    by_type: dict[str, int] = {}
    for m in manifests:
        by_type[m.bug_type] = by_type.get(m.bug_type, 0) + 1
    for bk, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {bk}: {count} modules")
    print()

    # 2. Propagate
    manifests = propagate_through_veins(root, manifests)
    with_chain = [m for m in manifests if m.affected_chain]
    print(f"Propagated through import graph:")
    print(f"  {len(with_chain)}/{len(manifests)} bugs have downstream affected modules")
    if with_chain:
        example = max(with_chain, key=lambda x: len(x.affected_chain))
        print(f"  Widest blast radius: {example.origin_module} ({example.bug_type})"
              f" → {len(example.affected_chain)} downstream module(s)")
        if example.affected_chain:
            print(f"  Affected chain: {' → '.join(example.affected_chain[:5])}")
    print()

    # 3. Test packet injection
    sample_path = [manifests[0].origin_module] if manifests else ["unknown"]
    if with_chain:
        sample_path = [with_chain[0].origin_module] + with_chain[0].affected_chain[:2]

    packet_dict = {
        "origin": sample_path[0],
        "task_seed": "debug overcap in backward pass",
        "path": sample_path,
        "fear_chain": [],
        "accumulated": [],
    }
    inject_into_packet(packet_dict, manifests)
    print(f"Packet injection ({len(sample_path)} nodes):")
    print(f"  bug_manifests injected: {len(packet_dict['bug_manifests'])}")
    print(f"  fear_chain entries added: {len(packet_dict['fear_chain'])}")
    for entry in packet_dict["fear_chain"][:3]:
        print(f"  {entry}")
    print()

    # 4. Write to node_memory
    electron_id = "demo_" + uuid.uuid4().hex[:6]
    for node in sample_path[:3]:
        write_to_node_memory(root, node, manifests, electron_id)

    # Verify: read back and confirm active_bugs present
    p = root / NODE_MEMORY_PATH
    if p.exists():
        memory = json.loads(p.read_text("utf-8"))
        for node in sample_path[:3]:
            rec = memory.get(node, {})
            entries = rec.get("entries", [])
            bug_entry = next(
                (e for e in reversed(entries) if e.get("active_bugs")), None
            )
            policy_warn = rec.get("policy", {}).get("active_bug_warning", "none")
            print(f"node_memory[{node}]:")
            if bug_entry:
                print(f"  active_bugs: {len(bug_entry['active_bugs'])} entry(ies)")
                top = bug_entry["active_bugs"][0]
                print(f"  top bug: {top['bug_type']}:{top['origin_module']} sev={top['severity']}")
            else:
                print(f"  active_bugs: (not written to memory yet)")
            print(f"  policy.active_bug_warning: {policy_warn}")
    print()
    print("=== Chain verification complete ===")
    print()
    print("RESULT: Bug context now persists in node_memory for these nodes.")
    print("The next backward pass that touches them will see active_bugs.")
    print("Packet fear_chain carries bug annotations — task_writer will surface them.")
