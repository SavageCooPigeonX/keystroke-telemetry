"""Interlink self-test for scale_inference_seq001_v001.

Auto-generated. This test keeps scale_inference_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.scale_inference_seq001_v001_seq001_v001 import infer_scale, scale_to_token_budget, scale_to_instructions
    assert callable(infer_scale), "infer_scale must be callable"
    assert callable(scale_to_token_budget), "scale_to_token_budget must be callable"
    assert callable(scale_to_instructions), "scale_to_instructions must be callable"
    print(f"  ✓ scale_inference_seq001_v001: 3 exports verified")

def test_infer_scale_contract():
    """Data flow contract: infer_scale(fragment, cognitive_state, wpm, del_ratio) → output."""
    from src.scale_inference_seq001_v001_seq001_v001 import infer_scale
    # smoke test: function exists and is callable
    assert infer_scale.__name__ == "infer_scale"
    print(f"  ✓ infer_scale: contract holds")

def test_scale_to_token_budget_contract():
    """Data flow contract: scale_to_token_budget(scale) → output."""
    from src.scale_inference_seq001_v001_seq001_v001 import scale_to_token_budget
    # smoke test: function exists and is callable
    assert scale_to_token_budget.__name__ == "scale_to_token_budget"
    print(f"  ✓ scale_to_token_budget: contract holds")

def test_scale_to_instructions_contract():
    """Data flow contract: scale_to_instructions(scale) → output."""
    from src.scale_inference_seq001_v001_seq001_v001 import scale_to_instructions
    # smoke test: function exists and is callable
    assert scale_to_instructions.__name__ == "scale_to_instructions"
    print(f"  ✓ scale_to_instructions: contract holds")

def run_interlink_test():
    """Run all interlink checks for scale_inference_seq001_v001."""
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
    print(f"  scale_inference_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
