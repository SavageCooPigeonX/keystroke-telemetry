"""Interlink self-test for u_prc_s016_v001.

Auto-generated. This test keeps u_prc_s016_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.u_prc_s016_v001 import reconstruct_all, reconstruct_latest, build_mutation_audit, get_latest_composition, track_copilot_prompt_mutations
    assert callable(reconstruct_all), "reconstruct_all must be callable"
    assert callable(reconstruct_latest), "reconstruct_latest must be callable"
    assert callable(build_mutation_audit), "build_mutation_audit must be callable"
    assert callable(get_latest_composition), "get_latest_composition must be callable"
    assert callable(track_copilot_prompt_mutations), "track_copilot_prompt_mutations must be callable"
    print(f"  ✓ u_prc_s016_v001: 5 exports verified")

def test_reconstruct_all_contract():
    """Data flow contract: reconstruct_all(root) → output."""
    from src.u_prc_s016_v001 import reconstruct_all
    # smoke test: function exists and is callable
    assert reconstruct_all.__name__ == "reconstruct_all"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = reconstruct_all(root)
    assert result is not None, "reconstruct_all returned None"
    print(f"  ✓ reconstruct_all: contract holds")

def test_reconstruct_latest_contract():
    """Data flow contract: reconstruct_latest(root) → output."""
    from src.u_prc_s016_v001 import reconstruct_latest
    # smoke test: function exists and is callable
    assert reconstruct_latest.__name__ == "reconstruct_latest"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = reconstruct_latest(root)
    assert result is not None, "reconstruct_latest returned None"
    print(f"  ✓ reconstruct_latest: contract holds")

def test_build_mutation_audit_contract():
    """Data flow contract: build_mutation_audit(root) → output."""
    from src.u_prc_s016_v001 import build_mutation_audit
    # smoke test: function exists and is callable
    assert build_mutation_audit.__name__ == "build_mutation_audit"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_mutation_audit(root)
    assert result is not None, "build_mutation_audit returned None"
    print(f"  ✓ build_mutation_audit: contract holds")

def test_get_latest_composition_contract():
    """Data flow contract: get_latest_composition(root, n) → output."""
    from src.u_prc_s016_v001 import get_latest_composition
    # smoke test: function exists and is callable
    assert get_latest_composition.__name__ == "get_latest_composition"
    print(f"  ✓ get_latest_composition: contract holds")

def test_track_copilot_prompt_mutations_contract():
    """Data flow contract: track_copilot_prompt_mutations(root) → output."""
    from src.u_prc_s016_v001 import track_copilot_prompt_mutations
    # smoke test: function exists and is callable
    assert track_copilot_prompt_mutations.__name__ == "track_copilot_prompt_mutations"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = track_copilot_prompt_mutations(root)
    assert result is not None, "track_copilot_prompt_mutations returned None"
    print(f"  ✓ track_copilot_prompt_mutations: contract holds")

def run_interlink_test():
    """Run all interlink checks for u_prc_s016_v001."""
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
    print(f"  u_prc_s016_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
