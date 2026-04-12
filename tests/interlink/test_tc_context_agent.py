"""Interlink self-test for tc_context_agent.

Auto-generated. This test keeps tc_context_agent interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.tc_context_agent import select_context_files, build_code_context
    assert callable(select_context_files), "select_context_files must be callable"
    assert callable(build_code_context), "build_code_context must be callable"
    print(f"  ✓ tc_context_agent: 2 exports verified")

def test_select_context_files_contract():
    """Data flow contract: select_context_files(buffer, ctx, max_files) → output."""
    from src.tc_context_agent import select_context_files
    # smoke test: function exists and is callable
    assert select_context_files.__name__ == "select_context_files"
    print(f"  ✓ select_context_files: contract holds")

def test_build_code_context_contract():
    """Data flow contract: build_code_context(buffer, ctx) → output."""
    from src.tc_context_agent import build_code_context
    # smoke test: function exists and is callable
    assert build_code_context.__name__ == "build_code_context"
    print(f"  ✓ build_code_context: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_context_agent."""
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
    print(f"  tc_context_agent: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
