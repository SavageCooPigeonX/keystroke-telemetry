# @pigeon: seq=008 | role=operator_stats | depends=[models,logger] | exports=[OperatorStats] | tokens=~600
"""Self-growing operator stats — persistent markdown memory file.

Classifies each finalized message with a cognitive state label,
accumulates ranges (min–max) across all messages, and silently
rewrites a markdown stats file every N finalized messages.

Designed for LLM consumption: an agent reading the .md file gets
a compact operator profile that sharpens with every message.
"""

import json
import time as _time
from pathlib import Path
from datetime import datetime, timezone, timedelta


# ── time-of-day slots ──

TIME_SLOTS = {
    "night":   (0, 6),    # 00:00–05:59
    "morning": (6, 12),   # 06:00–11:59
    "afternoon": (12, 18), # 12:00–17:59
    "evening": (18, 24),  # 18:00–23:59
}

def _hour_to_slot(hour: int) -> str:
    for name, (lo, hi) in TIME_SLOTS.items():
        if lo <= hour < hi:
            return name
    return "night"

def _local_hour_now() -> int:
    """Current local hour (0–23), no pytz needed."""
    return datetime.now().hour


def classify_state(msg: dict) -> str:
    """Classify a finalized message dict into a cognitive state label."""
    keys = max(msg.get("total_keystrokes", 0), 1)
    inserts = msg.get("total_inserts", 0)
    dels = msg.get("total_deletions", 0)
    pauses = msg.get("typing_pauses", [])
    duration_ms = max(msg.get("end_time_ms", 0) - msg.get("start_time_ms", 0), 1)
    hes = msg.get("hesitation_score", 0)

    del_ratio = dels / keys
    wpm = (inserts / 5) / max(duration_ms / 60_000, 0.001)
    pause_ratio = sum(p.get("duration_ms", 0) for p in pauses) / duration_ms

    if msg.get("deleted"):
        return "abandoned"
    if hes > 0.6 or (del_ratio > 0.3 and pause_ratio > 0.3):
        return "frustrated"
    if pause_ratio > 0.4 or hes > 0.4:
        return "hesitant"
    if wpm > 60 and del_ratio < 0.05 and hes < 0.15:
        return "flow"
    if wpm > 40 and hes < 0.25:
        return "focused"
    if del_ratio > 0.20:
        return "restructuring"
    return "neutral"


class OperatorStats:
    """Accumulates operator cognitive stats and writes a markdown memory file.

    Usage:
        stats = OperatorStats("operator_profile.md")
        # called automatically by logger every finalize:
        stats.ingest(message_dict)
        # ^^ silently writes .md every `write_every` messages
    """

    def __init__(self, stats_path: str = "operator_profile.md", write_every: int = 8):
        self.stats_path = Path(stats_path)
        self.write_every = write_every
        self._msg_count = 0
        self._history: list[dict] = []  # compact per-message records
        self._load_existing()

    def _load_existing(self):
        """Bootstrap from existing stats file if present (read the JSON block)."""
        if not self.stats_path.exists():
            return
        text = self.stats_path.read_text(encoding="utf-8")
        # look for the embedded JSON data block
        start = text.find("<!-- DATA")
        end = text.find("DATA -->")
        if start == -1 or end == -1:
            return
        json_str = text[start + len("<!-- DATA"):end].strip()
        try:
            data = json.loads(json_str)
            self._history = data.get("history", [])
            self._msg_count = len(self._history)
        except (json.JSONDecodeError, TypeError):
            pass

    def ingest(self, msg: dict):
        """Ingest a finalized message dict. Writes .md every write_every messages."""
        state = classify_state(msg)
        keys = max(msg.get("total_keystrokes", 0), 1)
        inserts = msg.get("total_inserts", 0)
        dels = msg.get("total_deletions", 0)
        duration_ms = max(msg.get("end_time_ms", 0) - msg.get("start_time_ms", 0), 1)
        pauses = msg.get("typing_pauses", [])

        wpm = round((inserts / 5) / max(duration_ms / 60_000, 0.001), 1)
        del_ratio = round(dels / keys, 3)
        pause_time_ms = sum(p.get("duration_ms", 0) for p in pauses)
        hes = msg.get("hesitation_score", 0)

        local_hour = _local_hour_now()
        record = {
            "state": state,
            "wpm": wpm,
            "del_ratio": del_ratio,
            "hesitation": hes,
            "pause_ms": pause_time_ms,
            "keys": msg.get("total_keystrokes", 0),
            "submitted": msg.get("submitted", False),
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "local_hour": local_hour,
            "slot": _hour_to_slot(local_hour),
        }
        self._history.append(record)
        self._msg_count += 1

        if self._msg_count % self.write_every == 0:
            self.flush()

    def flush(self):
        """Force-write the markdown stats file now."""
        if not self._history:
            return
        self.stats_path.write_text(self._render(), encoding="utf-8")

    def _render(self) -> str:
        """Render the full markdown stats file from accumulated history."""
        h = self._history
        n = len(h)

        # compute ranges
        wpms = [r["wpm"] for r in h]
        del_ratios = [r["del_ratio"] for r in h]
        hes_scores = [r["hesitation"] for r in h]
        pause_totals = [r["pause_ms"] for r in h]

        # state distribution
        state_counts: dict[str, int] = {}
        for r in h:
            state_counts[r["state"]] = state_counts.get(r["state"], 0) + 1

        submitted = sum(1 for r in h if r["submitted"])
        discarded = n - submitted

        # dominant state
        dominant = max(state_counts, key=state_counts.get) if state_counts else "unknown"

        lines = [
            "# Operator Cognitive Profile",
            "",
            f"*Auto-updated every {self.write_every} messages · {n} messages ingested*",
            f"*Last update: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "## Ranges",
            "",
            "| Metric | Min | Max | Avg |",
            "| --- | ---: | ---: | ---: |",
            f"| WPM | {min(wpms):.0f} | {max(wpms):.0f} | {sum(wpms)/n:.1f} |",
            f"| Deletion % | {min(del_ratios):.1%} | {max(del_ratios):.1%} | {sum(del_ratios)/n:.1%} |",
            f"| Hesitation | {min(hes_scores):.3f} | {max(hes_scores):.3f} | {sum(hes_scores)/n:.3f} |",
            f"| Pause ms | {min(pause_totals)} | {max(pause_totals)} | {sum(pause_totals)//n} |",
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

        # ── timeframe analysis ──
        lines += self._render_timeframes(h, n)

        # ── pattern observations (natural language for LLM) ──
        lines += self._render_observations(h)

        lines += [
            "",
            "## Recent Messages",
            "",
            "| # | State | WPM | Del% | Hes | Submitted |",
            "| ---: | --- | ---: | ---: | ---: | --- |",
        ]
        # show last 12 messages
        for i, r in enumerate(h[-12:], max(n - 11, 1)):
            sub = "yes" if r["submitted"] else "no"
            lines.append(
                f"| {i} | {r['state']} | {r['wpm']:.0f} | {r['del_ratio']:.1%} "
                f"| {r['hesitation']:.3f} | {sub} |"
            )

        # embed raw data as hidden JSON for self-bootstrap
        lines += [
            "",
            "<!--",
            "DATA",
            json.dumps({"history": h}, separators=(",", ":")),
            "DATA",
            "-->",
        ]

        return "\n".join(lines) + "\n"
    # ── timeframe rendering ──

    def _render_timeframes(self, h: list[dict], n: int) -> list[str]:
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
            avg_wpm = sum(r["wpm"] for r in msgs) / cnt
            avg_hes = sum(r["hesitation"] for r in msgs) / cnt
            avg_del = sum(r["del_ratio"] for r in msgs) / cnt
            sub = sum(1 for r in msgs if r["submitted"])
            # dominant state for this slot
            sc: dict[str, int] = {}
            for r in msgs:
                sc[r["state"]] = sc.get(r["state"], 0) + 1
            dom = max(sc, key=sc.get)
            lines.append(
                f"| {slot_name} | {cnt} | {avg_wpm:.0f} | {avg_hes:.3f} "
                f"| {avg_del:.1%} | {dom} | {sub*100//cnt}% |"
            )

        # hour heatmap — compact one-liner
        hour_counts = [0] * 24
        for r in h:
            hour_counts[r.get("local_hour", 12)] += 1
        active_hours = [f"{hr}:00({c})" for hr, c in enumerate(hour_counts) if c]
        if active_hours:
            lines += ["", f"**Active hours:** {', '.join(active_hours)}"]

        return lines

    # ── pattern observations ──

    def _render_observations(self, h: list[dict]) -> list[str]:
        """Derive natural-language patterns from timestamp + state data."""
        if len(h) < 4:
            return []

        lines = ["", "## Patterns (LLM-readable)"]
        obs = []

        # group by slot
        slots: dict[str, list[dict]] = {}
        for r in h:
            s = r.get("slot", "afternoon")
            slots.setdefault(s, []).append(r)

        # compare WPM across timeframes
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

        # hesitation by timeframe
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

        # discard rate by slot
        for s, msgs in slots.items():
            if len(msgs) >= 3:
                disc = sum(1 for r in msgs if not r["submitted"])
                rate = disc / len(msgs)
                if rate > 0.3:
                    obs.append(
                        f"High discard rate in the **{s}** "
                        f"({disc}/{len(msgs)} = {rate:.0%} abandoned)."
                    )

        # streak detection: consecutive frustrated/hesitant
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

        # morning warmup detection
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

        # late night degradation
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