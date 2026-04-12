"""Interlink self-test for 虚f_mc_s036_v001.

Auto-generated. This test keeps 虚f_mc_s036_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.虚f_mc_s036_v001 import scan_missing_context
    assert callable(scan_missing_context), "scan_missing_context must be callable"
    print(f"  ✓ 虚f_mc_s036_v001: 1 exports verified")

def test_scan_missing_context_contract():
    """Data flow contract: scan_missing_context(root) → output."""
    from src.虚f_mc_s036_v001 import scan_missing_context
    # smoke test: function exists and is callable
    assert scan_missing_context.__name__ == "scan_missing_context"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = scan_missing_context(root)
    assert result is not None, "scan_missing_context returned None"
    print(f"  ✓ scan_missing_context: contract holds")

def run_interlink_test():
    """Run all interlink checks for 虚f_mc_s036_v001."""
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
    print(f"  虚f_mc_s036_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
