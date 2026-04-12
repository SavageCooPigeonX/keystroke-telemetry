"""Interlink self-test for tc_buffer_watcher.

Auto-generated. This test keeps tc_buffer_watcher interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.tc_buffer_watcher import BufferWatcher
    assert callable(BufferWatcher), "BufferWatcher must be callable"
    print(f"  ✓ tc_buffer_watcher: 1 exports verified")

def run_interlink_test():
    """Run all interlink checks for tc_buffer_watcher."""
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
    print(f"  tc_buffer_watcher: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
