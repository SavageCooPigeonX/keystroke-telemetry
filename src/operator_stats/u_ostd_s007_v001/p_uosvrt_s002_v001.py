"""u_ostd_s007_v001_render_timeframes_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 47 lines | ~404 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import time as _time

def _render_timeframes(h, n):
    """Build per-timeframe stats table."""
    slots = {}
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
        avg_wpm = sum(r["wpm"] for r in msgs) / cnt
        avg_hes = sum(r["hesitation"] for r in msgs) / cnt
        avg_del = sum(r["del_ratio"] for r in msgs) / cnt
        sub = sum(1 for r in msgs if r["submitted"])
        sc = {}
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
