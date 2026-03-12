"""Full test — exercises logger, context budget, drift watcher, resistance bridge.
Run from repo root: py test_all.py
"""

import json
import time
import sys
import os

# ensure src is importable
sys.path.insert(0, os.path.dirname(__file__))

from src.logger_seq003_v001 import TelemetryLogger
from src.context_budget_seq004_v001 import score_context_budget, estimate_tokens
from src.drift_watcher_seq005_v001 import DriftWatcher
from src.resistance_bridge_seq006_v001 import HesitationAnalyzer


# ─────────────── helpers ───────────────
def sim_type(logger, text, buf="", wpm=80):
    delay = 60.0 / (wpm * 5)
    for ch in text:
        buf += ch
        logger.log_event("insert", ch, len(buf), buf)
        time.sleep(delay)
    return buf

def sim_backspace(logger, buf, count=1):
    for _ in range(count):
        if buf:
            removed = buf[-1]
            buf = buf[:-1]
            logger.log_event("backspace", removed, len(buf), buf)
            time.sleep(0.04)
    return buf


# ═══════════════ TEST 1: Telemetry Logger ═══════════════
def test_logger():
    print("=" * 60)
    print("TEST 1: Telemetry Logger (v2 schema)")
    print("=" * 60)

    log = TelemetryLogger(log_dir="test_logs", live_print=True)
    print(f"Session {log.session_id}\n")

    # Turn 1: typo + correction
    print("── Turn 1: typo → correct → submit ──")
    log.start_message()
    buf = sim_type(log, "Helo wrld")
    buf = sim_backspace(log, buf, 4)
    buf = sim_type(log, "world!", buf)
    log.submit_message(buf)
    print(f"\n>>> SUBMITTED: \"{buf}\"\n")

    time.sleep(0.2)

    # Turn 2: type → pause → discard
    print("── Turn 2: type → pause → discard ──")
    log.start_message()
    buf = sim_type(log, "Actually nvm")
    print("  (pause 2.1s)")
    time.sleep(2.1)
    log.log_event("clear", "Ctrl+A+Del", 0, "")
    log.discard_message(buf)
    print(f"\n>>> DISCARDED: \"{buf}\"\n")

    time.sleep(0.2)

    # Turn 3: paste → edit
    print("── Turn 3: paste → edit → submit ──")
    log.start_message()
    pasted = "What is the meaning of life?"
    log.log_event("paste", pasted, len(pasted), pasted)
    buf = pasted
    buf = sim_backspace(log, buf, 5)
    buf = sim_type(log, "42?", buf)
    log.submit_message(buf)
    print(f"\n>>> SUBMITTED: \"{buf}\"\n")

    log.close()

    # ── Validate ──
    with open(log.events_file, encoding="utf-8") as f:
        events = [json.loads(line) for line in f]

    print(f"Total event blocks: {len(events)}")

    required_keys = {"schema", "seq", "session_id", "message_id",
                     "timestamp_ms", "delta_ms", "event_type",
                     "key", "cursor_pos", "buffer", "buffer_len"}
    for i, e in enumerate(events):
        missing = required_keys - set(e.keys())
        assert not missing, f"Event {i} missing keys: {missing}"
        assert e["schema"] == "keystroke_telemetry/v2"
    print("✓ All blocks match v2 schema")

    ts_list = [e["timestamp_ms"] for e in events]
    assert all(isinstance(t, int) for t in ts_list)
    assert all(t > 1_700_000_000_000 for t in ts_list)
    assert ts_list == sorted(ts_list)
    print("✓ Timestamps: ms-epoch, monotonic")

    seqs = [e["seq"] for e in events]
    assert seqs == list(range(1, len(events) + 1))
    print("✓ Sequence: 1..N")

    with open(log.summary_file, encoding="utf-8") as f:
        summary = json.load(f)
    msgs = summary["messages"]
    assert len(msgs) == 3
    assert msgs[0]["submitted"] and not msgs[0]["deleted"]
    assert not msgs[1]["submitted"] and msgs[1]["deleted"]
    assert msgs[2]["submitted"] and not msgs[2]["deleted"]
    assert len(msgs[1]["typing_pauses"]) >= 1
    # v2: hesitation_score
    for m in msgs:
        assert "hesitation_score" in m, "v2 must include hesitation_score"
        assert 0 <= m["hesitation_score"] <= 1.0
    print("✓ Summary: 3 drafts, hesitation scores present")

    for m in msgs:
        status = "SUBMITTED" if m["submitted"] else "DISCARDED"
        print(f"  [{status}] keys={m['total_keystrokes']} dels={m['total_deletions']} "
              f"hesitation={m['hesitation_score']} "
              f"duration={m['end_time_ms'] - m['start_time_ms']}ms")

    print("✓ TEST 1 PASSED\n")
    return log.summary_file


# ═══════════════ TEST 2: Context Budget ═══════════════
def test_context_budget():
    print("=" * 60)
    print("TEST 2: Context Budget Scorer")
    print("=" * 60)

    # Self-contained 80-line file → OK
    r = score_context_budget(80, [])
    assert r["verdict"] == "OK", f"Expected OK, got {r['verdict']}"
    print(f"  80-line, 0 deps → {r['verdict']}  ({r['total_tokens']} tokens)")

    # 90-line file → OVER_HARD_CAP
    r = score_context_budget(90, [])
    assert r["verdict"] == "OVER_HARD_CAP"
    print(f"  90-line, 0 deps → {r['verdict']}")

    # 70-line file with heavy deps → could blow budget
    r = score_context_budget(70, [60, 50, 40], coupling_score=0.8)
    print(f"  70-line, 3 deps (coupling=0.8) → {r['verdict']}  ({r['total_tokens']} tokens)")

    # 40-line with minimal deps → OK
    r = score_context_budget(40, [20], coupling_score=0.1)
    assert r["verdict"] == "OK"
    print(f"  40-line, 1 dep (coupling=0.1) → {r['verdict']}  ({r['total_tokens']} tokens)")

    print("✓ TEST 2 PASSED\n")


# ═══════════════ TEST 3: Drift Watcher ═══════════════
def test_drift_watcher():
    print("=" * 60)
    print("TEST 3: Drift Watcher")
    print("=" * 60)

    # Watch our own src/ directory
    watcher = DriftWatcher("src", coupling_score=0.3)
    watcher.snapshot()
    signals = watcher.check_and_print()

    # logger_seq003 at ~130 lines should trigger OVER_HARD_CAP
    over_files = [s["file"] for s in signals if s["verdict"] == "OVER_HARD_CAP"]
    assert "logger_seq003_v001.py" in over_files, \
        f"Expected logger to be over hard cap, got: {over_files}"
    print("✓ Drift correctly flags logger_seq003 as OVER_HARD_CAP")

    print("✓ TEST 3 PASSED\n")


# ═══════════════ TEST 4: Resistance Bridge ═══════════════
def test_resistance_bridge(summary_path: str):
    print("=" * 60)
    print("TEST 4: Resistance Bridge (telemetry → compiler signal)")
    print("=" * 60)

    analyzer = HesitationAnalyzer(summary_dir=str(summary_path.parent))
    profile = analyzer.compute_operator_profile()
    print(f"  Profile: {json.dumps(profile, indent=2)}")

    assert profile["total_sessions"] >= 1
    assert profile["total_messages"] >= 3
    assert profile["avg_wpm"] > 0
    print(f"  avg_wpm={profile['avg_wpm']}")
    print(f"  avg_hesitation={profile['avg_hesitation_score']}")
    print(f"  discard_rate={profile['discard_rate']}")
    print(f"  confidence={profile['profile_confidence']}")

    signal = analyzer.resistance_signal()
    print(f"\n  Resistance signal: adjustment={signal['adjustment']}, reason={signal['reason']}")

    assert "adjustment" in signal
    assert 0 <= signal["adjustment"] <= 0.3

    print("✓ TEST 4 PASSED\n")


# ═══════════════ RUN ALL ═══════════════
def main():
    from pathlib import Path
    summary_path = Path(test_logger())
    test_context_budget()
    test_drift_watcher()
    test_resistance_bridge(summary_path)

    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
