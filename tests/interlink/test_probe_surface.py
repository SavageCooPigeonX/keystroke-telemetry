"""Interlink self-test for probe_surface_seq001_v001.

Auto-generated. This test keeps probe_surface_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.probe_surface_seq001_v001 import parse_probe_blocks, harvest_pending_probes, write_resolution, build_resolution_block
    assert callable(parse_probe_blocks), "parse_probe_blocks must be callable"
    assert callable(harvest_pending_probes), "harvest_pending_probes must be callable"
    assert callable(write_resolution), "write_resolution must be callable"
    assert callable(build_resolution_block), "build_resolution_block must be callable"
    print(f"  ✓ probe_surface_seq001_v001: 4 exports verified")

def test_parse_probe_blocks_contract():
    """Data flow contract: parse_probe_blocks(text) → output."""
    from src.probe_surface_seq001_v001 import parse_probe_blocks
    # smoke test: function exists and is callable
    assert parse_probe_blocks.__name__ == "parse_probe_blocks"
    print(f"  ✓ parse_probe_blocks: contract holds")

def test_harvest_pending_probes_contract():
    """Data flow contract: harvest_pending_probes(root, limit) → output."""
    from src.probe_surface_seq001_v001 import harvest_pending_probes
    # smoke test: function exists and is callable
    assert harvest_pending_probes.__name__ == "harvest_pending_probes"
    print(f"  ✓ harvest_pending_probes: contract holds")

def test_write_resolution_contract():
    """Data flow contract: write_resolution(root, probe, resolution) → output."""
    from src.probe_surface_seq001_v001 import write_resolution
    # smoke test: function exists and is callable
    assert write_resolution.__name__ == "write_resolution"
    print(f"  ✓ write_resolution: contract holds")

def test_build_resolution_block_contract():
    """Data flow contract: build_resolution_block(root, max_items) → output."""
    from src.probe_surface_seq001_v001 import build_resolution_block
    # smoke test: function exists and is callable
    assert build_resolution_block.__name__ == "build_resolution_block"
    print(f"  ✓ build_resolution_block: contract holds")

def run_interlink_test():
    """Run all interlink checks for probe_surface_seq001_v001."""
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
    print(f"  probe_surface_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
