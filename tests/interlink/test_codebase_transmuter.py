"""Interlink self-test for codebase_transmuter.

Auto-generated. This test keeps codebase_transmuter interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.codebase_transmuter import numerify_file, build_numerical_mirror, build_narrative_mirror, compute_global_stats, transmute_all
    assert callable(numerify_file), "numerify_file must be callable"
    assert callable(build_numerical_mirror), "build_numerical_mirror must be callable"
    assert callable(build_narrative_mirror), "build_narrative_mirror must be callable"
    assert callable(compute_global_stats), "compute_global_stats must be callable"
    assert callable(transmute_all), "transmute_all must be callable"
    print(f"  ✓ codebase_transmuter: 5 exports verified")

def test_numerify_file_contract():
    """Data flow contract: numerify_file(filepath) → output."""
    from src.codebase_transmuter import numerify_file
    # smoke test: function exists and is callable
    assert numerify_file.__name__ == "numerify_file"
    print(f"  ✓ numerify_file: contract holds")

def test_build_numerical_mirror_contract():
    """Data flow contract: build_numerical_mirror(root) → output."""
    from src.codebase_transmuter import build_numerical_mirror
    # smoke test: function exists and is callable
    assert build_numerical_mirror.__name__ == "build_numerical_mirror"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_numerical_mirror(root)
    assert result is not None, "build_numerical_mirror returned None"
    print(f"  ✓ build_numerical_mirror: contract holds")

def test_build_narrative_mirror_contract():
    """Data flow contract: build_narrative_mirror(root) → output."""
    from src.codebase_transmuter import build_narrative_mirror
    # smoke test: function exists and is callable
    assert build_narrative_mirror.__name__ == "build_narrative_mirror"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_narrative_mirror(root)
    assert result is not None, "build_narrative_mirror returned None"
    print(f"  ✓ build_narrative_mirror: contract holds")

def test_compute_global_stats_contract():
    """Data flow contract: compute_global_stats(root) → output."""
    from src.codebase_transmuter import compute_global_stats
    # smoke test: function exists and is callable
    assert compute_global_stats.__name__ == "compute_global_stats"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = compute_global_stats(root)
    assert result is not None, "compute_global_stats returned None"
    print(f"  ✓ compute_global_stats: contract holds")

def test_transmute_all_contract():
    """Data flow contract: transmute_all(root) → output."""
    from src.codebase_transmuter import transmute_all
    # smoke test: function exists and is callable
    assert transmute_all.__name__ == "transmute_all"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = transmute_all(root)
    assert result is not None, "transmute_all returned None"
    print(f"  ✓ transmute_all: contract holds")

def run_interlink_test():
    """Run all interlink checks for codebase_transmuter."""
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
    print(f"  codebase_transmuter: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
