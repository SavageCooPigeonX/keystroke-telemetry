"""Full test — exercises logger, context budget, drift watcher, resistance bridge.
Run from repo root: python test_all.py
"""

import json
import os
import sys
import time

# ensure src is importable
sys.path.insert(0, os.path.dirname(__file__))

import glob as _glob
import importlib.util


def _load_src(pattern: str, *symbols):
    """Load symbol(s) from the first src/ file matching glob pattern."""
    matches = sorted(_glob.glob(f'src/{pattern}'))
    if not matches:
        raise ImportError(f'No src/ file matches {pattern!r}')
    spec = importlib.util.spec_from_file_location('_dyn', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if len(symbols) == 1:
        return getattr(mod, symbols[0])
    return tuple(getattr(mod, s) for s in symbols)


TelemetryLogger = _load_src('*lo_s003*.py', 'TelemetryLogger')
score_context_budget, estimate_tokens = _load_src('*cb_s004*.py', 'score_context_budget', 'estimate_tokens')
DriftWatcher = _load_src('*dw_s005*.py', 'DriftWatcher')
HesitationAnalyzer = _load_src('*rb_s006*.py', 'HesitationAnalyzer')


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

    # logger_seq003 should trigger OVER_HARD_CAP even as pigeon renames versions over time
    over_files = [s["file"] for s in signals if s["verdict"] == "OVER_HARD_CAP"]
    assert any("lo_s003" in name for name in over_files), \
        f"Expected logger to be over hard cap, got: {over_files}"
    print("✓ Drift correctly flags logger (lo_s003) as OVER_HARD_CAP")

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


# ═══════════════ TEST 5: Edit Pairs Pipeline ═══════════════
def test_edit_pairs_pipeline():
    """Stamp pulse blocks on 3 temp files, harvest, verify edit_pairs.jsonl entries."""
    print("=" * 60)
    print("TEST 5: Edit Pairs (pulse stamp → harvest → edit_pairs.jsonl)")
    print("=" * 60)

    import tempfile, shutil
    from pathlib import Path

    stamp_pulse, pair_pulse_to_prompt, read_pulse = _load_src(
        '*ph_s015*.py', 'stamp_pulse', 'pair_pulse_to_prompt', 'read_pulse'
    )

    tmpdir = Path(tempfile.mkdtemp())
    try:
        # Set up minimal repo structure in tmpdir
        (tmpdir / 'logs').mkdir()
        (tmpdir / 'src').mkdir()

        # Write a fake prompt_journal entry
        import json as _json
        from datetime import datetime, timezone
        journal_path = tmpdir / 'logs' / 'prompt_journal.jsonl'
        journal_path.write_text(
            _json.dumps({'ts': datetime.now(timezone.utc).isoformat(),
                         'msg': 'test pressure run',
                         'session_n': 5,
                         'running': {
                             'prompt_density': {
                                 'last_5m': {'count': 3, 'per_hour': 36.0},
                                 'last_15m': {'count': 5, 'per_hour': 20.0},
                                 'last_60m': {'count': 9, 'per_hour': 9.0},
                                 'latest_gap_s': 45.0,
                                 'avg_gap_s': 90.0,
                             },
                         }}) + '\n',
            encoding='utf-8',
        )

        # Create 3 temp .py files with pulse blocks
        PULSE_TEMPLATE = (
            '"""test module"""\n'
            '# ── telemetry:pulse ──\n'
            '# EDIT_TS:   None\n'
            '# EDIT_HASH: None\n'
            '# EDIT_WHY:  None\n'
            '# ── /pulse ──\n'
            'x = 1\n'
        )
        files = []
        for i in range(3):
            fp = tmpdir / 'src' / f'test_module_{i}.py'
            fp.write_text(PULSE_TEMPLATE, encoding='utf-8')
            files.append(fp)

        # Stamp each file
        for i, fp in enumerate(files):
            ok = stamp_pulse(fp, edit_why=f'test edit {i}')
            assert ok, f'stamp_pulse failed for {fp}'
            pulse = read_pulse(fp)
            assert pulse is not None, f'read_pulse returned None for {fp}'
            assert pulse['edit_why'] == f'test edit {i}'
            assert pulse['edit_ts'] != 'None'
            print(f'  ✓ stamped {fp.name}: edit_why={pulse["edit_why"]!r}')

        # Harvest all 3
        harvested = []
        for fp in files:
            record = pair_pulse_to_prompt(tmpdir, fp, cognitive_state='focused')
            assert record is not None, f'pair_pulse_to_prompt returned None for {fp}'
            assert record['edit_why'] != 'None', f'edit_why not populated: {record}'
            assert record['file'].endswith('.py')
            assert record['session_n'] == 5
            assert record['prompt_density']['last_5m']['count'] == 3
            harvested.append(record)
            print(f'  ✓ harvested {fp.name}: latency_ms={record["latency_ms"]}')

        # Verify edit_pairs.jsonl was written with 3 entries
        pairs_path = tmpdir / 'logs' / 'edit_pairs.jsonl'
        assert pairs_path.exists(), 'edit_pairs.jsonl not created'
        lines = [l for l in pairs_path.read_text('utf-8').splitlines() if l.strip()]
        assert len(lines) == 3, f'Expected 3 edit_pairs entries, got {len(lines)}'
        for line in lines:
            entry = _json.loads(line)
            assert entry['edit_why'] not in ('None', None), f'Blank edit_why in stored entry'
        print(f'  ✓ edit_pairs.jsonl has {len(lines)} entries, all with edit_why populated')

        # Verify pulse blocks are cleared after harvest
        for fp in files:
            pulse_after = read_pulse(fp)
            assert pulse_after is None or pulse_after.get('edit_ts') in ('None', None), \
                f'Pulse not cleared after harvest: {fp}'
        print('  ✓ pulse blocks cleared after harvest')

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("✓ TEST 5 PASSED\n")


# ═══════════════ TEST 6: Prompt Density Summary ═══════════════
def test_prompt_density_summary():
    """Running prompt telemetry should expose windowed prompt density."""
    print("=" * 60)
    print("TEST 6: Prompt Density Summary")
    print("=" * 60)

    import tempfile, shutil
    from datetime import datetime, timedelta, timezone
    from pathlib import Path

    running_stats = _load_src('*u_pj_s019*.py', '_running_stats')

    tmpdir = Path(tempfile.mkdtemp())
    try:
        (tmpdir / 'logs').mkdir()
        base = datetime.now(timezone.utc)
        entries = [
            {
                'ts': (base - timedelta(minutes=50)).isoformat(),
                'prompt_kind': 'operator',
                'signals': {'wpm': 30, 'deletion_ratio': 0.1},
                'cognitive_state': 'focused',
            },
            {
                'ts': (base - timedelta(minutes=12)).isoformat(),
                'prompt_kind': 'operator',
                'signals': {'wpm': 35, 'deletion_ratio': 0.2},
                'cognitive_state': 'focused',
            },
            {
                'ts': (base - timedelta(minutes=4)).isoformat(),
                'prompt_kind': 'operator',
                'signals': {'wpm': 40, 'deletion_ratio': 0.15},
                'cognitive_state': 'focused',
            },
            {
                'ts': (base - timedelta(seconds=30)).isoformat(),
                'prompt_kind': 'operator',
                'signals': {'wpm': 45, 'deletion_ratio': 0.05},
                'cognitive_state': 'focused',
            },
        ]

        journal = tmpdir / 'logs' / 'prompt_journal.jsonl'
        with journal.open('w', encoding='utf-8') as f:
            for entry in entries:
                f.write(json.dumps(entry) + '\n')

        stats = running_stats(tmpdir)
        density = stats.get('prompt_density') or {}

        assert stats['total_prompts'] == 4
        assert density['last_5m']['count'] == 2
        assert density['last_15m']['count'] == 3
        assert density['last_60m']['count'] == 4
        assert density['latest_gap_s'] > 0
        print(
            '  ✓ prompt density windows:',
            density['last_5m']['count'],
            density['last_15m']['count'],
            density['last_60m']['count'],
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("✓ TEST 6 PASSED\n")


# ═══════════════ TEST 7: Prompt Enricher Regression ═══════════════
def test_prompt_enricher_unsaid_reconstruction():
    """inject_query_block should persist unsaid reconstructions from deleted words."""
    print("=" * 60)
    print("TEST 7: Prompt Enricher Unsaid Reconstruction")
    print("=" * 60)

    import tempfile, shutil
    from pathlib import Path

    tmpdir = Path(tempfile.mkdtemp())
    try:
        (tmpdir / 'logs').mkdir()
        (tmpdir / '.github').mkdir()

        copilot_path = tmpdir / '.github' / 'copilot-instructions.md'
        copilot_path.write_text(
            '# test prompt\n\n'
            '<!-- pigeon:task-context -->\n'
            '## Live Task Context\n'
            '<!-- /pigeon:task-context -->\n',
            encoding='utf-8',
        )

        matches = sorted(_glob.glob('src/u_pe_s024*.py'))
        assert matches, 'No prompt enricher module found'
        spec = importlib.util.spec_from_file_location('_u_pe_regression', matches[-1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        original_enrich_prompt = mod.enrich_prompt
        try:
            mod.enrich_prompt = lambda *args, **kwargs: '\n'.join([
                'COPILOT_QUERY: debug deletion reconstruction in prompt assembly',
                'INTERPRETED INTENT: ensure deleted words survive prompt enrichment',
                f'KEY FILES: {Path(matches[-1]).name}',
                'PRIOR ATTEMPTS: none',
                'WATCH OUT FOR: losing the unsaid log breaks downstream consumers',
                'OPERATOR SIGNAL: deleted words should remain visible after prompt assembly',
                'UNSAID_RECONSTRUCTION: the operator started with orange before shifting into deletion reconstruction debugging',
            ])

            ok = mod.inject_query_block(
                tmpdir,
                'test deletion reconstruction path',
                deleted_words=[{'word': 'orange'}],
                cognitive_state={'del_ratio': 0.099},
            )
            assert ok, 'inject_query_block should succeed'
        finally:
            mod.enrich_prompt = original_enrich_prompt

        cp_text = copilot_path.read_text('utf-8')
        assert 'UNSAID_RECONSTRUCTION: the operator started with orange before shifting into deletion reconstruction debugging' in cp_text

        recon_path = tmpdir / 'logs' / 'unsaid_reconstructions.jsonl'
        assert recon_path.exists(), 'unsaid reconstruction log should be created'
        entries = [json.loads(line) for line in recon_path.read_text('utf-8').splitlines() if line.strip()]
        assert entries, 'unsaid reconstruction log should contain an entry'
        latest = entries[-1]
        assert latest['deleted_words'] == ['orange']
        assert latest['reconstructed_intent'] == 'the operator started with orange before shifting into deletion reconstruction debugging'
        assert latest['trigger'] == 'enricher'

        print('  ✓ current-query block keeps UNSAID_RECONSTRUCTION')
        print('  ✓ unsaid_reconstructions.jsonl stores normalized deleted_words')
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("✓ TEST 7 PASSED\n")


# ═══════════════ RUN ALL ═══════════════
def main():
    from pathlib import Path
    summary_path = Path(test_logger())
    test_context_budget()
    test_drift_watcher()
    test_resistance_bridge(summary_path)
    test_edit_pairs_pipeline()
    test_prompt_density_summary()
    test_prompt_enricher_unsaid_reconstruction()

    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
