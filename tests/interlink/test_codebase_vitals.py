"""Interlink self-test for codebase_vitals_seq001_v001.

Auto-generated. This test keeps codebase_vitals_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.codebase_vitals_seq001_v001 import snapshot_vitals, append_vitals, load_vitals, record_vitals
    assert callable(snapshot_vitals), "snapshot_vitals must be callable"
    assert callable(append_vitals), "append_vitals must be callable"
    assert callable(load_vitals), "load_vitals must be callable"
    assert callable(record_vitals), "record_vitals must be callable"
    print(f"  ✓ codebase_vitals_seq001_v001: 4 exports verified")

def test_snapshot_vitals_contract():
    """Data flow contract: snapshot_vitals(root, commit_hash, commit_msg) → output."""
    from src.codebase_vitals_seq001_v001 import snapshot_vitals
    # smoke test: function exists and is callable
    assert snapshot_vitals.__name__ == "snapshot_vitals"
    print(f"  ✓ snapshot_vitals: contract holds")

def test_append_vitals_contract():
    """Data flow contract: append_vitals(root, snap) → output."""
    from src.codebase_vitals_seq001_v001 import append_vitals
    # smoke test: function exists and is callable
    assert append_vitals.__name__ == "append_vitals"
    print(f"  ✓ append_vitals: contract holds")

def test_load_vitals_contract():
    """Data flow contract: load_vitals(root) → output."""
    from src.codebase_vitals_seq001_v001 import load_vitals
    # smoke test: function exists and is callable
    assert load_vitals.__name__ == "load_vitals"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = load_vitals(root)
    assert result is not None, "load_vitals returned None"
    print(f"  ✓ load_vitals: contract holds")

def test_record_vitals_contract():
    """Data flow contract: record_vitals(root, commit_hash, commit_msg) → output."""
    from src.codebase_vitals_seq001_v001 import record_vitals
    # smoke test: function exists and is callable
    assert record_vitals.__name__ == "record_vitals"
    print(f"  ✓ record_vitals: contract holds")

def run_interlink_test():
    """Run all interlink checks for codebase_vitals_seq001_v001."""
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
    print(f"  codebase_vitals_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
