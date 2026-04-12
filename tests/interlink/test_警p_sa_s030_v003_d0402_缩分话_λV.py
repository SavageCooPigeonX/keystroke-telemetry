"""Interlink self-test for 警p_sa_s030_v003_d0402_缩分话_λV.

Auto-generated. This test keeps 警p_sa_s030_v003_d0402_缩分话_λV interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.警p_sa_s030_v003_d0402_缩分话_λV import check_staleness, inject_staleness_alert
    assert callable(check_staleness), "check_staleness must be callable"
    assert callable(inject_staleness_alert), "inject_staleness_alert must be callable"
    print(f"  ✓ 警p_sa_s030_v003_d0402_缩分话_λV: 2 exports verified")

def test_check_staleness_contract():
    """Data flow contract: check_staleness(root) → output."""
    from src.警p_sa_s030_v003_d0402_缩分话_λV import check_staleness
    # smoke test: function exists and is callable
    assert check_staleness.__name__ == "check_staleness"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = check_staleness(root)
    assert result is not None, "check_staleness returned None"
    print(f"  ✓ check_staleness: contract holds")

def test_inject_staleness_alert_contract():
    """Data flow contract: inject_staleness_alert(root) → output."""
    from src.警p_sa_s030_v003_d0402_缩分话_λV import inject_staleness_alert
    # smoke test: function exists and is callable
    assert inject_staleness_alert.__name__ == "inject_staleness_alert"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = inject_staleness_alert(root)
    assert result is not None, "inject_staleness_alert returned None"
    print(f"  ✓ inject_staleness_alert: contract holds")

def run_interlink_test():
    """Run all interlink checks for 警p_sa_s030_v003_d0402_缩分话_λV."""
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
    print(f"  警p_sa_s030_v003_d0402_缩分话_λV: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
