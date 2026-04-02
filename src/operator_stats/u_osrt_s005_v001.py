"""operator_stats_render_tables_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

def _render_ranges_table(h):
    """Render the Ranges markdown table."""
    n = len(h)
    wpms = [r["wpm"] for r in h]
    del_ratios = [r["del_ratio"] for r in h]
    hes_scores = [r["hesitation"] for r in h]
    pause_totals = [r["pause_ms"] for r in h]

    lines = [
        "## Ranges",
        "",
        "| Metric | Min | Max | Avg |",
        "| --- | ---: | ---: | ---: |",
        f"| WPM | {min(wpms):.0f} | {max(wpms):.0f} | {sum(wpms)/n:.1f} |",
        f"| Deletion % | {min(del_ratios):.1%} | {max(del_ratios):.1%} | {sum(del_ratios)/n:.1%} |",
        f"| Hesitation | {min(hes_scores):.3f} | {max(hes_scores):.3f} | {sum(hes_scores)/n:.3f} |",
        f"| Pause ms | {min(pause_totals)} | {max(pause_totals)} | {sum(pause_totals)//n} |",
        "",
    ]
    return lines


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


def _render_recent_messages(h):
    """Render the Recent Messages table."""
    n = len(h)
    lines = [
        "",
        "## Recent Messages",
        "",
        "| # | State | WPM | Del% | Hes | Submitted |",
        "| ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for i, r in enumerate(h[-12:], max(n - 11, 1)):
        sub = "yes" if r["submitted"] else "no"
        lines.append(
            f"| {i} | {r['state']} | {r['wpm']:.0f} | {r['del_ratio']:.1%} "
            f"| {r['hesitation']:.3f} | {sub} |"
        )
    return lines
