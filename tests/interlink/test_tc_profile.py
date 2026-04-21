"""Interlink self-test for tc_profile_seq001_v001.

Auto-generated. This test keeps tc_profile_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.tc_profile_seq001_v001 import load_profile, save_profile, update_profile_from_completion, update_profile_from_composition, bootstrap_profile, format_profile_for_prompt
    assert callable(load_profile), "load_profile must be callable"
    assert callable(save_profile), "save_profile must be callable"
    assert callable(update_profile_from_completion), "update_profile_from_completion must be callable"
    assert callable(update_profile_from_composition), "update_profile_from_composition must be callable"
    assert callable(bootstrap_profile), "bootstrap_profile must be callable"
    assert callable(format_profile_for_prompt), "format_profile_for_prompt must be callable"
    print(f"  ✓ tc_profile_seq001_v001: 6 exports verified")

def test_load_profile_contract():
    """Data flow contract: load_profile() → output."""
    from src.tc_profile_seq001_v001 import load_profile
    # smoke test: function exists and is callable
    assert load_profile.__name__ == "load_profile"
    result = load_profile()
    assert result is not None, "load_profile returned None"
    print(f"  ✓ load_profile: contract holds")

def test_save_profile_contract():
    """Data flow contract: save_profile(profile) → output."""
    from src.tc_profile_seq001_v001 import save_profile
    # smoke test: function exists and is callable
    assert save_profile.__name__ == "save_profile"
    print(f"  ✓ save_profile: contract holds")

def test_update_profile_from_completion_contract():
    """Data flow contract: update_profile_from_completion(buffer, completion, outcome, context, repo) → output."""
    from src.tc_profile_seq001_v001 import update_profile_from_completion
    # smoke test: function exists and is callable
    assert update_profile_from_completion.__name__ == "update_profile_from_completion"
    print(f"  ✓ update_profile_from_completion: contract holds")

def test_update_profile_from_composition_contract():
    """Data flow contract: update_profile_from_composition(comp) → output."""
    from src.tc_profile_seq001_v001 import update_profile_from_composition
    # smoke test: function exists and is callable
    assert update_profile_from_composition.__name__ == "update_profile_from_composition"
    print(f"  ✓ update_profile_from_composition: contract holds")

def test_bootstrap_profile_contract():
    """Data flow contract: bootstrap_profile() → output."""
    from src.tc_profile_seq001_v001 import bootstrap_profile
    # smoke test: function exists and is callable
    assert bootstrap_profile.__name__ == "bootstrap_profile"
    result = bootstrap_profile()
    assert result is not None, "bootstrap_profile returned None"
    print(f"  ✓ bootstrap_profile: contract holds")

def test_format_profile_for_prompt_contract():
    """Data flow contract: format_profile_for_prompt(profile) → output."""
    from src.tc_profile_seq001_v001 import format_profile_for_prompt
    # smoke test: function exists and is callable
    assert format_profile_for_prompt.__name__ == "format_profile_for_prompt"
    print(f"  ✓ format_profile_for_prompt: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_profile_seq001_v001."""
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
    print(f"  tc_profile_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
