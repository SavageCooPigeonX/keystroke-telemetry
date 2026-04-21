"""Interlink self-test for numeric_surface_seq001_v001.

Auto-generated. This test keeps numeric_surface_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.numeric_surface_seq001_v001 import generate_surface
    assert callable(generate_surface), "generate_surface must be callable"
    print(f"  ✓ numeric_surface_seq001_v001: 1 exports verified")

def test_generate_surface_contract():
    """Data flow contract: generate_surface(root) → output."""
    from src.numeric_surface_seq001_v001 import generate_surface
    # smoke test: function exists and is callable
    assert generate_surface.__name__ == "generate_surface"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = generate_surface(root)
    assert result is not None, "generate_surface returned None"
    print(f"  ✓ generate_surface: contract holds")

def run_interlink_test():
    """Run all interlink checks for numeric_surface_seq001_v001."""
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
    print(f"  numeric_surface_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
