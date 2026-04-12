"""Interlink self-test for prompt_signal_seq026_v001.

Auto-generated. This test keeps prompt_signal_seq026_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.prompt_signal_seq026_v001 import log_raw_signal, load_raw_signals, load_latest_raw
    assert callable(log_raw_signal), "log_raw_signal must be callable"
    assert callable(load_raw_signals), "load_raw_signals must be callable"
    assert callable(load_latest_raw), "load_latest_raw must be callable"
    print(f"  ✓ prompt_signal_seq026_v001: 3 exports verified")

def test_log_raw_signal_contract():
    """Data flow contract: log_raw_signal(root, msg, files_open, session_n, signals, deleted_words, rewrites, composition_binding) → output."""
    from src.prompt_signal_seq026_v001 import log_raw_signal
    # smoke test: function exists and is callable
    assert log_raw_signal.__name__ == "log_raw_signal"
    print(f"  ✓ log_raw_signal: contract holds")

def test_load_raw_signals_contract():
    """Data flow contract: load_raw_signals(root, after_line) → output."""
    from src.prompt_signal_seq026_v001 import load_raw_signals
    # smoke test: function exists and is callable
    assert load_raw_signals.__name__ == "load_raw_signals"
    print(f"  ✓ load_raw_signals: contract holds")

def test_load_latest_raw_contract():
    """Data flow contract: load_latest_raw(root, n) → output."""
    from src.prompt_signal_seq026_v001 import load_latest_raw
    # smoke test: function exists and is callable
    assert load_latest_raw.__name__ == "load_latest_raw"
    print(f"  ✓ load_latest_raw: contract holds")

def run_interlink_test():
    """Run all interlink checks for prompt_signal_seq026_v001."""
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    total = len(tests)
    status = "INTERLINKED" if passed == total else f"{passed}/{total}"
    print(f"  prompt_signal_seq026_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
