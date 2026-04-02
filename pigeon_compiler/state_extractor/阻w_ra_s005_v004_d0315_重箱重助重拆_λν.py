"""resistance_analyzer_seq005_v001.py — Classify WHY a file resists splitting.

9 resistance patterns scored 0.0-1.0. Aggregate score drives the decision:
  < 0.3 → auto-extract (trivial)
  0.3-0.7 → DeepSeek plans the cut
  > 0.7 → flag for human review
"""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v004 | 97 lines | ~1,039 tokens
# DESC:   classify_why_a_file_resists
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import ast
from pathlib import Path

PATTERNS = {
    "PROMPT_BLOB": 0.3,
    "PURE_FUNCTIONS": 0.1,
    "COUPLED_CLUSTER": 0.5,
    "SHARED_STATE": 0.6,
    "STRING_SURGERY": 0.7,
    "FLASK_ROUTES": 0.4,
    "TEST_MONSOON": 0.5,
    "IMPORT_WEB": 0.8,
    "GOD_ORCHESTRATOR": 0.9,
}


def analyze_resistance(file_path: str | Path, call_graph: dict,
                       shared_state: dict, inbound_count: int) -> dict:
    """Classify resistance patterns and compute aggregate score."""
    source = Path(file_path).read_text(encoding='utf-8')
    tree = ast.parse(source)
    found = []

    # PROMPT_BLOB — large string constants (>20 lines) inside functions
    # Also detect f-strings (JoinedStr) by checking source line span
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.count('\n') > 20:
                found.append({"pattern": "PROMPT_BLOB",
                               "detail": f"~{node.value.count(chr(10))} line string at L{node.lineno}"})
        elif isinstance(node, ast.JoinedStr):
            # f-string: estimate size from line span
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                span = (node.end_lineno or node.lineno) - node.lineno
                if span > 20:
                    found.append({"pattern": "PROMPT_BLOB",
                                   "detail": f"~{span} line f-string at L{node.lineno}"})

    # COUPLED_CLUSTER — any cluster with >2 mutually-calling functions
    _check_clusters(call_graph, found)

    # SHARED_STATE — mutable module-level vars used by >2 functions
    mutable_shared = [n for n, d in shared_state.items() if not d["is_const"] and len(d["used_by"]) > 1]
    if mutable_shared:
        found.append({"pattern": "SHARED_STATE", "detail": f"mutable: {mutable_shared}"})

    # FLASK_ROUTES — has @app.route or @bp.route decorators
    if 'route' in source and ('@app.' in source or '@bp.' in source or 'Blueprint' in source):
        found.append({"pattern": "FLASK_ROUTES", "detail": "Flask route decorators detected"})

    # TEST_MONSOON — file with >10 test functions
    test_fns = [n for n in call_graph if n.startswith('test_')]
    if len(test_fns) > 10:
        found.append({"pattern": "TEST_MONSOON", "detail": f"{len(test_fns)} test functions"})

    # IMPORT_WEB — imported by many other files
    if inbound_count > 5:
        found.append({"pattern": "IMPORT_WEB", "detail": f"imported by {inbound_count} files"})

    # GOD_ORCHESTRATOR — one function that calls >6 other local functions
    for fn, calls in call_graph.items():
        if len(calls) > 6:
            found.append({"pattern": "GOD_ORCHESTRATOR", "detail": f"{fn}() calls {len(calls)} functions"})

    # PURE_FUNCTIONS fallback — no other patterns found
    if not found:
        found.append({"pattern": "PURE_FUNCTIONS", "detail": "independent functions, easy split"})

    # Aggregate score — take max of found patterns
    score = max(PATTERNS.get(f["pattern"], 0.0) for f in found)
    verdict = "AUTO_EXTRACT" if score < 0.3 else "DEEPSEEK_PLAN" if score <= 0.7 else "HUMAN_REVIEW"

    return {"patterns": found, "score": round(score, 2), "verdict": verdict}


def _check_clusters(graph, found):
    from pigeon_compiler.state_extractor.演p_cg_s002_v004_d0315_重箱重助重拆_λν import find_clusters
    clusters = find_clusters(graph)
    big = [c for c in clusters if len(c) > 2]
    if big:
        found.append({"pattern": "COUPLED_CLUSTER",
                       "detail": f"{len(big)} cluster(s) with >2 functions"})
