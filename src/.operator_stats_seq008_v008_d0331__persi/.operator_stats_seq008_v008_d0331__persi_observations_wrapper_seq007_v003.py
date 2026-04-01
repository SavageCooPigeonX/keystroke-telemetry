""".operator_stats_seq008_v008_d0331__persi_observations_wrapper_seq007_v003.py — Auto-extracted by Pigeon Compiler."""
import re

def _render_observations(h: list[dict]) -> list[str]:
    """Derive natural-language patterns from timestamp + state data."""
    if len(h) < 4:
        return []

    lines = ["", "## Patterns (LLM-readable)"]
    obs = []

    slots: dict[str, list[dict]] = {}
    for r in h:
        s = r.get("slot", "afternoon")
        slots.setdefault(s, []).append(r)

    slot_wpm: dict[str, float] = {}
    for s, msgs in slots.items():
        if len(msgs) >= 2:
            slot_wpm[s] = sum(r["wpm"] for r in msgs) / len(msgs)

    if len(slot_wpm) >= 2:
        fastest = max(slot_wpm, key=slot_wpm.get)
        slowest = min(slot_wpm, key=slot_wpm.get)
        if slot_wpm[fastest] > slot_wpm[slowest] * 1.3:
            obs.append(
                f"Operator types fastest in the **{fastest}** "
                f"(avg {slot_wpm[fastest]:.0f} WPM) "
                f"and slowest in the **{slowest}** "
                f"(avg {slot_wpm[slowest]:.0f} WPM)."
            )

    slot_hes: dict[str, float] = {}
    for s, msgs in slots.items():
        if len(msgs) >= 2:
            slot_hes[s] = sum(r["hesitation"] for r in msgs) / len(msgs)

    if len(slot_hes) >= 2:
        most_hes = max(slot_hes, key=slot_hes.get)
        least_hes = min(slot_hes, key=slot_hes.get)
        if slot_hes[most_hes] > slot_hes[least_hes] + 0.15:
            obs.append(
                f"Most hesitant in the **{most_hes}** "
                f"(avg {slot_hes[most_hes]:.3f}). "
                f"Most decisive in the **{least_hes}** "
                f"(avg {slot_hes[least_hes]:.3f})."
            )

    for s, msgs in slots.items():
        if len(msgs) >= 3:
            disc = sum(1 for r in msgs if not r["submitted"])
            rate = disc / len(msgs)
            if rate > 0.3:
                obs.append(
                    f"High discard rate in the **{s}** "
                    f"({disc}/{len(msgs)} = {rate:.0%} abandoned)."
                )

    streak = 0
    max_streak = 0
    streak_slot = ""
    for r in h:
        if r["state"] in ("frustrated", "hesitant", "abandoned"):
            streak += 1
            if streak > max_streak:
                max_streak = streak
                streak_slot = r.get("slot", "")
        else:
            streak = 0
    if max_streak >= 3:
        obs.append(
            f"Longest struggle streak: **{max_streak} messages** "
            f"in a row ({streak_slot}). Consider a break."
        )

    morning = slots.get("morning", [])
    if len(morning) >= 3:
        first_half = morning[:len(morning)//2]
        second_half = morning[len(morning)//2:]
        avg_first = sum(r["wpm"] for r in first_half) / len(first_half)
        avg_second = sum(r["wpm"] for r in second_half) / len(second_half)
        if avg_second > avg_first * 1.4:
            obs.append(
                "Morning warmup detected — early morning messages are "
                f"~{avg_second/max(avg_first,1):.1f}x slower than later morning. "
                "Coffee effect?"
            )

    night = slots.get("night", [])
    evening = slots.get("evening", [])
    if len(night) >= 2 and len(evening) >= 2:
        night_hes = sum(r["hesitation"] for r in night) / len(night)
        eve_hes = sum(r["hesitation"] for r in evening) / len(evening)
        if night_hes > eve_hes + 0.15:
            obs.append(
                f"Late-night degradation: hesitation jumps from "
                f"{eve_hes:.3f} (evening) to {night_hes:.3f} (night). "
                "Operator may be fatigued."
            )

    if not obs:
        obs.append("Not enough data across timeframes yet — keep typing.")

    for o in obs:
        lines.append(f"- {o}")

    return lines
