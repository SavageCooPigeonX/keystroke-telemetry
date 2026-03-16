"""operator_stats_render_ranges_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

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
