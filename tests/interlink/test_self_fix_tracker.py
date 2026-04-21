"""Interlink self-test for self_fix_tracker_seq001_v001.

Auto-generated. This test keeps self_fix_tracker_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.self_fix_tracker_seq001_v001 import compute_accuracy, build_narrative_block
    assert callable(compute_accuracy), "compute_accuracy must be callable"
    assert callable(build_narrative_block), "build_narrative_block must be callable"
    print(f"  ✓ self_fix_tracker_seq001_v001: 2 exports verified")

def test_compute_accuracy_contract():
    """Data flow contract: compute_accuracy(root) → output."""
    from src.self_fix_tracker_seq001_v001 import compute_accuracy
    # smoke test: function exists and is callable
    assert compute_accuracy.__name__ == "compute_accuracy"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = compute_accuracy(root)
    assert result is not None, "compute_accuracy returned None"
    print(f"  ✓ compute_accuracy: contract holds")

def test_build_narrative_block_contract():
    """Data flow contract: build_narrative_block(root) → output."""
    from src.self_fix_tracker_seq001_v001 import build_narrative_block
    # smoke test: function exists and is callable
    assert build_narrative_block.__name__ == "build_narrative_block"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_narrative_block(root)
    assert result is not None, "build_narrative_block returned None"
    print(f"  ✓ build_narrative_block: contract holds")

def run_interlink_test():
    """Run all interlink checks for self_fix_tracker_seq001_v001."""
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
    print(f"  self_fix_tracker_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
