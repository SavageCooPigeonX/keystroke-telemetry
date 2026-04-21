"""Interlink self-test for operator_probes_seq001_v001.

Auto-generated. This test keeps operator_probes_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.operator_probes_seq001_v001 import build_probe_block, inject_probes
    assert callable(build_probe_block), "build_probe_block must be callable"
    assert callable(inject_probes), "inject_probes must be callable"
    print(f"  ✓ operator_probes_seq001_v001: 2 exports verified")

def test_build_probe_block_contract():
    """Data flow contract: build_probe_block(root) → output."""
    from src.operator_probes_seq001_v001 import build_probe_block
    # smoke test: function exists and is callable
    assert build_probe_block.__name__ == "build_probe_block"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_probe_block(root)
    assert result is not None, "build_probe_block returned None"
    print(f"  ✓ build_probe_block: contract holds")

def test_inject_probes_contract():
    """Data flow contract: inject_probes(root) → output."""
    from src.operator_probes_seq001_v001 import inject_probes
    # smoke test: function exists and is callable
    assert inject_probes.__name__ == "inject_probes"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = inject_probes(root)
    assert result is not None, "inject_probes returned None"
    print(f"  ✓ inject_probes: contract holds")

def run_interlink_test():
    """Run all interlink checks for operator_probes_seq001_v001."""
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
    print(f"  operator_probes_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
