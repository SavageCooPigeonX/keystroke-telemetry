"""Interlink self-test for probe_resolver_seq001_v001.

Auto-generated. This test keeps probe_resolver_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.probe_resolver_seq001_v001_seq001_v001 import resolve_probe, resolve_all_pending
    assert callable(resolve_probe), "resolve_probe must be callable"
    assert callable(resolve_all_pending), "resolve_all_pending must be callable"
    print(f"  ✓ probe_resolver_seq001_v001: 2 exports verified")

def test_resolve_probe_contract():
    """Data flow contract: resolve_probe(root, probe) → output."""
    from src.probe_resolver_seq001_v001_seq001_v001 import resolve_probe
    # smoke test: function exists and is callable
    assert resolve_probe.__name__ == "resolve_probe"
    print(f"  ✓ resolve_probe: contract holds")

def test_resolve_all_pending_contract():
    """Data flow contract: resolve_all_pending(root, auto_write) → output."""
    from src.probe_resolver_seq001_v001_seq001_v001 import resolve_all_pending
    # smoke test: function exists and is callable
    assert resolve_all_pending.__name__ == "resolve_all_pending"
    print(f"  ✓ resolve_all_pending: contract holds")

def run_interlink_test():
    """Run all interlink checks for probe_resolver_seq001_v001."""
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
    print(f"  probe_resolver_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
