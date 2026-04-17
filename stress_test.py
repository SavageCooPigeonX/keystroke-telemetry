"""Cognitive stress test — operator state recognition via typing telemetry.

Simulates multiple typing patterns (focused, hesitant, frustrated, discarded)
and prints a live dashboard of cognitive metrics alongside the typing transcript.

Usage:
    python3 stress_test.py
"""

import time
import random
import os
import sys
import importlib.util

# Dynamic imports — pigeon filenames mutate on rename; never hardcode the full name
def _load_src(pattern: str, symbol: str):
    """Load a symbol from the first src/ file matching glob pattern."""
    import glob
    matches = sorted(glob.glob(f'src/{pattern}'))
    if not matches:
        raise ImportError(f'No src/ file matches {pattern!r}')
    spec = importlib.util.spec_from_file_location('_dyn', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, symbol)

TelemetryLogger = _load_src('logger_seq003*.py', 'TelemetryLogger')
HesitationAnalyzer = _load_src('resistance_bridge_seq006*.py', 'HesitationAnalyzer')

# ──────────────── typing scenarios ────────────────

SCENARIOS = [
    {
        "label": "FOCUSED — fast confident typing",
        "text": "The streaming layer handles real-time event processing with low latency",
        "delay_range": (0.03, 0.08),   # fast, consistent
        "typo_rate": 0.02,
        "pause_chance": 0.01,
        "rewrite_chance": 0.0,
        "discard": False,
    },
    {
        "label": "HESITANT — frequent pauses, slow",
        "text": "Maybe the architecture should use a different approach to buffering",
        "delay_range": (0.10, 0.30),   # slow, variable
        "typo_rate": 0.05,
        "pause_chance": 0.15,           # lots of thinking pauses
        "rewrite_chance": 0.0,
        "discard": False,
    },
    {
        "label": "FRUSTRATED — heavy deletion bursts",
        "text": "The connection pool needs refactoring",
        "delay_range": (0.04, 0.12),
        "typo_rate": 0.08,
        "pause_chance": 0.05,
        "rewrite_chance": 0.25,         # frequently rewrites
        "discard": False,
    },
    {
        "label": "DISCARDED — starts then abandons",
        "text": "Actually this whole approach is wrong we should probably",
        "delay_range": (0.06, 0.15),
        "typo_rate": 0.04,
        "pause_chance": 0.10,
        "rewrite_chance": 0.05,
        "discard": True,                # abandoned mid-sentence
    },
    {
        "label": "FLOW STATE — rapid burst of clarity",
        "text": "Stream events into ring buffer, flush on threshold, aggregate per window, emit metrics",
        "delay_range": (0.02, 0.05),   # very fast
        "typo_rate": 0.01,
        "pause_chance": 0.0,
        "rewrite_chance": 0.0,
        "discard": False,
    },
]

# ──────────────── cognitive state classifier ────────────────

def classify_state(wpm, hesitation, deletion_ratio, pause_ratio):
    """Label the operator's cognitive state from live metrics."""
    if hesitation > 0.6 or (deletion_ratio > 0.3 and pause_ratio > 0.3):
        return "FRUSTRATED"
    if pause_ratio > 0.4 or hesitation > 0.4:
        return "HESITANT"
    if wpm > 60 and deletion_ratio < 0.05 and hesitation < 0.15:
        return "FLOW"
    if wpm > 40 and hesitation < 0.25:
        return "FOCUSED"
    if deletion_ratio > 0.20:
        return "RESTRUCTURING"
    return "NEUTRAL"


STATE_COLORS = {
    "FLOW":          "\033[92m",  # bright green
    "FOCUSED":       "\033[32m",  # green
    "NEUTRAL":       "\033[37m",  # white
    "HESITANT":      "\033[33m",  # yellow
    "RESTRUCTURING": "\033[35m",  # magenta
    "FRUSTRATED":    "\033[91m",  # bright red
}
RESET = "\033[0m"

# ──────────────── dashboard rendering ────────────────

DIVIDER = "─" * 72

def render_header():
    print(f"\n{DIVIDER}")
    print("  KEYSTROKE TELEMETRY — COGNITIVE STRESS TEST")
    print(f"{DIVIDER}\n")


def render_scenario_header(idx, total, label):
    print(f"\n{'━' * 72}")
    print(f"  SCENARIO {idx}/{total}: {label}")
    print(f"{'━' * 72}")


def render_stats_panel(stats, state_label):
    """Print a compact stats panel above the transcript."""
    color = STATE_COLORS.get(state_label, "\033[37m")
    print(f"\n  ┌{'─' * 68}┐")
    print(f"  │  WPM: {stats['wpm']:>5.1f}  │  "
          f"Hesitation: {stats['hesitation']:>5.3f}  │  "
          f"Del%: {stats['del_ratio']:>5.1%}  │  "
          f"Pauses: {stats['pauses']:>2d}  │")
    print(f"  │  State: {color}{state_label:^14s}{RESET}"
          f"  │  Keys: {stats['keys']:>4d}  │  "
          f"Buffer: {stats['buf_len']:>3d} chars         │")
    print(f"  └{'─' * 68}┘")


def render_transcript_line(buffer_text, cursor):
    """Show the current buffer with a cursor marker."""
    display = buffer_text[:cursor] + "▌" + buffer_text[cursor:]
    # Truncate for display
    if len(display) > 66:
        display = "…" + display[-(65):]
    print(f"  │ {display:<67s}│", end="\r\n")


# ──────────────── simulation engine ────────────────

def simulate_scenario(logger, scenario):
    """Type out a scenario character by character, computing live stats."""
    text = scenario["text"]
    delay_lo, delay_hi = scenario["delay_range"]
    buffer = ""
    cursor = 0
    keystrokes = 0
    deletions = 0
    inserts = 0
    pauses = 0
    start_ms = time.time() * 1000

    msg_id = logger.start_message()

    for i, ch in enumerate(text):
        # Simulate a thinking pause
        if random.random() < scenario["pause_chance"]:
            pause_sec = random.uniform(2.0, 4.5)
            pauses += 1
            # Show pause state
            elapsed_min = max((time.time() * 1000 - start_ms) / 60_000, 0.001)
            wpm = (inserts / 5) / elapsed_min if inserts else 0
            duration_ms = max(time.time() * 1000 - start_ms, 1)
            pause_time = sum(p["duration_ms"] for p in (logger.current_draft.typing_pauses if logger.current_draft else []))
            pause_ratio = pause_time / duration_ms
            del_ratio = deletions / max(keystrokes, 1)
            hes = min(pause_ratio + del_ratio, 1.0)
            state = classify_state(wpm, hes, del_ratio, pause_ratio)
            render_stats_panel({
                "wpm": wpm, "hesitation": hes, "del_ratio": del_ratio,
                "pauses": pauses, "keys": keystrokes, "buf_len": len(buffer),
            }, f"{state} (pause)")
            render_transcript_line(buffer, cursor)
            time.sleep(pause_sec)

        # Simulate a rewrite burst (delete 3-8 chars then retype differently)
        if buffer and random.random() < scenario["rewrite_chance"]:
            burst = min(random.randint(3, 8), len(buffer))
            for _ in range(burst):
                buffer = buffer[:cursor - 1] + buffer[cursor:]
                cursor = max(cursor - 1, 0)
                keystrokes += 1
                deletions += 1
                logger.log_event("backspace", "Backspace", cursor, buffer)
                time.sleep(random.uniform(0.02, 0.05))

        # Inject occasional typo + correction
        if random.random() < scenario["typo_rate"]:
            wrong_char = random.choice("asdfjkl;qwertyuiop")
            buffer = buffer[:cursor] + wrong_char + buffer[cursor:]
            cursor += 1
            keystrokes += 1
            inserts += 1
            logger.log_event("insert", wrong_char, cursor, buffer)
            time.sleep(random.uniform(0.02, 0.04))
            # immediately correct
            buffer = buffer[:cursor - 1] + buffer[cursor:]
            cursor -= 1
            keystrokes += 1
            deletions += 1
            logger.log_event("backspace", "Backspace", cursor, buffer)
            time.sleep(random.uniform(0.02, 0.04))

        # Type the actual character
        buffer = buffer[:cursor] + ch + buffer[cursor:]
        cursor += 1
        keystrokes += 1
        inserts += 1
        logger.log_event("insert", ch, cursor, buffer)

        # Compute live metrics
        elapsed_min = max((time.time() * 1000 - start_ms) / 60_000, 0.001)
        wpm = (inserts / 5) / elapsed_min
        duration_ms = max(time.time() * 1000 - start_ms, 1)
        pause_time = sum(p["duration_ms"] for p in (logger.current_draft.typing_pauses if logger.current_draft else []))
        pause_ratio = pause_time / duration_ms
        del_ratio = deletions / max(keystrokes, 1)
        hes = min(pause_ratio + del_ratio, 1.0)

        state = classify_state(wpm, hes, del_ratio, pause_ratio)

        # Render every 3 chars to keep output manageable
        if i % 3 == 0 or i == len(text) - 1:
            render_stats_panel({
                "wpm": wpm, "hesitation": hes, "del_ratio": del_ratio,
                "pauses": pauses, "keys": keystrokes, "buf_len": len(buffer),
            }, state)
            render_transcript_line(buffer, cursor)

        time.sleep(random.uniform(delay_lo, delay_hi))

    # Discard or submit
    if scenario["discard"]:
        logger.discard_message(buffer)
        print(f"\n  ✗ MESSAGE DISCARDED")
    else:
        logger.submit_message(buffer)
        print(f"\n  ✓ MESSAGE SUBMITTED: \"{buffer}\"")

    return {
        "keystrokes": keystrokes,
        "inserts": inserts,
        "deletions": deletions,
        "pauses": pauses,
        "final_buffer": buffer,
        "discarded": scenario["discard"],
    }


# ──────────────── main ────────────────

def main():
    os.makedirs("stress_logs", exist_ok=True)
    logger = TelemetryLogger(log_dir="stress_logs", live_print=False)

    render_header()
    print(f"  Session: {logger.session_id}")
    print(f"  Scenarios: {len(SCENARIOS)}")
    print(f"  Log dir: stress_logs/")

    scenario_results = []

    for idx, scenario in enumerate(SCENARIOS, 1):
        render_scenario_header(idx, len(SCENARIOS), scenario["label"])
        result = simulate_scenario(logger, scenario)
        scenario_results.append(result)
        time.sleep(0.5)

    logger.close()

    # ── aggregate operator profile ──
    print(f"\n\n{'═' * 72}")
    print("  OPERATOR COGNITIVE PROFILE — AGGREGATE ANALYSIS")
    print(f"{'═' * 72}")

    analyzer = HesitationAnalyzer(summary_dir="stress_logs")
    profile = analyzer.compute_operator_profile()

    # Classify aggregate state
    agg_state = classify_state(
        profile.get("avg_wpm", 0),
        profile.get("avg_hesitation_score", 0),
        profile.get("deletion_ratio", 0),
        profile.get("pause_frequency", 0) * 0.1,  # normalize
    )
    color = STATE_COLORS.get(agg_state, "\033[37m")

    print(f"""
  Sessions:       {profile.get('total_sessions', 0)}
  Messages:       {profile.get('total_messages', 0)}
  Total keys:     {profile.get('total_keystrokes', 0)}
  Avg WPM:        {profile.get('avg_wpm', 0):.1f}
  Avg hesitation:  {profile.get('avg_hesitation_score', 0):.3f}
  Deletion ratio:  {profile.get('deletion_ratio', 0):.3f}
  Discard rate:    {profile.get('discard_rate', 0):.3f}
  Pause frequency: {profile.get('pause_frequency', 0):.2f}
  Confidence:      {profile.get('profile_confidence', 'none')}

  ┌──────────────────────────────────────────┐
  │  AGGREGATE STATE: {color}{agg_state:^20s}{RESET}  │
  └──────────────────────────────────────────┘""")

    # ── resistance signal ──
    signal = analyzer.resistance_signal()
    print(f"""
  RESISTANCE BRIDGE SIGNAL:
    Adjustment: +{signal['adjustment']:.3f}
    Reason:     {signal['reason']}""")

    # ── per-scenario summary table ──
    print(f"\n  {'─' * 68}")
    print(f"  {'Scenario':<40s} {'Keys':>5s} {'Del%':>6s} {'Pauses':>7s} {'Result':>8s}")
    print(f"  {'─' * 68}")
    for idx, (sc, res) in enumerate(zip(SCENARIOS, scenario_results), 1):
        dr = res['deletions'] / max(res['keystrokes'], 1)
        outcome = "DISCARD" if res['discarded'] else "SUBMIT"
        label = sc['label'].split('—')[0].strip()
        print(f"  {idx}. {label:<37s} {res['keystrokes']:>5d} {dr:>5.1%} {res['pauses']:>7d} {outcome:>8s}")
    print(f"  {'─' * 68}")

    print(f"\n  Logs written to: stress_logs/events_{logger.session_id}.jsonl")
    print(f"  Summary:         stress_logs/summary_{logger.session_id}.json")
    print(f"\n{DIVIDER}\n")


if __name__ == "__main__":
    main()
