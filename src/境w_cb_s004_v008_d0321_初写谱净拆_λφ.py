"""Context budget scorer for LLM-aware file sizing.

Instead of a flat line-count cap, scores files by how many tokens an LLM
needs to understand them (source tokens + dependency context tokens).
Pigeon compiler integration: feed this score into resistance analysis.
"""


import math

# Approximate token-per-line ratio for Python (empirical: ~7 tokens/line avg)
TOKENS_PER_LINE = 7.0

# Default budget thresholds
DEFAULT_CONFIG = {
    "hard_cap_lines": 88,           # absolute max lines per file
    "context_budget_tokens": 3000,  # max tokens = file + weighted deps
    "coupling_weight": 0.6,         # how much coupling inflates dep cost
    "self_contained_bonus": 0.8,    # multiplier if zero project imports
}


def default_budget_config() -> dict:
    return dict(DEFAULT_CONFIG)


def estimate_tokens(line_count: int) -> int:
    return int(math.ceil(line_count * TOKENS_PER_LINE))


def score_context_budget(
    file_lines: int,
    dependency_lines: list[int],
    coupling_score: float = 0.0,
    config: dict = None,
) -> dict:
    """Score a file's LLM context cost.

    Args:
        file_lines: line count of the target file
        dependency_lines: line counts of files this file imports from (project-internal only)
        coupling_score: 0.0-1.0 from Ether Map
        config: override DEFAULT_CONFIG

    Returns:
        {file_tokens, dep_tokens, total_tokens, budget, over_budget, verdict}
    """
    cfg = config or DEFAULT_CONFIG

    file_tokens = estimate_tokens(file_lines)
    dep_tokens = sum(
        int(estimate_tokens(dl) * (cfg["coupling_weight"] * coupling_score + 0.2))
        for dl in dependency_lines
    )

    if not dependency_lines:
        file_tokens = int(file_tokens * cfg["self_contained_bonus"])

    total = file_tokens + dep_tokens
    budget = cfg["context_budget_tokens"]
    over = total > budget

    if file_lines > cfg["hard_cap_lines"]:
        verdict = "OVER_HARD_CAP"
    elif over:
        verdict = "OVER_BUDGET"
    elif total > budget * 0.8:
        verdict = "WARN"
    else:
        verdict = "OK"

    return {
        "file_lines": file_lines,
        "file_tokens": file_tokens,
        "dep_tokens": dep_tokens,
        "total_tokens": total,
        "budget": budget,
        "over_budget": over,
        "verdict": verdict,
    }


