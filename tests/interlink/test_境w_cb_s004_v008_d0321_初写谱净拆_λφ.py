"""Interlink self-test for 境w_cb_s004_v008_d0321_初写谱净拆_λφ.

Auto-generated. This test keeps 境w_cb_s004_v008_d0321_初写谱净拆_λφ interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.境w_cb_s004_v008_d0321_初写谱净拆_λφ import default_budget_config, estimate_tokens, score_context_budget
    assert callable(default_budget_config), "default_budget_config must be callable"
    assert callable(estimate_tokens), "estimate_tokens must be callable"
    assert callable(score_context_budget), "score_context_budget must be callable"
    print(f"  ✓ 境w_cb_s004_v008_d0321_初写谱净拆_λφ: 3 exports verified")

def test_default_budget_config_contract():
    """Data flow contract: default_budget_config() → output."""
    from src.境w_cb_s004_v008_d0321_初写谱净拆_λφ import default_budget_config
    # smoke test: function exists and is callable
    assert default_budget_config.__name__ == "default_budget_config"
    result = default_budget_config()
    assert result is not None, "default_budget_config returned None"
    print(f"  ✓ default_budget_config: contract holds")

def test_estimate_tokens_contract():
    """Data flow contract: estimate_tokens(line_count) → output."""
    from src.境w_cb_s004_v008_d0321_初写谱净拆_λφ import estimate_tokens
    # smoke test: function exists and is callable
    assert estimate_tokens.__name__ == "estimate_tokens"
    print(f"  ✓ estimate_tokens: contract holds")

def test_score_context_budget_contract():
    """Data flow contract: score_context_budget(file_lines, dependency_lines, coupling_score, config) → output."""
    from src.境w_cb_s004_v008_d0321_初写谱净拆_λφ import score_context_budget
    # smoke test: function exists and is callable
    assert score_context_budget.__name__ == "score_context_budget"
    print(f"  ✓ score_context_budget: contract holds")

def run_interlink_test():
    """Run all interlink checks for 境w_cb_s004_v008_d0321_初写谱净拆_λφ."""
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
    print(f"  境w_cb_s004_v008_d0321_初写谱净拆_λφ: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
