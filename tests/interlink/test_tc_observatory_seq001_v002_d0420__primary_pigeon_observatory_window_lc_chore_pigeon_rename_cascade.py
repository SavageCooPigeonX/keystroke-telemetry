"""Interlink self-test for tc_observatory_seq001_v002_d0420__primary_pigeon_observatory_window_lc_chore_pigeon_rename_cascade.

Auto-generated. This test keeps tc_observatory_seq001_v002_d0420__primary_pigeon_observatory_window_lc_chore_pigeon_rename_cascade interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.tc_observatory_seq001_v002_d0420__primary_pigeon_observatory_window_lc_chore_pigeon_rename_cascade import run_observatory
    assert callable(run_observatory), "run_observatory must be callable"
    print(f"  ✓ tc_observatory_seq001_v002_d0420__primary_pigeon_observatory_window_lc_chore_pigeon_rename_cascade: 1 exports verified")

def test_run_observatory_contract():
    """Data flow contract: run_observatory() → output."""
    from src.tc_observatory_seq001_v002_d0420__primary_pigeon_observatory_window_lc_chore_pigeon_rename_cascade import run_observatory
    # smoke test: function exists and is callable
    assert run_observatory.__name__ == "run_observatory"
    result = run_observatory()
    assert result is not None, "run_observatory returned None"
    print(f"  ✓ run_observatory: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_observatory_seq001_v002_d0420__primary_pigeon_observatory_window_lc_chore_pigeon_rename_cascade."""
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
    print(f"  tc_observatory_seq001_v002_d0420__primary_pigeon_observatory_window_lc_chore_pigeon_rename_cascade: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
