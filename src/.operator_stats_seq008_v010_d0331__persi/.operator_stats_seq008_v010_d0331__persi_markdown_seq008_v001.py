""".operator_stats_seq008_v010_d0331__persi_markdown_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone, timedelta
import json
import re
import time as _time

def _render_markdown(history: list[dict], write_every: int) -> str:
    """Render the full markdown stats file from accumulated history."""
    h = history
    n = len(h)

    human = [r for r in h if r.get("wpm", 0) <= WPM_HUMAN_MAX]
    wpms = [r["wpm"] for r in human] or [0]
    del_ratios = [r["del_ratio"] for r in h]
    hes_scores = [r["hesitation"] for r in h]
    pause_totals = [r["pause_ms"] for r in h]

    baselines = compute_baselines(h)

    state_counts: dict[str, int] = {}
    for r in h:
        state_counts[r["state"]] = state_counts.get(r["state"], 0) + 1

    submitted = sum(1 for r in h if r["submitted"])
    discarded = n - submitted

    dominant = max(state_counts, key=state_counts.get) if state_counts else "unknown"

    lines = [
        "# Operator Cognitive Profile",
        "",
        f"*Auto-updated every {write_every} messages · {n} messages ingested*",
        f"*Last update: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Ranges",
        "",
        "| Metric | Min | Max | Avg |",
        "| --- | ---: | ---: | ---: |",
        f"| WPM | {min(wpms):.0f} | {max(wpms):.0f} | {sum(wpms)/max(len(wpms),1):.1f} |",
        f"| Deletion % | {min(del_ratios):.1%} | {max(del_ratios):.1%} | {sum(del_ratios)/n:.1%} |",
        f"| Hesitation | {min(hes_scores):.3f} | {max(hes_scores):.3f} | {sum(hes_scores)/n:.3f} |",
        f"| Pause ms | {min(pause_totals)} | {max(pause_totals)} | {sum(pause_totals)//n} |",
    ]

    if baselines:
        lines += [
            "",
            "## Self-Calibration Baselines (rolling 50)",
            "",
            f"*Computed from last {baselines['n']} submitted messages. "
            "Classification thresholds adapt to these norms.*",
            "",
            "| Metric | Baseline | ±1 SD |",
            "| --- | ---: | ---: |",
            f"| WPM | {baselines['avg_wpm']:.1f} | ±{baselines['sd_wpm']:.1f} |",
            f"| Deletion % | {baselines['avg_del']:.1%} | ±{baselines['sd_del']:.1%} |",
            f"| Hesitation | {baselines['avg_hes']:.3f} | ±{baselines['sd_hes']:.3f} |",
        ]
    else:
        lines += [
            "",
            "## Self-Calibration",
            "",
            "*Not enough data yet (need 5+ submitted messages). Using default thresholds.*",
        ]

    lines += [
        "",
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

    lines += _render_timeframes(h, n)
    lines += _render_observations(h)

    lines += [
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

    lines += [
        "",
        "<!--",
        "DATA",
        json.dumps({"history": h, "baselines": baselines}, separators=(",", ":")),
        "DATA",
        "-->",
    ]

    return "\n".join(lines) + "\n"
