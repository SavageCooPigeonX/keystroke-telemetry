"""脉运w_vt_s006_v003_d0401_唤分话_λA_helpers_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 16 lines | ~170 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from typing import Any

def _build_vein_lookup(veins_data: dict[str, Any]) -> dict[str, float]:
    """Extract module → vein_score from veins JSON."""
    lookup: dict[str, float] = {}
    for node in veins_data.get("arteries", []):
        lookup[node["module"]] = node.get("vein_score", 1.0)
    for node in veins_data.get("clots", []):
        lookup[node["module"]] = node.get("vein_score", 0.0)
    return lookup


def _build_clot_set(veins_data: dict[str, Any]) -> set[str]:
    """Extract set of clot module names."""
    return {n["module"] for n in veins_data.get("clots", [])}
