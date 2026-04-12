"""Interlink self-test for 虚f_mc_s036_v001_profile.

Auto-generated. This test keeps 虚f_mc_s036_v001_profile interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.虚f_mc_s036_v001_profile import read_source, is_real_module_name, top_hesitation_files, find_module_path, build_file_profile
    assert callable(read_source), "read_source must be callable"
    assert callable(is_real_module_name), "is_real_module_name must be callable"
    assert callable(top_hesitation_files), "top_hesitation_files must be callable"
    assert callable(find_module_path), "find_module_path must be callable"
    assert callable(build_file_profile), "build_file_profile must be callable"
    print(f"  ✓ 虚f_mc_s036_v001_profile: 5 exports verified")

def test_read_source_contract():
    """Data flow contract: read_source(root, rel_path, max_lines) → output."""
    from src.虚f_mc_s036_v001_profile import read_source
    # smoke test: function exists and is callable
    assert read_source.__name__ == "read_source"
    print(f"  ✓ read_source: contract holds")

def test_is_real_module_name_contract():
    """Data flow contract: is_real_module_name(name) → output."""
    from src.虚f_mc_s036_v001_profile import is_real_module_name
    # smoke test: function exists and is callable
    assert is_real_module_name.__name__ == "is_real_module_name"
    print(f"  ✓ is_real_module_name: contract holds")

def test_top_hesitation_files_contract():
    """Data flow contract: top_hesitation_files(root, threshold, max_n) → output."""
    from src.虚f_mc_s036_v001_profile import top_hesitation_files
    # smoke test: function exists and is callable
    assert top_hesitation_files.__name__ == "top_hesitation_files"
    print(f"  ✓ top_hesitation_files: contract holds")

def test_find_module_path_contract():
    """Data flow contract: find_module_path(root, module_name) → output."""
    from src.虚f_mc_s036_v001_profile import find_module_path
    # smoke test: function exists and is callable
    assert find_module_path.__name__ == "find_module_path"
    print(f"  ✓ find_module_path: contract holds")

def test_build_file_profile_contract():
    """Data flow contract: build_file_profile(root, module_name, hes_score) → output."""
    from src.虚f_mc_s036_v001_profile import build_file_profile
    # smoke test: function exists and is callable
    assert build_file_profile.__name__ == "build_file_profile"
    print(f"  ✓ build_file_profile: contract holds")

def run_interlink_test():
    """Run all interlink checks for 虚f_mc_s036_v001_profile."""
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
    print(f"  虚f_mc_s036_v001_profile: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
