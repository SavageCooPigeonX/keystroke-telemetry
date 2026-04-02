"""operator_stats_render_recent_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

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
