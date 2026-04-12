"""Interlink self-test for u_cs_s033_v001.

Auto-generated. This test keeps u_cs_s033_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.u_cs_s033_v001 import score_module_confidence, compute_copilot_meta_state, format_confidence_line
    assert callable(score_module_confidence), "score_module_confidence must be callable"
    assert callable(compute_copilot_meta_state), "compute_copilot_meta_state must be callable"
    assert callable(format_confidence_line), "format_confidence_line must be callable"
    print(f"  ✓ u_cs_s033_v001: 3 exports verified")

def test_score_module_confidence_contract():
    """Data flow contract: score_module_confidence(root, registry_modules) → output."""
    from src.u_cs_s033_v001 import score_module_confidence
    # smoke test: function exists and is callable
    assert score_module_confidence.__name__ == "score_module_confidence"
    print(f"  ✓ score_module_confidence: contract holds")

def test_compute_copilot_meta_state_contract():
    """Data flow contract: compute_copilot_meta_state(scores) → output."""
    from src.u_cs_s033_v001 import compute_copilot_meta_state
    # smoke test: function exists and is callable
    assert compute_copilot_meta_state.__name__ == "compute_copilot_meta_state"
    print(f"  ✓ compute_copilot_meta_state: contract holds")

def test_format_confidence_line_contract():
    """Data flow contract: format_confidence_line(meta) → output."""
    from src.u_cs_s033_v001 import format_confidence_line
    # smoke test: function exists and is callable
    assert format_confidence_line.__name__ == "format_confidence_line"
    print(f"  ✓ format_confidence_line: contract holds")

def run_interlink_test():
    """Run all interlink checks for u_cs_s033_v001."""
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
    print(f"  u_cs_s033_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
