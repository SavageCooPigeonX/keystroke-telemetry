# ┌──────────────────────────────────────────────┐
# │  path_selector — chooses traversal strategy    │
# │  pigeon_brain/flow                             │
# └──────────────────────────────────────────────┘
"""
Three traversal modes, each a different perspective on the same graph:
TARGETED: follow dependencies outward from bug's node (depth-limited).
HEAT: greedy hill-climb toward highest dual_score (pain clusters).
FAILURE: follow historical death patterns (known bad routes).
The flow engine calls select_next() at each step.
"""

from __future__ import annotations

from typing import Any

MAX_TARGETED_DEPTH = 10
MAX_HEAT_DEPTH = 8
MAX_FAILURE_DEPTH = 6


def select_next(
    current: str,
    visited: set[str],
    mode: str,
    graph_data: dict[str, Any],
    depth: int = 0,
) -> str | None:
    """
    Choose the next node to visit.

    Returns node name or None to terminate the path.
    """
    if mode == "targeted":
        return _targeted_next(current, visited, graph_data, depth)
    elif mode == "heat":
        return _heat_next(current, visited, graph_data, depth)
    elif mode == "failure":
        return _failure_next(current, visited, graph_data, depth)
    return None


def _targeted_next(
    current: str,
    visited: set[str],
    graph: dict[str, Any],
    depth: int,
) -> str | None:
    """Follow dependency edges outward, breadth-first by edge count."""
    if depth >= MAX_TARGETED_DEPTH:
        return None

    nodes = graph.get("nodes", {})
    node = nodes.get(current, {})

    # Prefer edges_out (dependencies this node imports)
    candidates = [n for n in node.get("edges_out", []) if n not in visited]

    # If no outbound, try inbound (who depends on this node)
    if not candidates:
        candidates = [n for n in node.get("edges_in", []) if n not in visited]

    if not candidates:
        return None

    # Sort by degree (higher connectivity = richer intelligence)
    def _degree(name: str) -> int:
        n = nodes.get(name, {})
        return len(n.get("edges_out", [])) + len(n.get("edges_in", []))

    candidates.sort(key=_degree, reverse=True)
    return candidates[0]


def _heat_next(
    current: str,
    visited: set[str],
    graph: dict[str, Any],
    depth: int,
) -> str | None:
    """Greedy: always step toward highest dual_score neighbor."""
    if depth >= MAX_HEAT_DEPTH:
        return None

    nodes = graph.get("nodes", {})
    node = nodes.get(current, {})

    # All neighbors (both directions)
    neighbors = set(node.get("edges_out", [])) | set(node.get("edges_in", []))
    candidates = [n for n in neighbors if n not in visited]

    if not candidates:
        return None

    # Pick hottest neighbor
    def _heat(name: str) -> float:
        return nodes.get(name, {}).get("dual_score", 0.0)

    candidates.sort(key=_heat, reverse=True)
    return candidates[0]


def _failure_next(
    current: str,
    visited: set[str],
    graph: dict[str, Any],
    depth: int,
) -> str | None:
    """Follow paths with highest death/failure signals."""
    if depth >= MAX_FAILURE_DEPTH:
        return None

    nodes = graph.get("nodes", {})
    node = nodes.get(current, {})

    neighbors = set(node.get("edges_out", [])) | set(node.get("edges_in", []))
    candidates = [n for n in neighbors if n not in visited]

    if not candidates:
        return None

    # Rank by death signals: electron_deaths + agent_deaths
    def _failure(name: str) -> float:
        n = nodes.get(name, {})
        deaths = n.get("electron_deaths", 0) + n.get("agent_deaths", 0)
        hes = n.get("human_hesitation", 0.0)
        return deaths + hes

    candidates.sort(key=_failure, reverse=True)

    # Only follow if there's actual failure signal
    best = candidates[0]
    if _failure(best) <= 0:
        return None

    return best


def _tokenize(text: str) -> set[str]:
    """Extract lowercase word tokens, splitting underscores."""
    import re
    raw = re.findall(r"[a-z_]{3,}", text.lower())
    tokens: set[str] = set()
    for tok in raw:
        tokens.add(tok)
        for part in tok.split("_"):
            if len(part) >= 3:
                tokens.add(part)
    return tokens


def find_origin(
    task_seed: str,
    graph_data: dict[str, Any],
) -> str | None:
    """
    Find the best starting node for a task seed.

    Matches module names and descriptions against the task text.
    """
    task_tokens = _tokenize(task_seed)
    if not task_tokens:
        return None

    nodes = graph_data.get("nodes", {})
    best_name = None
    best_score = 0.0

    for name, node in nodes.items():
        name_tokens = _tokenize(name)
        desc_tokens = _tokenize(node.get("desc", ""))
        all_tokens = name_tokens | desc_tokens
        if not all_tokens:
            continue
        overlap = len(task_tokens & all_tokens)
        score = overlap / max(len(task_tokens), 1)
        if score > best_score:
            best_score = score
            best_name = name

    return best_name if best_score > 0.1 else None
