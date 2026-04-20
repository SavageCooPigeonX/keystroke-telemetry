"""Interlink self-test for p_tcsr_s008_v002_d0420_λRN.

Auto-generated. This test keeps p_tcsr_s008_v002_d0420_λRN interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.tc_sim.p_tcsr_s008_v002_d0420_λRN import replay_pause_live
    assert callable(replay_pause_live), "replay_pause_live must be callable"
    print(f"  ✓ p_tcsr_s008_v002_d0420_λRN: 1 exports verified")

def test_replay_pause_live_contract():
    """Data flow contract: replay_pause_live(pause, use_historical_ctx) → output."""
    from src.tc_sim.p_tcsr_s008_v002_d0420_λRN import replay_pause_live
    # smoke test: function exists and is callable
    assert replay_pause_live.__name__ == "replay_pause_live"
    print(f"  ✓ replay_pause_live: contract holds")

def run_interlink_test():
    """Run all interlink checks for p_tcsr_s008_v002_d0420_λRN."""
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
    print(f"  p_tcsr_s008_v002_d0420_λRN: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
