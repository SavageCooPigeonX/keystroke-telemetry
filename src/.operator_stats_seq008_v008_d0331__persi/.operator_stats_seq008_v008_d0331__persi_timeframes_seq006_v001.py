""".operator_stats_seq008_v008_d0331__persi_timeframes_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
import re
import time as _time

def _render_timeframes(h: list[dict], n: int) -> list[str]:
    """Build per-timeframe stats table."""
    slots: dict[str, list[dict]] = {}
    for r in h:
        s = r.get("slot", _hour_to_slot(r.get("local_hour", 12)))
        slots.setdefault(s, []).append(r)

    if not slots:
        return []

    lines = [
        "",
        "## Time-of-Day Profile",
        "",
        "| Timeframe | Msgs | Avg WPM | Avg Hes | Del% | Dominant | Submit% |",
        "| --- | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for slot_name in ("morning", "afternoon", "evening", "night"):
        msgs = slots.get(slot_name, [])
        if not msgs:
            lines.append(f"| {slot_name} | 0 | — | — | — | — | — |")
            continue
        cnt = len(msgs)
        human_wpm = [r["wpm"] for r in msgs if r.get("wpm", 0) <= WPM_HUMAN_MAX] or [0]
        avg_wpm = sum(human_wpm) / len(human_wpm)
        avg_hes = sum(r["hesitation"] for r in msgs) / cnt
        avg_del = sum(r["del_ratio"] for r in msgs) / cnt
        sub = sum(1 for r in msgs if r["submitted"])
        sc: dict[str, int] = {}
        for r in msgs:
            sc[r["state"]] = sc.get(r["state"], 0) + 1
        dom = max(sc, key=sc.get)
        lines.append(
            f"| {slot_name} | {cnt} | {avg_wpm:.0f} | {avg_hes:.3f} "
            f"| {avg_del:.1%} | {dom} | {sub*100//cnt}% |"
        )

    hour_counts = [0] * 24
    for r in h:
        hour_counts[r.get("local_hour", 12)] += 1
    active_hours = [f"{hr}:00({c})" for hr, c in enumerate(hour_counts) if c]
    if active_hours:
        lines += ["", f"**Active hours:** {', '.join(active_hours)}"]

    return lines
