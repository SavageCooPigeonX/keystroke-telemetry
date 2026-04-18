"""numeric_surface_seq001_v001_traversal_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 14 lines | ~141 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def _compressed_traversal(surface: dict, top_n: int = 12) -> list[str]:
    """Traversal strings for highest-heat nodes using addresses."""
    ranked = sorted(surface.items(), key=lambda x: -x[1].get("heat", 0))[:top_n]
    paths = []
    for addr, data in ranked:
        edges = data.get("edges_out", [])
        if not edges:
            paths.append(addr)
            continue
        chain = " > ".join(edges[:5])
        paths.append(f"{addr} > {chain}")
    return paths
