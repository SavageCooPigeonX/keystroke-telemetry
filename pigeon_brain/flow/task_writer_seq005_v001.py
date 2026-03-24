# ┌──────────────────────────────────────────────┐
# │  task_writer — terminal node: writes enriched  │
# │  tasks from accumulated packet intelligence    │
# │  pigeon_brain/flow                             │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
"""
The river delta. Where all flowing intelligence collects and deposits.

A packet that has traversed the graph carries the memory of every node
it touched. The task writer synthesizes that into a task that isn't just
"what to fix" but "what to fix, why it's scary, who tried before, what
the operator felt, and which modules will scream if you change it."

Two output modes:
  - write_task()    → Markdown task for humans/Copilot
  - write_multi()   → Merged output from multiple perspectives
"""
from __future__ import annotations

from .context_packet_seq001_v001 import ContextPacket


def write_task(packet: ContextPacket) -> str:
    """
    Synthesize a completed packet into an enriched Markdown task.
    """
    lines: list[str] = []

    # Header
    lines.append(f"## Task: {packet.task_seed}")
    lines.append("")
    lines.append(f"**Mode:** {packet.mode} | "
                 f"**Path depth:** {packet.depth} nodes | "
                 f"**Heat:** {packet.heat:.2f} | "
                 f"**Importance:** {packet.importance:.2f}")
    lines.append(f"**Path:** {' → '.join(packet.path)}")
    lines.append("")

    # Heat warnings
    if packet.heat > 2.0:
        lines.append("⚠️ **HIGH HEAT PATH** — multiple dangerous nodes touched")
        lines.append("")
    elif packet.heat > 1.0:
        lines.append("🟠 **WARM PATH** — moderate risk zone")
        lines.append("")

    # Dead vein warnings
    if packet.dead_vein_warnings:
        lines.append("**Dead veins crossed:**")
        for warn in packet.dead_vein_warnings:
            lines.append(f"- 🔴 {warn}")
        lines.append("")

    # Node intelligence summary (only the awakened ones)
    if packet.accumulated:
        lines.append("**Nodes that contributed intelligence:**")
        lines.append("")
        for intel in packet.accumulated:
            badge = ""
            if intel.dual_score > 0.5:
                badge = " 🔥"
            elif intel.human_hesitation > 0.6:
                badge = " 😰"
            line = (f"- **{intel.node}** v{intel.version}"
                    f" ({intel.personality}){badge}"
                    f" — dual={intel.dual_score:.2f},"
                    f" hes={intel.human_hesitation:.2f},"
                    f" deaths={intel.dead_limbs}")
            if intel.clot_signals:
                line += f" | clot: {', '.join(intel.clot_signals[:2])}"
            lines.append(line)
        lines.append("")

    # Fear chain — the accumulated warnings
    if packet.fear_chain:
        lines.append("**Fears along this path:**")
        for fear in packet.fear_chain:
            lines.append(f"- {fear}")
        lines.append("")

    # Narrative fragments — what the nodes remember
    if packet.narrative_fragments:
        lines.append("**What the nodes remember:**")
        for frag in packet.narrative_fragments:
            lines.append(f"- {frag}")
        lines.append("")

    # Slumber parties (coupled modules on the path)
    partners = set()
    for intel in packet.accumulated:
        for p in intel.slumber_parties:
            if p not in set(packet.path):
                partners.add(f"{intel.node} ↔ {p}")
    if partners:
        lines.append("**Coupled modules (may cascade):**")
        for pair in sorted(partners):
            lines.append(f"- {pair}")
        lines.append("")

    # The enriched instruction
    lines.append("---")
    lines.append("")
    lines.append(f"**Enriched instruction:** {packet.task_seed}")
    ctx = []
    ctx.append(f"{len(packet.accumulated)} nodes' intelligence")
    ctx.append(f"{len(packet.fear_chain)} documented fears")
    ctx.append(f"cumulative heat {packet.heat:.2f}")
    if packet.dead_vein_warnings:
        ctx.append(f"{len(packet.dead_vein_warnings)} dead veins")
    lines.append(f"*Approached with awareness of: {', '.join(ctx)}.*")

    return "\n".join(lines)


def write_multi(packets: list[ContextPacket]) -> str:
    """
    Merge multiple perspective packets into a single enriched task.

    Each packet ran through a different path mode (targeted, heat, failure)
    for the same task seed. The merged output shows all perspectives.
    """
    if not packets:
        return "*No packets completed.*"

    seed = packets[0].task_seed
    lines: list[str] = []
    lines.append(f"# Multi-Perspective Task: {seed}")
    lines.append("")
    lines.append(f"*{len(packets)} traversals through the same graph.*")
    lines.append("")

    # Summary table
    lines.append("| Mode | Depth | Heat | Nodes | Fears | Dead Veins |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for p in packets:
        lines.append(
            f"| {p.mode} | {p.depth} | {p.heat:.2f}"
            f" | {len(p.accumulated)} | {len(p.fear_chain)}"
            f" | {len(p.dead_vein_warnings)} |"
        )
    lines.append("")

    # Consensus fears (appeared in 2+ paths)
    all_fears: dict[str, int] = {}
    for p in packets:
        for fear in p.fear_chain:
            all_fears[fear] = all_fears.get(fear, 0) + 1
    consensus = {f: c for f, c in all_fears.items() if c >= 2}
    if consensus:
        lines.append("**Consensus fears (multiple paths agree):**")
        for fear, count in sorted(consensus.items(), key=lambda x: -x[1]):
            lines.append(f"- [{count}/{len(packets)}] {fear}")
        lines.append("")

    # Each perspective
    for p in packets:
        lines.append(f"### {p.mode.upper()} perspective")
        lines.append("")
        lines.append(write_task(p))
        lines.append("")

    return "\n".join(lines)
