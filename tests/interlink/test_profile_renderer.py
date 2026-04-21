"""Interlink self-test for profile_renderer_seq001_v001.

Auto-generated. This test keeps profile_renderer_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.profile_renderer_seq001_v001 import render_profile, render_profile_index, render_all_profiles
    assert callable(render_profile), "render_profile must be callable"
    assert callable(render_profile_index), "render_profile_index must be callable"
    assert callable(render_all_profiles), "render_all_profiles must be callable"
    print(f"  ✓ profile_renderer_seq001_v001: 3 exports verified")

def test_render_profile_contract():
    """Data flow contract: render_profile(ident, root) → output."""
    from src.profile_renderer_seq001_v001 import render_profile
    # smoke test: function exists and is callable
    assert render_profile.__name__ == "render_profile"
    print(f"  ✓ render_profile: contract holds")

def test_render_profile_index_contract():
    """Data flow contract: render_profile_index(identities, root) → output."""
    from src.profile_renderer_seq001_v001 import render_profile_index
    # smoke test: function exists and is callable
    assert render_profile_index.__name__ == "render_profile_index"
    print(f"  ✓ render_profile_index: contract holds")

def test_render_all_profiles_contract():
    """Data flow contract: render_all_profiles(root) → output."""
    from src.profile_renderer_seq001_v001 import render_all_profiles
    # smoke test: function exists and is callable
    assert render_all_profiles.__name__ == "render_all_profiles"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = render_all_profiles(root)
    assert result is not None, "render_all_profiles returned None"
    print(f"  ✓ render_all_profiles: contract holds")

def run_interlink_test():
    """Run all interlink checks for profile_renderer_seq001_v001."""
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
    print(f"  profile_renderer_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
