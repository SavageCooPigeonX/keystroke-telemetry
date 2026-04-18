"""包p_cpk_s001_v002_d0324_缩分话_λε_factory_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 13 lines | ~89 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

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
