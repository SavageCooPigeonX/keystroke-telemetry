"""numeric_surface_seq001_v001_load_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 39 lines | ~358 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_json(path: Path) -> dict | list:
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return {}


def _rebuild_graph_cache(root: Path) -> dict:
    """Rebuild graph_cache.json from the latest graph extractor when stale."""
    import importlib.util

    brain_dir = root / "pigeon_brain"
    cache_path = brain_dir / "graph_cache.json"
    candidates = sorted(
        brain_dir.glob("图p_ge_s*_v*.py"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        try:
            spec = importlib.util.spec_from_file_location("_graph_extractor", candidate)
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            build_graph = getattr(mod, "build_graph", None)
            if not callable(build_graph):
                continue
            graph = build_graph(root)
            if isinstance(graph, dict) and isinstance(graph.get("nodes"), dict):
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
                return graph
        except Exception:
            continue
    return {}
