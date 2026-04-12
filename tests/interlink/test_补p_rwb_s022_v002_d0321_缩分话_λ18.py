"""Interlink self-test for 补p_rwb_s022_v002_d0321_缩分话_λ18.

Auto-generated. This test keeps 补p_rwb_s022_v002_d0321_缩分话_λ18 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.补p_rwb_s022_v002_d0321_缩分话_λ18 import backfill
    assert callable(backfill), "backfill must be callable"
    print(f"  ✓ 补p_rwb_s022_v002_d0321_缩分话_λ18: 1 exports verified")

def test_backfill_contract():
    """Data flow contract: backfill(root) → output."""
    from src.补p_rwb_s022_v002_d0321_缩分话_λ18 import backfill
    # smoke test: function exists and is callable
    assert backfill.__name__ == "backfill"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = backfill(root)
    assert result is not None, "backfill returned None"
    print(f"  ✓ backfill: contract holds")

def run_interlink_test():
    """Run all interlink checks for 补p_rwb_s022_v002_d0321_缩分话_λ18."""
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
    print(f"  补p_rwb_s022_v002_d0321_缩分话_λ18: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
