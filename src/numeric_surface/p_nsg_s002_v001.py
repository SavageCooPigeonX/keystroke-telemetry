"""numeric_surface_seq001_v001_graph_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 33 lines | ~320 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_or_rebuild_graph(root: Path, registry: dict | list) -> dict:
    """Load graph_cache.json, but self-heal when coverage is obviously stale."""
    cache_path = root / "pigeon_brain" / "graph_cache.json"
    graph = _load_json(cache_path)
    if not isinstance(graph, dict):
        graph = {}
    nodes = graph.get("nodes", {}) if isinstance(graph.get("nodes"), dict) else {}

    reg_files = registry.get("files", []) if isinstance(registry, dict) else registry
    reg_names = {
        f.get("name", "")
        for f in (reg_files if isinstance(reg_files, list) else [])
        if f.get("name")
    }
    missing = reg_names - set(nodes)

    cache_stale = not cache_path.exists()
    if not cache_stale and (root / "pigeon_registry.json").exists():
        try:
            cache_stale = cache_path.stat().st_mtime < (root / "pigeon_registry.json").stat().st_mtime
        except OSError:
            cache_stale = False

    coverage_bad = bool(reg_names) and len(missing) > max(10, int(len(reg_names) * 0.05))
    if not cache_stale and not coverage_bad:
        return graph

    rebuilt = _rebuild_graph_cache(root)
    return rebuilt or graph
