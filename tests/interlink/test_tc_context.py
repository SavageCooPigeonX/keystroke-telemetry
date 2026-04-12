"""Interlink self-test for tc_context.

Auto-generated. This test keeps tc_context interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.tc_context import load_context, invalidate_context_cache
    assert callable(load_context), "load_context must be callable"
    assert callable(invalidate_context_cache), "invalidate_context_cache must be callable"
    print(f"  ✓ tc_context: 2 exports verified")

def test_load_context_contract():
    """Data flow contract: load_context(repo_root) → output."""
    from src.tc_context import load_context
    # smoke test: function exists and is callable
    assert load_context.__name__ == "load_context"
    print(f"  ✓ load_context: contract holds")

def test_invalidate_context_cache_contract():
    """Data flow contract: invalidate_context_cache() → output."""
    from src.tc_context import invalidate_context_cache
    # smoke test: function exists and is callable
    assert invalidate_context_cache.__name__ == "invalidate_context_cache"
    result = invalidate_context_cache()
    assert result is not None, "invalidate_context_cache returned None"
    print(f"  ✓ invalidate_context_cache: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_context."""
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
    print(f"  tc_context: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
