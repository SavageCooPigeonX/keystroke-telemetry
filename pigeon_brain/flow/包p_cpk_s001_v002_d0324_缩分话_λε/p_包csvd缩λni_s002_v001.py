"""包p_cpk_s001_v002_d0324_缩分话_λε_node_intel_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 19 lines | ~186 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field

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
