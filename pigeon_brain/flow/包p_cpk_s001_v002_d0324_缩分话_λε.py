# ┌────────────────────────────────────────────┐
# │  context_packet — the flowing data structure │
# │  pigeon_brain/flow                           │
# └────────────────────────────────────────────┘
"""
The ContextPacket is the unit of cognition that flows through the graph.

It enters at a source node carrying a task seed. Each node it visits
appends its intelligence. Each edge it traverses can amplify or decay
the signal. By the time it reaches a terminal, it carries the accumulated
memory of every node it touched.

Strict size discipline: accumulated entries are capped. Importance decays
with depth. Packets die if they loop or exceed max depth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MAX_DEPTH = 15
MAX_ACCUMULATED = 30
IMPORTANCE_DECAY = 0.92


@dataclass
class NodeIntel:
    """Intelligence contributed by a single awakened node."""
    node: str
    version: int = 1
    personality: str = ""
    fears: list[str] = field(default_factory=list)
    human_hesitation: float = 0.0
    agent_death_rate: float = 0.0
    dual_score: float = 0.0
    dead_limbs: int = 0
    drama: int = 1            # version count = mutation drama
    slumber_parties: list[str] = field(default_factory=list)
    clot_signals: list[str] = field(default_factory=list)
    vein_score: float = 0.5
    relevance: float = 1.0    # how relevant this node was to the packet


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


def create_packet(
    origin: str,
    task_seed: str,
    mode: str = "targeted",
) -> ContextPacket:
    """Factory for a fresh packet at a source node."""
    return ContextPacket(
        origin=origin,
        task_seed=task_seed,
        mode=mode,
    )
