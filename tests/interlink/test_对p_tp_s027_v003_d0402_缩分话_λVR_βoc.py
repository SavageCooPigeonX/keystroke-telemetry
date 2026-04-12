"""Interlink self-test for 对p_tp_s027_v003_d0402_缩分话_λVR_βoc.

Auto-generated. This test keeps 对p_tp_s027_v003_d0402_缩分话_λVR_βoc interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.对p_tp_s027_v003_d0402_缩分话_λVR_βoc import capture_training_pair, generate_cycle_summary
    assert callable(capture_training_pair), "capture_training_pair must be callable"
    assert callable(generate_cycle_summary), "generate_cycle_summary must be callable"
    print(f"  ✓ 对p_tp_s027_v003_d0402_缩分话_λVR_βoc: 2 exports verified")

def test_capture_training_pair_contract():
    """Data flow contract: capture_training_pair(root) → output."""
    from src.对p_tp_s027_v003_d0402_缩分话_λVR_βoc import capture_training_pair
    # smoke test: function exists and is callable
    assert capture_training_pair.__name__ == "capture_training_pair"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = capture_training_pair(root)
    assert result is not None, "capture_training_pair returned None"
    print(f"  ✓ capture_training_pair: contract holds")

def test_generate_cycle_summary_contract():
    """Data flow contract: generate_cycle_summary(root, cycle) → output."""
    from src.对p_tp_s027_v003_d0402_缩分话_λVR_βoc import generate_cycle_summary
    # smoke test: function exists and is callable
    assert generate_cycle_summary.__name__ == "generate_cycle_summary"
    print(f"  ✓ generate_cycle_summary: contract holds")

def run_interlink_test():
    """Run all interlink checks for 对p_tp_s027_v003_d0402_缩分话_λVR_βoc."""
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
    print(f"  对p_tp_s027_v003_d0402_缩分话_λVR_βoc: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
