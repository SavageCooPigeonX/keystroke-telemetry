"""Context vein/clot analyzer — scores import graph health for self-trim.

VEINS  = healthy import paths (data flow arteries)
CLOTS  = dead/bloated files (no relationships, stale imports, unused exports)

Composes existing infrastructure:
  - graph_extractor: import edges
  - node_tester: dead import / unused export / dead edge checks
  - file_heat_map: cognitive load data
  - pigeon_registry: module metadata
  - dual_substrate: merged human/agent heat

Outputs context_veins.json consumed by dynamic_prompt for self-trim injection.
"""

import ast
import json
import time
from datetime import datetime, timezone
from pathlib import Path

VEINS_PATH = "pigeon_brain/context_veins.json"
REGISTRY_PATH = "pigeon_registry.json"
HEAT_MAP_PATH = "file_heat_map.json"
DUAL_VIEW_PATH = "pigeon_brain/dual_view.json"
SELF_FIX_DIR = "docs/self_fix"

# Thresholds
CLOT_SCORE_THRESHOLD = 0.4     # above this = recommend trim
HIGH_DEGREE_ARTERY = 5         # in-degree >= this = critical artery
STALE_DAYS = 30                # no edit in N days = stale signal


def analyze_veins(root: Path) -> dict:
    """Run full vein/clot analysis. Returns the context_veins structure."""
    graph = _load_graph(root)
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    heat = _load_heat_map(root)
    dual = _load_dual_view(root)
    registry = _load_registry(root)
    self_fix_problems = _load_latest_self_fix(root)

    # Build per-node analysis
    node_scores = {}
    for name, node in nodes.items():
        clot_signals = []
        vein_signals = []

        in_degree = len(node.get("edges_in", []))
        out_degree = len(node.get("edges_out", []))

        # --- CLOT signals ---
        # Isolated: no edges in either direction
        if in_degree == 0 and out_degree == 0:
            clot_signals.append("isolated")

        # Orphan: nobody imports this module (skip entry points)
        _entry_patterns = ("cli", "main", "test", "demo", "run_", "traced_runner", "stress")
        if in_degree == 0 and out_degree > 0:
            if not any(kw in name for kw in _entry_patterns):
                clot_signals.append("orphan_no_importers")

        # Dead imports (file imports things it doesn't use)
        fpath = root / node.get("path", "")
        dead_imports = []
        if fpath.exists():
            try:
                source = fpath.read_text(encoding="utf-8")
                dead_imports = _find_dead_imports(source)
                if dead_imports:
                    clot_signals.append(f"dead_imports:{len(dead_imports)}")
            except Exception:
                pass

        # Unused exports (exports nobody consumes)
        unused_exports = _check_unused_exports(name, nodes)
        if unused_exports:
            clot_signals.append(f"unused_exports:{len(unused_exports)}")

        # Oversize (>200 lines = bloat)
        lines = _count_lines(fpath)
        if lines > 200:
            clot_signals.append(f"oversize:{lines}")

        # High cognitive load (heat map)
        mod_heat = heat.get(name, {})
        avg_hes = mod_heat.get("avg_hes", 0)
        miss_count = mod_heat.get("miss_count", 0)
        if avg_hes > 0.7:
            clot_signals.append(f"high_hesitation:{avg_hes:.2f}")
        if miss_count >= 3:
            clot_signals.append(f"high_miss:{miss_count}")

        # Stale (not edited recently — check registry date)
        reg_entry = registry.get(name, {})
        last_date = reg_entry.get("date", "")
        if last_date and _is_stale(last_date):
            clot_signals.append("stale")

        # Self-fix known problems (from latest report)
        node_problems = self_fix_problems.get(name, [])
        for prob in node_problems:
            sev = prob.get("severity", "low")
            ptype = prob.get("type", "")
            if ptype == "dead_export":
                clot_signals.append(f"self_fix:dead_export:{prob.get('function', '?')}")
            elif ptype == "hardcoded_import":
                clot_signals.append("self_fix:hardcoded_import")
            elif ptype == "high_coupling":
                clot_signals.append(f"self_fix:high_coupling:{prob.get('fan_in', 0)}")

        # --- VEIN signals ---
        if in_degree >= HIGH_DEGREE_ARTERY:
            vein_signals.append(f"critical_artery:in_degree={in_degree}")

        if out_degree >= 3 and in_degree >= 2:
            vein_signals.append("hub")

        if avg_hes < 0.3 and in_degree >= 1:
            vein_signals.append("low_friction")

        # Compute scores
        clot_score = _compute_clot_score(clot_signals, in_degree, out_degree, lines, avg_hes)
        vein_score = _compute_vein_score(vein_signals, in_degree, out_degree, avg_hes)

        node_scores[name] = {
            "in_degree": in_degree,
            "out_degree": out_degree,
            "lines": lines,
            "clot_score": round(clot_score, 3),
            "clot_signals": clot_signals,
            "vein_score": round(vein_score, 3),
            "vein_signals": vein_signals,
            "dead_imports": dead_imports[:5],
            "unused_exports": unused_exports[:5],
        }

    # Build edge health map
    vein_edges = []
    for edge in edges:
        src = edge.get("from", "")
        tgt = edge.get("to", "")
        src_score = node_scores.get(src, {})
        tgt_score = node_scores.get(tgt, {})
        # Edge health = average of endpoint vein scores
        health = (src_score.get("vein_score", 0.5) + tgt_score.get("vein_score", 0.5)) / 2
        vein_edges.append({
            "from": src,
            "to": tgt,
            "health": round(health, 3),
            "type": edge.get("type", "import"),
        })

    # Identify clots and arteries
    clots = sorted(
        [{"module": n, **s} for n, s in node_scores.items()
         if s["clot_score"] >= CLOT_SCORE_THRESHOLD],
        key=lambda x: -x["clot_score"]
    )
    arteries = sorted(
        [{"module": n, **s} for n, s in node_scores.items()
         if s["vein_score"] >= 0.6],
        key=lambda x: -x["vein_score"]
    )

    # Generate trim recommendations
    trim_recs = _generate_trim_recommendations(clots, node_scores, nodes)

    # Stats
    alive = sum(1 for s in node_scores.values() if s["clot_score"] < CLOT_SCORE_THRESHOLD)
    avg_vein = sum(s["vein_score"] for s in node_scores.values()) / max(len(node_scores), 1)

    result = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "total_nodes": len(node_scores),
            "alive": alive,
            "clots": len(clots),
            "arteries": len(arteries),
            "avg_vein_health": round(avg_vein, 3),
            "total_edges": len(edges),
        },
        "clots": clots[:20],
        "arteries": arteries[:10],
        "trim_recommendations": trim_recs[:10],
        "veins": vein_edges,
        "node_scores": node_scores,
    }

    # Write to disk
    out_path = root / VEINS_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return result


# ── Scoring ──────────────────────────────────────────────────────────────────

def _compute_clot_score(signals: list, in_deg: int, out_deg: int,
                        lines: int, avg_hes: float) -> float:
    """0.0 = healthy, 1.0 = dead clot."""
    score = 0.0
    for sig in signals:
        if sig == "isolated":
            score += 0.4
        elif sig == "orphan_no_importers":
            score += 0.3
        elif sig.startswith("dead_imports:"):
            score += min(int(sig.split(":")[1]) * 0.05, 0.2)
        elif sig.startswith("unused_exports:"):
            score += min(int(sig.split(":")[1]) * 0.05, 0.2)
        elif sig.startswith("oversize:"):
            score += 0.15
        elif sig.startswith("high_hesitation:"):
            score += 0.1
        elif sig.startswith("high_miss:"):
            score += 0.1
        elif sig == "stale":
            score += 0.1
        elif sig.startswith("self_fix:dead_export"):
            score += 0.05
        elif sig == "self_fix:hardcoded_import":
            score += 0.1
        elif sig.startswith("self_fix:high_coupling"):
            score += 0.05

    # Low connectivity is a clot signal
    if in_deg == 0:
        score += 0.1
    if out_deg == 0:
        score += 0.05

    return min(score, 1.0)


def _compute_vein_score(signals: list, in_deg: int, out_deg: int,
                        avg_hes: float) -> float:
    """0.0 = dead end, 1.0 = healthy artery."""
    score = 0.3  # baseline
    for sig in signals:
        if sig.startswith("critical_artery"):
            score += 0.3
        elif sig == "hub":
            score += 0.2
        elif sig == "low_friction":
            score += 0.1

    # Connectivity bonus
    score += min(in_deg * 0.05, 0.2)
    score += min(out_deg * 0.03, 0.1)

    # Penalty for high cognitive load
    if avg_hes > 0.5:
        score -= 0.1

    return max(min(score, 1.0), 0.0)


# ── Trim Recommendations ────────────────────────────────────────────────────

def _generate_trim_recommendations(clots: list, node_scores: dict,
                                   nodes: dict) -> list[dict]:
    """Generate actionable trim recommendations from clot analysis."""
    recs = []
    for clot in clots:
        name = clot["module"]
        signals = clot["clot_signals"]
        score = clot["clot_score"]

        if "isolated" in signals:
            recs.append({
                "action": "investigate",
                "target": name,
                "score": score,
                "reason": f"Isolated module (no imports in/out). May be dead code.",
                "signals": signals,
            })
        elif "orphan_no_importers" in signals:
            recs.append({
                "action": "investigate",
                "target": name,
                "score": score,
                "reason": f"Nobody imports this module. Check if it's an entry point or dead.",
                "signals": signals,
            })
        elif any(s.startswith("oversize") for s in signals):
            recs.append({
                "action": "split",
                "target": name,
                "score": score,
                "reason": f"Oversize + clot signals. Recommend pigeon split.",
                "signals": signals,
            })
        elif any(s.startswith("dead_imports") for s in signals):
            recs.append({
                "action": "clean_imports",
                "target": name,
                "score": score,
                "reason": f"Dead imports bloating the module.",
                "signals": signals,
            })
        else:
            recs.append({
                "action": "review",
                "target": name,
                "score": score,
                "reason": f"Multiple clot signals detected.",
                "signals": signals,
            })

    return recs


# ── Data Loaders ─────────────────────────────────────────────────────────────

def _load_graph(root: Path) -> dict:
    """Load graph from graph_extractor (import or cached)."""
    cache = root / "pigeon_brain" / "graph_cache.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text("utf-8"))
        except Exception:
            pass
    # Fallback: build fresh
    try:
        from pigeon_brain.graph_extractor_seq003_v003_d0324__extract_the_cognition_graph_from_lc_gemini_chat_dead import build_graph
        return build_graph(root)
    except Exception:
        return {"nodes": {}, "edges": []}


def _load_heat_map(root: Path) -> dict:
    p = root / HEAT_MAP_PATH
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:
        return {}


def _load_dual_view(root: Path) -> dict:
    p = root / DUAL_VIEW_PATH
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:
        return {}


def _load_registry(root: Path) -> dict:
    """Load registry as {name: entry} dict."""
    p = root / REGISTRY_PATH
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text("utf-8"))
        return {f.get("name", ""): f for f in data.get("files", [])}
    except Exception:
        return {}


def _load_latest_self_fix(root: Path) -> dict:
    """Load latest self_fix report, return {module_name: [problems]}."""
    sf_dir = root / SELF_FIX_DIR
    if not sf_dir.exists():
        return {}
    reports = sorted(sf_dir.glob("*.md"))
    if not reports:
        return {}
    latest = reports[-1]
    try:
        text = latest.read_text("utf-8")
    except Exception:
        return {}

    import re
    problems_by_module: dict[str, list] = {}
    # Parse markdown: ### N. [SEVERITY] type  then  - **File**: path
    current_problem: dict = {}
    for line in text.splitlines():
        m = re.match(r'^###\s+\d+\.\s+\[(\w+)\]\s+(\w+)', line)
        if m:
            if current_problem:
                _index_problem(problems_by_module, current_problem)
            current_problem = {"severity": m.group(1).lower(), "type": m.group(2)}
            continue
        if current_problem:
            fm = re.match(r'^-\s+\*\*File\*\*:\s+(.+)', line)
            if fm:
                current_problem["file"] = fm.group(1).strip()
            func_m = re.match(r'^-\s+\*\*Function\*\*:\s+`?(\w+)', line)
            if func_m:
                current_problem["function"] = func_m.group(1)
    if current_problem:
        _index_problem(problems_by_module, current_problem)
    return problems_by_module


def _index_problem(index: dict, problem: dict) -> None:
    """Index a self_fix problem by module name extracted from file path."""
    fpath = problem.get("file", "")
    if not fpath:
        return
    stem = Path(fpath).stem
    # Extract base module name (before _seq)
    import re
    m = re.match(r'^(.+?)_seq\d+', stem)
    name = m.group(1) if m else stem
    index.setdefault(name, []).append(problem)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _count_lines(fpath: Path) -> int:
    if not fpath.exists():
        return 0
    try:
        return len(fpath.read_text("utf-8").splitlines())
    except Exception:
        return 0


def _find_dead_imports(source: str) -> list[str]:
    """Find imports whose names are never referenced in the rest of the file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[-1]
                imported[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                imported[name] = f"{node.module}.{alias.name}" if node.module else alias.name
    if not imported:
        return []
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            used.add(node.attr)
    return [full for alias, full in imported.items() if alias not in used]


def _check_unused_exports(name: str, nodes: dict) -> list[str]:
    """Check if a module's public functions are imported by anyone."""
    node = nodes.get(name, {})
    edges_in = node.get("edges_in", [])
    if not edges_in:
        # No importers = all exports potentially unused
        # But don't flag entry points (CLI modules, __main__, test files)
        if any(kw in name for kw in ("cli", "main", "test", "demo", "run_")):
            return []
        return ["(all — no importers)"]
    return []


def _is_stale(date_str: str) -> bool:
    """Check if a pigeon date code (e.g. '0315') is > STALE_DAYS old."""
    try:
        if len(date_str) == 4:
            month = int(date_str[:2])
            day = int(date_str[2:])
            now = datetime.now(timezone.utc)
            file_date = now.replace(month=month, day=day)
            if file_date > now:
                file_date = file_date.replace(year=now.year - 1)
            return (now - file_date).days > STALE_DAYS
    except (ValueError, TypeError):
        pass
    return False


def get_trim_summary(root: Path) -> str:
    """Load context_veins.json and return a compact summary for prompt injection."""
    p = root / VEINS_PATH
    if not p.exists():
        return ""
    try:
        data = json.loads(p.read_text("utf-8"))
    except Exception:
        return ""

    stats = data.get("stats", {})
    clots = data.get("clots", [])
    recs = data.get("trim_recommendations", [])

    if not clots:
        return ""

    lines = [
        f"**Codebase Health:** {stats.get('alive', 0)}/{stats.get('total_nodes', 0)} alive, "
        f"{stats.get('clots', 0)} clots, avg vein health {stats.get('avg_vein_health', 0):.2f}",
        "",
    ]
    if clots:
        lines.append("**Clots (dead/bloated modules):**")
        for c in clots[:8]:
            sigs = ", ".join(c.get("clot_signals", []))
            lines.append(f"- `{c['module']}` (score={c['clot_score']:.2f}): {sigs}")

    if recs:
        lines.append("")
        lines.append("**Trim recommendations:**")
        for r in recs[:5]:
            lines.append(f"- [{r['action']}] `{r['target']}`: {r['reason']}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    result = analyze_veins(root)
    stats = result["stats"]
    print(f"Nodes: {stats['total_nodes']} | Alive: {stats['alive']} | "
          f"Clots: {stats['clots']} | Arteries: {stats['arteries']} | "
          f"Avg Vein Health: {stats['avg_vein_health']:.3f}")
    print(f"\nTop clots:")
    for c in result["clots"][:10]:
        print(f"  {c['module']}: score={c['clot_score']:.3f} signals={c['clot_signals']}")
    print(f"\nTrim recommendations:")
    for r in result["trim_recommendations"][:5]:
        print(f"  [{r['action']}] {r['target']}: {r['reason']}")
