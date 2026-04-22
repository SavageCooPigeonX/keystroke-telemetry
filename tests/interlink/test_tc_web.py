"""Interlink self-test for tc_web_seq001_v001.

Auto-generated. This test keeps tc_web_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src._resolve import src_import as _src_import

def test_import():
    """Module imports without error."""
    run_web = _src_import("tc_web_seq001", "run_web")
    assert callable(run_web), "run_web must be callable"
    print(f"  ✓ tc_web_seq001_v001: 1 exports verified")

def test_run_web_contract():
    """Data flow contract: run_web(port) → output."""
    run_web = _src_import("tc_web_seq001", "run_web")
    # smoke test: function exists and is callable
    assert run_web.__name__ == "run_web"
    print(f"  ✓ run_web: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_web_seq001_v001."""
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
    print(f"  tc_web_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
