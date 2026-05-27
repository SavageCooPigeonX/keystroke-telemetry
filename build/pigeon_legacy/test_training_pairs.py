"""Stress test for the training pairs pipeline.

Simulates N edit cycles with synthetic journal entries, edit pairs,
copilot edits, and rework logs — then verifies capture_training_pair
and generate_cycle_summary under realistic and adversarial conditions.

Usage:  py test_training_pairs.py
"""
import json
import random
import shutil
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Bootstrap ──
ROOT = Path(__file__).parent.resolve()
import sys
from src._resolve import src_import

sys.path.insert(0, str(ROOT))
capture_training_pair, generate_cycle_summary = src_import(
    "training_pairs_seq027",
    "capture_training_pair",
    "generate_cycle_summary",
)

INTENTS = ['bugfix', 'refactor', 'exploring', 'feature', 'debug', 'cleanup']
STATES = ['focused', 'hesitant', 'frustrated', 'flow', 'neutral', 'unknown']
EDIT_SOURCES = ['copilot_apply', 'copilot_edit', 'copilot_inline', 'copilot_tab_accept',
                'paste', 'undo', 'human_edit', 'unknown']
MODULES = [
    'src/cognitive_reactor_seq014.py', 'src/self_fix_seq013.py',
    'src/dynamic_prompt_seq017.py', 'src/training_pairs_seq027.py',
    'src/pulse_harvest_seq015.py', 'src/push_cycle_seq025.py',
    'pigeon_compiler/rename_engine/scanner_seq001.py',
    'pigeon_brain/flow/backward_seq007.py',
    'streaming_layer/streaming_layer_orchestrator_seq016.py',
    'src/unified_signal_seq026.py',
]
PROMPTS = [
    'fix the import path in cognitive reactor',
    'refactor the entire learning loop',
    'why is the prediction score so low',
    'add error handling for the deepseek timeout',
    'is that what we should actually be tracking from copilot',
    'push then watch mutation',
    'how do we analyze copilots cognition during processing',
    'clear all test scripts and push again',
    'yes but what im talking about is training data after every edit',
    'can you audit the organism health system',
    'the deletion ratio seems wrong on the last 3 prompts',
    'wire the moon cycle prediction into push narrative',
]
EDIT_WHYS = [
    'fix import path', 'add error handling', 'refactor loop',
    'wire training pairs', 'fix dead formula', 'initial module',
    'add cross-correlation', 'update classifier', 'fix test',
    'bump threshold', 'split oversized function', 'add typing hints',
]


def _synth_journal_entry(session_n: int, ts: datetime) -> dict:
    prompt = random.choice(PROMPTS)
    wpm = random.uniform(15, 120)
    del_ratio = random.uniform(0, 0.6)
    hes = random.randint(0, 8)
    rw = random.randint(0, 5)
    deleted = random.sample(['refactor', 'also', 'mend', 'ideally', 'cont', 'k', 'ta'],
                            k=random.randint(0, 3))
    return {
        'ts': ts.isoformat(),
        'session_n': session_n,
        'session_id': 'stress_test_session',
        'msg': prompt,
        'intent': random.choice(INTENTS),
        'cognitive_state': random.choice(STATES),
        'signals': {
            'wpm': round(wpm, 1),
            'chars_per_sec': round(wpm * 5 / 60, 1),
            'deletion_ratio': round(del_ratio, 3),
            'hesitation_count': hes,
            'rewrite_count': rw,
            'typo_corrections': random.randint(0, 3),
            'intentional_deletions': random.randint(0, 4),
            'total_keystrokes': random.randint(20, 400),
            'duration_ms': random.randint(3000, 120000),
        },
        'deleted_words': deleted,
        'rewrites': [],
        'module_refs': [],
        'source': 'stress_test',
    }


def _synth_edit_pair(session_n: int, ts: datetime, file: str) -> dict:
    return {
        'ts': ts.isoformat(),
        'prompt_ts': (ts - timedelta(seconds=random.randint(5, 300))).isoformat(),
        'prompt_msg': random.choice(PROMPTS)[:200],
        'file': file,
        'edit_ts': ts.isoformat(),
        'edit_why': random.choice(EDIT_WHYS),
        'edit_hash': 'auto',
        'latency_ms': random.randint(500, 90000),
        'state': random.choice(STATES),
        'session_n': session_n,
    }


def _synth_copilot_edit(ts: datetime, file: str) -> dict:
    return {
        'ts': int(ts.timestamp() * 1000),
        'file': file,
        'chars_inserted': random.randint(10, 2000),
        'chars_replaced': random.randint(0, 500),
        'lines_added': random.randint(0, 60),
        'is_multiline': random.random() > 0.3,
        'edit_source': random.choice(EDIT_SOURCES),
        'time_since_ai_response_ms': random.choice([None, random.randint(100, 15000)]),
        'ai_response_len': random.choice([None, random.randint(50, 5000)]),
        'nearby_os_events': random.randint(0, 20),
        'had_physical_keystroke': random.random() > 0.6,
        'source': 'vscode',
        'sid': 'stress_sid',
    }


def _synth_rework(query_hint: str) -> dict:
    return {
        'ts': datetime.now(timezone.utc).isoformat(),
        'verdict': random.choice(['ok', 'rework', 'partial']),
        'rework_score': round(random.uniform(0, 1), 2),
        'del_ratio': round(random.uniform(0, 0.5), 3),
        'wpm': round(random.uniform(20, 80), 1),
        'query_hint': query_hint[:100],
        'response_hint': 'stress test response',
    }


def _synth_ai_response(prompt: str, ts: datetime, file: str, edit_why: str) -> dict:
    file_name = Path(file).name
    return {
        'ts': ts.isoformat(),
        'prompt': prompt,
        'response': f'Completed {edit_why} in {file_name} and verified the touched path still behaves.',
        'response_id': f'test:{file_name}:{int(ts.timestamp())}',
    }


def setup_sandbox(n_edits: int) -> Path:
    """Create a temp directory with synthetic log data."""
    sandbox = Path(tempfile.mkdtemp(prefix='training_stress_'))
    logs = sandbox / 'logs'
    logs.mkdir()

    base_ts = datetime.now(timezone.utc) - timedelta(hours=1)
    rework_entries = []

    for i in range(n_edits):
        ts = base_ts + timedelta(seconds=i * 30)
        session_n = i + 1
        file = random.choice(MODULES)

        # Journal
        j = _synth_journal_entry(session_n, ts)
        with open(logs / 'prompt_journal.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(j) + '\n')

        # Edit pair
        ep = _synth_edit_pair(session_n, ts + timedelta(seconds=random.randint(2, 20)), file)
        with open(logs / 'edit_pairs.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(ep) + '\n')

        # AI response capture for the same prompt cycle
        ai = _synth_ai_response(j['msg'], ts + timedelta(seconds=random.randint(1, 10)), file, ep['edit_why'])
        with open(logs / 'ai_responses.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(ai) + '\n')

        # Copilot edits (0-3 per edit cycle)
        for _ in range(random.randint(0, 3)):
            ce = _synth_copilot_edit(ts + timedelta(seconds=random.randint(1, 15)), file)
            with open(logs / 'copilot_edits.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(ce) + '\n')

        # Rework (50% chance)
        if random.random() > 0.5:
            rework_entries.append(_synth_rework(j['msg']))

    # Write rework log
    with open(sandbox / 'rework_log.json', 'w', encoding='utf-8') as f:
        json.dump(rework_entries, f)

    return sandbox


def test_basic_capture(sandbox: Path, n: int):
    """Test that capture_training_pair produces valid records."""
    print(f'\n{"="*60}')
    print(f'TEST 1: Basic capture ({n} synthetic edits)')
    print(f'{"="*60}')

    pair = capture_training_pair(sandbox)
    assert pair is not None, 'capture_training_pair returned None'
    assert pair['cycle'] == 'per_edit'
    assert 'user_intent' in pair
    assert 'copilot_intent' in pair
    assert 'alignment' in pair
    assert 'completion' in pair
    assert pair['user_intent']['raw_prompt'] != ''
    assert pair['copilot_intent']['edit_why'] != ''
    assert pair['completion']['work_note'] != ''
    assert pair['completion']['response_summary'] != ''
    assert pair['alignment']['response_captured'] is True

    # Verify it wrote to training_pairs.jsonl
    tp_path = sandbox / 'logs' / 'training_pairs.jsonl'
    assert tp_path.exists(), 'training_pairs.jsonl not created'
    lines = tp_path.read_text(encoding='utf-8').strip().split('\n')
    assert len(lines) >= 1
    parsed = json.loads(lines[-1])
    assert parsed['cycle'] == 'per_edit'

    print(f'  ✓ Captured pair: session_n={pair["session_n"]}')
    print(f'  ✓ User intent: {pair["user_intent"]["classified_intent"]}')
    print(f'  ✓ Copilot intent: {pair["copilot_intent"]["edit_why"]}')
    print(f'  ✓ Alignment rework: {pair["alignment"]["rework_score"]}')
    print('✓ TEST 1 PASSED')


def test_rapid_capture(sandbox: Path, count: int):
    """Capture N training pairs in rapid succession — simulate burst edits."""
    print(f'\n{"="*60}')
    print(f'TEST 2: Rapid burst capture ({count} pairs)')
    print(f'{"="*60}')

    tp_path = sandbox / 'logs' / 'training_pairs.jsonl'
    before = len(tp_path.read_text(encoding='utf-8').strip().split('\n')) if tp_path.exists() else 0

    start = time.perf_counter()
    for i in range(count):
        capture_training_pair(sandbox)
    elapsed = time.perf_counter() - start

    after = len(tp_path.read_text(encoding='utf-8').strip().split('\n'))
    captured = after - before
    rate = captured / elapsed if elapsed > 0 else 0

    print(f'  ✓ Captured {captured} pairs in {elapsed:.3f}s ({rate:.0f} pairs/sec)')
    assert captured == count, f'Expected {count} pairs, got {captured}'
    print('✓ TEST 2 PASSED')


def test_cycle_summary(sandbox: Path):
    """Test cycle summary generation."""
    print(f'\n{"="*60}')
    print(f'TEST 3: Cycle summary generation')
    print(f'{"="*60}')

    # Simulate a push cycle result
    mock_cycle = {
        'cycle_number': 42,
        'sync': {'score': 0.73},
        'prediction_score': {'avg_f1': 0.45, 'status': 'scored'},
        'new_predictions': 5,
        'backward_runs': 3,
        'operator_signal': {'prompt_count': 12},
        'copilot_signal': {'py_files_changed': 8},
    }

    summary = generate_cycle_summary(sandbox, cycle=mock_cycle)
    assert summary['cycle'] == 'push_summary'
    assert summary['pair_count'] > 0
    assert 'metrics' in summary
    assert 'intent_distribution' in summary
    assert 'edit_source_distribution' in summary
    assert 'completion_summary' in summary
    assert 'push_cycle' in summary
    assert summary['push_cycle']['cycle_number'] == 42
    assert summary['push_cycle']['sync_score'] == 0.73
    assert summary['metrics']['response_capture_rate'] is not None

    m = summary['metrics']
    print(f'  ✓ Pairs in cycle: {summary["pair_count"]}')
    print(f'  ✓ Avg rework score: {m["avg_rework_score"]}')
    print(f'  ✓ Avg latency: {m["avg_latency_ms"]}ms')
    print(f'  ✓ Physical keystroke rate: {m["physical_keystroke_rate"]}')
    print(f'  ✓ Response capture rate: {m["response_capture_rate"]}')
    print(f'  ✓ Intents: {summary["intent_distribution"]}')
    print(f'  ✓ Edit sources: {summary["edit_source_distribution"]}')
    print(f'  ✓ Completion notes: {summary["completion_summary"]["recent_completion_notes"][:2]}')
    print(f'  ✓ Push cycle merged: #{summary["push_cycle"]["cycle_number"]}')

    # Verify it wrote
    cs_path = sandbox / 'logs' / 'training_cycle_summaries.jsonl'
    assert cs_path.exists()
    print('✓ TEST 3 PASSED')


def test_empty_data():
    """Test graceful handling of missing/empty data."""
    print(f'\n{"="*60}')
    print(f'TEST 4: Empty/missing data graceful handling')
    print(f'{"="*60}')

    empty = Path(tempfile.mkdtemp(prefix='training_empty_'))
    (empty / 'logs').mkdir()

    # No edit_pairs → should return None
    pair = capture_training_pair(empty)
    assert pair is None, f'Expected None, got {pair}'
    print('  ✓ No edit_pairs → returned None')

    # No training pairs → summary should report no_pairs
    summary = generate_cycle_summary(empty)
    assert summary['status'] == 'no_pairs'
    print('  ✓ No training pairs → status=no_pairs')

    # Malformed JSONL
    (empty / 'logs' / 'edit_pairs.jsonl').write_text(
        'not json\n{"broken\n', encoding='utf-8')
    pair = capture_training_pair(empty)
    assert pair is None  # no valid edit pairs
    print('  ✓ Malformed JSONL → handled gracefully')

    # Valid edit pair but no journal
    (empty / 'logs' / 'edit_pairs.jsonl').write_text(
        json.dumps({
            'ts': datetime.now(timezone.utc).isoformat(),
            'prompt_ts': '', 'prompt_msg': 'test', 'file': 'test.py',
            'edit_ts': datetime.now(timezone.utc).isoformat(),
            'edit_why': 'test', 'edit_hash': 'auto',
            'latency_ms': 100, 'state': 'neutral', 'session_n': 1,
        }) + '\n', encoding='utf-8')
    pair = capture_training_pair(empty)
    assert pair is not None
    assert pair['user_intent'] == {}  # no journal → empty user intent
    assert pair['completion']['work_note'] != ''
    print('  ✓ Missing journal → empty user_intent, still captures')

    shutil.rmtree(empty)
    print('✓ TEST 4 PASSED')


def test_malformed_rework():
    """Test rework_log.json edge cases."""
    print(f'\n{"="*60}')
    print(f'TEST 5: Malformed rework_log handling')
    print(f'{"="*60}')

    tmp = Path(tempfile.mkdtemp(prefix='training_rework_'))
    logs = tmp / 'logs'
    logs.mkdir()

    # Write valid edit pair + journal
    ts = datetime.now(timezone.utc)
    (logs / 'edit_pairs.jsonl').write_text(json.dumps({
        'ts': ts.isoformat(), 'prompt_ts': ts.isoformat(),
        'prompt_msg': 'fix the thing', 'file': 'src/test.py',
        'edit_ts': ts.isoformat(), 'edit_why': 'fix it',
        'edit_hash': 'auto', 'latency_ms': 500,
        'state': 'neutral', 'session_n': 1,
    }) + '\n', encoding='utf-8')
    (logs / 'prompt_journal.jsonl').write_text(json.dumps({
        'ts': ts.isoformat(), 'session_n': 1, 'msg': 'fix the thing',
        'intent': 'bugfix', 'cognitive_state': 'focused',
        'signals': {'wpm': 50, 'deletion_ratio': 0.1, 'hesitation_count': 2,
                    'rewrite_count': 0, 'duration_ms': 5000},
        'deleted_words': [],
    }) + '\n', encoding='utf-8')

    # Malformed rework
    (tmp / 'rework_log.json').write_text('not json at all', encoding='utf-8')
    pair = capture_training_pair(tmp)
    assert pair is not None
    assert pair['alignment']['rework_score'] is None
    print('  ✓ Malformed rework_log.json → rework_score=None')

    # Rework is a dict instead of list
    (tmp / 'rework_log.json').write_text('{"single": "object"}', encoding='utf-8')
    pair = capture_training_pair(tmp)
    assert pair is not None
    assert pair['alignment']['rework_score'] is None
    print('  ✓ Dict rework_log → handled, rework_score=None')

    shutil.rmtree(tmp)
    print('✓ TEST 5 PASSED')


def test_high_volume_summary(sandbox: Path):
    """Capture many pairs then generate summary — check aggregation math."""
    print(f'\n{"="*60}')
    print(f'TEST 6: High-volume summary aggregation')
    print(f'{"="*60}')

    # Capture 50 pairs
    for _ in range(50):
        capture_training_pair(sandbox)

    summary = generate_cycle_summary(sandbox)
    assert summary['pair_count'] >= 50
    m = summary['metrics']

    # Sanity checks on aggregated values
    if m['avg_rework_score'] is not None:
        assert 0 <= m['avg_rework_score'] <= 1, f'rework score out of range: {m["avg_rework_score"]}'
    if m['avg_deletion_ratio'] is not None:
        assert 0 <= m['avg_deletion_ratio'] <= 1, f'deletion ratio out of range: {m["avg_deletion_ratio"]}'
    assert 0 <= m['physical_keystroke_rate'] <= 1
    assert 0 <= m['response_capture_rate'] <= 1
    assert sum(summary['intent_distribution'].values()) == summary['pair_count']

    print(f'  ✓ {summary["pair_count"]} pairs aggregated')
    print(f'  ✓ Intent distribution sums to pair_count')
    print(f'  ✓ All metrics in valid ranges')
    print(f'  ✓ Files touched: {len(summary["files_touched"])}')
    print('✓ TEST 6 PASSED')


def test_concurrent_writes(sandbox: Path):
    """Simulate concurrent capture calls (threading)."""
    print(f'\n{"="*60}')
    print(f'TEST 7: Concurrent writes (threaded)')
    print(f'{"="*60}')

    import threading

    tp_path = sandbox / 'logs' / 'training_pairs.jsonl'
    before = len(tp_path.read_text(encoding='utf-8').strip().split('\n')) if tp_path.exists() else 0

    threads = []
    errors = []
    for i in range(20):
        def worker():
            try:
                capture_training_pair(sandbox)
            except Exception as e:
                errors.append(str(e))
        t = threading.Thread(target=worker)
        threads.append(t)

    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    elapsed = time.perf_counter() - start

    after = len(tp_path.read_text(encoding='utf-8').strip().split('\n'))

    assert not errors, f'Thread errors: {errors}'
    print(f'  ✓ 20 concurrent captures in {elapsed:.3f}s')
    print(f'  ✓ {after - before} records written (some may deduplicate)')
    print(f'  ✓ No exceptions raised')

    # Verify ALL lines are valid JSON
    bad = 0
    for line in tp_path.read_text(encoding='utf-8').strip().split('\n'):
        try:
            json.loads(line)
        except json.JSONDecodeError:
            bad += 1
    assert bad == 0, f'{bad} malformed JSON lines after concurrent writes'
    print(f'  ✓ All JSONL lines valid after concurrent writes')
    print('✓ TEST 7 PASSED')


def main():
    print('=' * 60)
    print('TRAINING PAIRS STRESS TEST')
    print('=' * 60)

    N = 100  # synthetic edit cycles
    sandbox = setup_sandbox(N)
    print(f'Sandbox: {sandbox}')
    print(f'Synthetic data: {N} edit cycles')

    try:
        test_basic_capture(sandbox, N)
        test_rapid_capture(sandbox, 50)
        test_cycle_summary(sandbox)
        test_empty_data()
        test_malformed_rework()
        test_high_volume_summary(sandbox)
        test_concurrent_writes(sandbox)

        print(f'\n{"="*60}')
        print('ALL TRAINING PAIR TESTS PASSED ✓')
        print(f'{"="*60}')
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == '__main__':
    main()
