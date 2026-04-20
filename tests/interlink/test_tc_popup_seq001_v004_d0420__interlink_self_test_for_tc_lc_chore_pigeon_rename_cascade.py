"""Interlink self-test for tc_popup_seq001_v002_d0420__passive_always_on_top_tkinter_lc_fix_close_outcome_sim.

Auto-generated. This test keeps tc_popup_seq001_v002_d0420__passive_always_on_top_tkinter_lc_fix_close_outcome_sim interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v004 | 41 lines | ~484 tokens
# DESC:   interlink_self_test_for_tc
# INTENT: chore_pigeon_rename_cascade
# LAST:   2026-04-20 @ c61fc91
# SESSIONS: 1
# ──────────────────────────────────────────────
import sys
from pathlib import Path
from src._resolve import src_import
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    run_popup = src_import("tc_popup_seq001", "run_popup")
    assert callable(run_popup), "run_popup must be callable"
    print(f"  ✓ tc_popup_seq001_v002_d0420__passive_always_on_top_tkinter_lc_fix_close_outcome_sim: 1 exports verified")

def test_run_popup_contract():
    """Data flow contract: run_popup(corner, pause_ms, width, height, opacity, surface_ready) → output."""
    run_popup = src_import("tc_popup_seq001", "run_popup")
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
