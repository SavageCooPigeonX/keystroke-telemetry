"""Interlink self-test for loop_killswitch_sim.

Auto-generated. This test keeps loop_killswitch_sim interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.loop_killswitch_sim import run_sim
    assert callable(run_sim), "run_sim must be callable"
    print(f"  ✓ loop_killswitch_sim: 1 exports verified")

def test_run_sim_contract():
    """Data flow contract: run_sim() → output."""
    from src.loop_killswitch_sim import run_sim
    # smoke test: function exists and is callable
    assert run_sim.__name__ == "run_sim"
    result = run_sim()
    assert result is not None, "run_sim returned None"
    print(f"  ✓ run_sim: contract holds")

def run_interlink_test():
    """Run all interlink checks for loop_killswitch_sim."""
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
    print(f"  loop_killswitch_sim: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
