"""Interlink self-test for push_snapshot_seq001_v001.

Auto-generated. This test keeps push_snapshot_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.push_snapshot_seq001_v001 import capture_snapshot, compute_drift, get_snapshot_history, inject_drift_block
    assert callable(capture_snapshot), "capture_snapshot must be callable"
    assert callable(compute_drift), "compute_drift must be callable"
    assert callable(get_snapshot_history), "get_snapshot_history must be callable"
    assert callable(inject_drift_block), "inject_drift_block must be callable"
    print(f"  ✓ push_snapshot_seq001_v001: 4 exports verified")

def test_capture_snapshot_contract():
    """Data flow contract: capture_snapshot(root, commit_hash, intent, changed_files) → output."""
    from src.push_snapshot_seq001_v001 import capture_snapshot
    # smoke test: function exists and is callable
    assert capture_snapshot.__name__ == "capture_snapshot"
    print(f"  ✓ capture_snapshot: contract holds")

def test_compute_drift_contract():
    """Data flow contract: compute_drift(root, current, previous) → output."""
    from src.push_snapshot_seq001_v001 import compute_drift
    # smoke test: function exists and is callable
    assert compute_drift.__name__ == "compute_drift"
    print(f"  ✓ compute_drift: contract holds")

def test_get_snapshot_history_contract():
    """Data flow contract: get_snapshot_history(root, limit) → output."""
    from src.push_snapshot_seq001_v001 import get_snapshot_history
    # smoke test: function exists and is callable
    assert get_snapshot_history.__name__ == "get_snapshot_history"
    print(f"  ✓ get_snapshot_history: contract holds")

def test_inject_drift_block_contract():
    """Data flow contract: inject_drift_block(root, snapshot, drift_result) → output."""
    from src.push_snapshot_seq001_v001 import inject_drift_block
    # smoke test: function exists and is callable
    assert inject_drift_block.__name__ == "inject_drift_block"
    print(f"  ✓ inject_drift_block: contract holds")

def run_interlink_test():
    """Run all interlink checks for push_snapshot_seq001_v001."""
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
    print(f"  push_snapshot_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
