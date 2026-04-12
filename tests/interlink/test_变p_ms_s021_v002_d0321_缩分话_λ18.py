"""Interlink self-test for 变p_ms_s021_v002_d0321_缩分话_λ18.

Auto-generated. This test keeps 变p_ms_s021_v002_d0321_缩分话_λ18 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.变p_ms_s021_v002_d0321_缩分话_λ18 import score_mutations
    assert callable(score_mutations), "score_mutations must be callable"
    print(f"  ✓ 变p_ms_s021_v002_d0321_缩分话_λ18: 1 exports verified")

def test_score_mutations_contract():
    """Data flow contract: score_mutations(root) → output."""
    from src.变p_ms_s021_v002_d0321_缩分话_λ18 import score_mutations
    # smoke test: function exists and is callable
    assert score_mutations.__name__ == "score_mutations"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = score_mutations(root)
    assert result is not None, "score_mutations returned None"
    print(f"  ✓ score_mutations: contract holds")

def run_interlink_test():
    """Run all interlink checks for 变p_ms_s021_v002_d0321_缩分话_λ18."""
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
    print(f"  变p_ms_s021_v002_d0321_缩分话_λ18: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
