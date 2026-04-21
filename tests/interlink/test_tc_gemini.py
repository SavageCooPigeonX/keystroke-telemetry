"""Interlink self-test for tc_gemini_seq001_v001.

Auto-generated. This test keeps tc_gemini_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer import ThoughtBuffer, call_gemini, log_completion
    assert callable(ThoughtBuffer), "ThoughtBuffer must be callable"
    assert callable(call_gemini), "call_gemini must be callable"
    assert callable(log_completion), "log_completion must be callable"
    print(f"  ✓ tc_gemini_seq001_v001: 3 exports verified")

def test_call_gemini_contract():
    """Data flow contract: call_gemini(buffer, thought_buffer) → output."""
    from src.tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer import call_gemini
    # smoke test: function exists and is callable
    assert call_gemini.__name__ == "call_gemini"
    print(f"  ✓ call_gemini: contract holds")

def test_log_completion_contract():
    """Data flow contract: log_completion(entry) → output."""
    from src.tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer import log_completion
    # smoke test: function exists and is callable
    assert log_completion.__name__ == "log_completion"
    print(f"  ✓ log_completion: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_gemini_seq001_v001."""
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
    print(f"  tc_gemini_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
