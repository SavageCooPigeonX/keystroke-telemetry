"""ether_map_builder_seq006_v001.py — Assemble full Ether Map JSON for a file.

Orchestrates seq001-seq005 into a single dependency graph document.
This is the primary entry point for Layer 1.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v004 | 65 lines | ~707 tokens
# DESC:   assemble_full_ether_map_json
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import json
from pathlib import Path
from pigeon_compiler.state_extractor.ast_parser_seq001_v004_d0315__parse_python_file_into_function_lc_verify_pigeon_plugin import parse_file
from pigeon_compiler.state_extractor.call_graph_seq002_v004_d0315__build_intra_file_call_graph_lc_verify_pigeon_plugin import (
    build_call_graph, find_clusters, compute_call_depth)
from pigeon_compiler.state_extractor.import_tracer_seq003_v004_d0315__trace_imports_inbound_and_outbound_lc_verify_pigeon_plugin import (
    trace_outbound, trace_inbound)
from pigeon_compiler.state_extractor.shared_state_detector_seq004_v004_d0315__detect_module_level_shared_state_lc_verify_pigeon_plugin import (
    detect_shared_state, compute_coupling_score)
from pigeon_compiler.state_extractor.resistance_analyzer_seq005_v004_d0315__classify_why_a_file_resists_lc_verify_pigeon_plugin import (
    analyze_resistance)

PROJECT_ROOT = Path(__file__).parent.parent.parent


def build_ether_map(file_path: str | Path) -> dict:
    """Build the complete Ether Map for a single Python file."""
    fp = Path(file_path)

    parsed = parse_file(fp)
    call_graph = build_call_graph(fp)
    clusters = find_clusters(call_graph)
    call_depth = compute_call_depth(call_graph)
    outbound = trace_outbound(fp)
    inbound = trace_inbound(fp, PROJECT_ROOT)
    shared = detect_shared_state(fp)
    coupling = compute_coupling_score(shared)
    resistance = analyze_resistance(fp, call_graph, shared, len(inbound))

    return {
        "file": str(fp.relative_to(PROJECT_ROOT)),
        "total_lines": parsed["total_lines"],
        "functions": parsed["functions"],
        "classes": parsed["classes"],
        "constants": parsed["constants"],
        "call_graph": call_graph,
        "call_depth": call_depth,
        "clusters": [sorted(c) for c in clusters],
        "imports": {"outbound": outbound, "inbound": inbound},
        "shared_state": {k: v for k, v in shared.items()},
        "coupling_score": coupling,
        "resistance": resistance,
    }


def save_ether_map(ether_map: dict, out_path: str | Path = None):
    """Save ether map to JSON file."""
    if out_path is None:
        out_path = PROJECT_ROOT / "codebase_auditor" / ".ether_cache.json"
    Path(out_path).write_text(json.dumps(ether_map, indent=2, default=str),
                              encoding='utf-8')
    return out_path
