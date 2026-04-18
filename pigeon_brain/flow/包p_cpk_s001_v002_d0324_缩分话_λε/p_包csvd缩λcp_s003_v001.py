"""包p_cpk_s001_v002_d0324_缩分话_λε_context_packet_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 62 lines | ~628 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ContextPacket:
    """The flowing unit of cognition."""
    origin: str                                    # source node name
    task_seed: str                                 # original question / bug / task
    path: list[str] = field(default_factory=list)  # nodes visited in order
    accumulated: list[NodeIntel] = field(default_factory=list)
    heat: float = 0.0                              # running heat (increases through hot zones)
    importance: float = 1.0                        # decays per hop
    fear_chain: list[str] = field(default_factory=list)
    narrative_fragments: list[str] = field(default_factory=list)
    dead_vein_warnings: list[str] = field(default_factory=list)
    depth: int = 0
    alive: bool = True
    mode: str = "targeted"                         # targeted | heat | failure

    # ── lifecycle ──

    def step(self) -> None:
        """Called after each node visit. Applies decay + death checks."""
        self.depth += 1
        self.importance *= IMPORTANCE_DECAY
        if self.depth >= MAX_DEPTH:
            self.alive = False
        if len(self.accumulated) > MAX_ACCUMULATED:
            self.alive = False

    def visit(self, node_name: str) -> bool:
        """Check if we already visited this node (loop detection)."""
        return node_name in self.path

    def append_intel(self, intel: NodeIntel) -> None:
        """Add a node's intelligence to the accumulator."""
        if not self.alive:
            return
        self.accumulated.append(intel)
        self.heat += intel.dual_score
        for fear in intel.fears:
            self.fear_chain.append(f"{intel.node}: {fear}")

    # ── summary ──

    def summary(self) -> dict[str, Any]:
        """Compact summary for serialization / task writing."""
        return {
            "origin": self.origin,
            "task_seed": self.task_seed,
            "mode": self.mode,
            "path": self.path,
            "depth": self.depth,
            "heat": round(self.heat, 3),
            "importance": round(self.importance, 3),
            "alive": self.alive,
            "nodes_touched": len(self.accumulated),
            "fears_collected": len(self.fear_chain),
            "dead_veins": len(self.dead_vein_warnings),
            "narrative_fragments": len(self.narrative_fragments),
        }
