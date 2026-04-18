"""module_identity_seq001_v001_alias_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 33 lines | ~384 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _build_alias_map(sources: dict) -> dict:
    """Build bidirectional alias map: pigeon_name <-> original_name.

    The numeric surface and file_profiles use original names (e.g. dynamic_prompt)
    while the registry uses pigeon names (e.g. 推w_dp). We need both directions.
    """
    aliases = {}  # pigeon_name -> original_name
    surface_nodes = sources['numeric_surface_seq001_v001'].get('nodes', {})
    profile_keys = set(sources['file_profiles'].keys())

    # Surface nodes with edges are the "real" names. Pigeon names have 0 edges.
    nodes_with_edges = {k for k, v in surface_nodes.items() if v.get('degree', 0) > 0}

    # Registry files have both pigeon and original names via seq matching
    for entry in sources['registry'].get('files', []):
        name = entry.get('name', '')
        seq = entry.get('seq', 0)
        if name in nodes_with_edges:
            continue  # already a real name with edges
        # Check if this pigeon name maps to an original name in the graph
        # Look at file_profiles which uses original names
        for orig in profile_keys:
            if orig in nodes_with_edges:
                # Check if they share the same seq AND path prefix
                orig_node = surface_nodes.get(orig, {})
                my_node = surface_nodes.get(name, {})
                if orig_node.get('seq') == seq and seq > 0:
                    aliases[name] = orig
                    break
    return aliases
