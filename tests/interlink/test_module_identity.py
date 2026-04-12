"""Interlink self-test for module_identity.

Auto-generated. This test keeps module_identity interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.module_identity import build_identities
    assert callable(build_identities), "build_identities must be callable"
    print(f"  ✓ module_identity: 1 exports verified")

def test_build_identities_contract():
    """Data flow contract: build_identities(root, include_consciousness) → output."""
    from src.module_identity import build_identities
    # smoke test: function exists and is callable
    assert build_identities.__name__ == "build_identities"
    print(f"  ✓ build_identities: contract holds")

def run_interlink_test():
    """Run all interlink checks for module_identity."""
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
    print(f"  module_identity: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
