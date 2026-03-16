"""operator_stats_render_distribution_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

def _render_state_distribution(h):
    """Render the State Distribution section."""
    n = len(h)
    state_counts = {}
    for r in h:
        state_counts[r["state"]] = state_counts.get(r["state"], 0) + 1

    submitted = sum(1 for r in h if r["submitted"])
    discarded = n - submitted
    dominant = max(state_counts, key=state_counts.get) if state_counts else "unknown"

    lines = [
        "## State Distribution",
        "",
        "| State | Count | % |",
        "| --- | ---: | ---: |",
    ]
    for state in ("flow", "focused", "neutral", "hesitant", "restructuring", "frustrated", "abandoned"):
        c = state_counts.get(state, 0)
        if c:
            lines.append(f"| {state} | {c} | {c*100//n}% |")

    lines += [
        "",
        f"**Dominant state: {dominant}**",
        f"**Submit rate: {submitted}/{n} ({submitted*100//n}%)**",
    ]
    return lines
