"""node_memory_seq008_directive_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

def _synthesize_directive(
    node: str,
    score: float,
    top_patterns: list[str],
    fail_patterns: list[str],
) -> str:
    """Generate a one-line behavioral instruction from patterns."""
    parts = []
    if score > 0.7:
        parts.append(f"{node}: high performer")
    elif score < 0.3:
        parts.append(f"{node}: struggling")
    else:
        parts.append(f"{node}: moderate")

    if top_patterns:
        parts.append(f"focus on: {top_patterns[0][:60]}")
    if fail_patterns:
        parts.append(f"avoid: {fail_patterns[0][:60]}")

    return "; ".join(parts)
