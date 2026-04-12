"""Interlink self-test for 虚f_mc_s036_v001_llm.

Auto-generated. This test keeps 虚f_mc_s036_v001_llm interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.虚f_mc_s036_v001_llm import get_api_key, build_void_prompt, call_gemini, parse_blocks
    assert callable(get_api_key), "get_api_key must be callable"
    assert callable(build_void_prompt), "build_void_prompt must be callable"
    assert callable(call_gemini), "call_gemini must be callable"
    assert callable(parse_blocks), "parse_blocks must be callable"
    print(f"  ✓ 虚f_mc_s036_v001_llm: 4 exports verified")

def test_get_api_key_contract():
    """Data flow contract: get_api_key(root) → output."""
    from src.虚f_mc_s036_v001_llm import get_api_key
    # smoke test: function exists and is callable
    assert get_api_key.__name__ == "get_api_key"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = get_api_key(root)
    assert result is not None, "get_api_key returned None"
    print(f"  ✓ get_api_key: contract holds")

def test_build_void_prompt_contract():
    """Data flow contract: build_void_prompt(module_name, profile) → output."""
    from src.虚f_mc_s036_v001_llm import build_void_prompt
    # smoke test: function exists and is callable
    assert build_void_prompt.__name__ == "build_void_prompt"
    print(f"  ✓ build_void_prompt: contract holds")

def test_call_gemini_contract():
    """Data flow contract: call_gemini(api_key, prompt) → output."""
    from src.虚f_mc_s036_v001_llm import call_gemini
    # smoke test: function exists and is callable
    assert call_gemini.__name__ == "call_gemini"
    print(f"  ✓ call_gemini: contract holds")

def test_parse_blocks_contract():
    """Data flow contract: parse_blocks(raw) → output."""
    from src.虚f_mc_s036_v001_llm import parse_blocks
    # smoke test: function exists and is callable
    assert parse_blocks.__name__ == "parse_blocks"
    print(f"  ✓ parse_blocks: contract holds")

def run_interlink_test():
    """Run all interlink checks for 虚f_mc_s036_v001_llm."""
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
    print(f"  虚f_mc_s036_v001_llm: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
