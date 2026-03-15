"""call_graph_seq002_v001.py — Build intra-file call graph via AST walk.

For each function, finds which OTHER functions in the same file it calls.
This is the key input for cluster grouping — functions that call each
other should stay together after extraction.
"""
import ast
from pathlib import Path


def build_call_graph(file_path: str | Path) -> dict:
    """Return {func_name: [called_func_names]} for all top-level functions."""
    source = Path(file_path).read_text(encoding='utf-8')
    tree = ast.parse(source)

    # Collect all top-level function names (the universe of local calls)
    local_names = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local_names.add(node.name)

    # For each function, find calls to other local functions
    graph = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            called = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    name = _call_name(child)
                    if name and name in local_names and name != node.name:
                        called.add(name)
            graph[node.name] = sorted(called)

    return graph


def find_clusters(graph: dict) -> list[set]:
    """Find connected components — groups of mutually-calling functions."""
    visited, clusters = set(), []
    adj = {k: set(v) for k, v in graph.items()}
    # Make undirected (if A calls B, B is connected to A)
    for fn, calls in list(adj.items()):
        for c in calls:
            adj.setdefault(c, set()).add(fn)

    for fn in adj:
        if fn not in visited:
            cluster = set()
            _dfs(fn, adj, visited, cluster)
            clusters.append(cluster)
    return clusters


def _dfs(node, adj, visited, cluster):
    visited.add(node)
    cluster.add(node)
    for neighbor in adj.get(node, []):
        if neighbor not in visited:
            _dfs(neighbor, adj, visited, cluster)


def _call_name(node: ast.Call) -> str | None:
    """Extract function name from a Call node (simple names only)."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def compute_call_depth(graph: dict) -> dict:
    """Compute distance from GOD_ORCHESTRATOR (most-calling func) for each function.

    Returns {func_name: distance} where 0 = the god func itself.
    Functions at distance >=2 are the easiest extraction targets.
    """
    if not graph:
        return {}

    # Find the god function (most outbound calls)
    god = max(graph, key=lambda k: len(graph[k]))

    # BFS from god
    depths = {god: 0}
    queue = [god]
    while queue:
        current = queue.pop(0)
        for callee in graph.get(current, []):
            if callee not in depths:
                depths[callee] = depths[current] + 1
                queue.append(callee)

    # Functions not reachable from god (isolated)
    for fn in graph:
        if fn not in depths:
            depths[fn] = 999  # unreachable = easy to extract

    return depths
