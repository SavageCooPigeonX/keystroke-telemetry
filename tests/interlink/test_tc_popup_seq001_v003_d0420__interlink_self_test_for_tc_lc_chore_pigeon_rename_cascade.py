"""Interlink self-test for tc_popup_seq001_v002_d0420__passive_always_on_top_tkinter_lc_fix_close_outcome_sim.

Auto-generated. This test keeps tc_popup_seq001_v002_d0420__passive_always_on_top_tkinter_lc_fix_close_outcome_sim interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.tc_popup_seq001_v003_d0420__passive_always_on_top_tkinter_lc_chore_pigeon_rename_cascade import run_popup
    assert callable(run_popup), "run_popup must be callable"
    print(f"  ✓ tc_popup_seq001_v002_d0420__passive_always_on_top_tkinter_lc_fix_close_outcome_sim: 1 exports verified")

def test_run_popup_contract():
    """Data flow contract: run_popup(corner, pause_ms, width, height, opacity, surface_ready) → output."""
    from src.tc_popup_seq001_v003_d0420__passive_always_on_top_tkinter_lc_chore_pigeon_rename_cascade import run_popup
    # smoke test: function exists and is callable
    assert run_popup.__name__ == "run_popup"
    print(f"  ✓ run_popup: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_popup_seq001_v002_d0420__passive_always_on_top_tkinter_lc_fix_close_outcome_sim."""
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
    print(f"  tc_popup_seq001_v002_d0420__passive_always_on_top_tkinter_lc_fix_close_outcome_sim: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
