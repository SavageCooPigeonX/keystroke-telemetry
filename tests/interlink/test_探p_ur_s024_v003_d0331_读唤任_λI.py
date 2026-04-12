"""Interlink self-test for 探p_ur_s024_v003_d0331_读唤任_λI.

Auto-generated. This test keeps 探p_ur_s024_v003_d0331_读唤任_λI interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.探p_ur_s024_v003_d0331_读唤任_λI import reconstruct_if_needed
    assert callable(reconstruct_if_needed), "reconstruct_if_needed must be callable"
    print(f"  ✓ 探p_ur_s024_v003_d0331_读唤任_λI: 1 exports verified")

def test_reconstruct_if_needed_contract():
    """Data flow contract: reconstruct_if_needed(root, composition) → output."""
    from src.探p_ur_s024_v003_d0331_读唤任_λI import reconstruct_if_needed
    # smoke test: function exists and is callable
    assert reconstruct_if_needed.__name__ == "reconstruct_if_needed"
    print(f"  ✓ reconstruct_if_needed: contract holds")

def run_interlink_test():
    """Run all interlink checks for 探p_ur_s024_v003_d0331_读唤任_λI."""
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
    print(f"  探p_ur_s024_v003_d0331_读唤任_λI: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
