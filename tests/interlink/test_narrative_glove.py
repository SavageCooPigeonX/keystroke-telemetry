"""Interlink self-test for narrative_glove_seq001_v001.

Auto-generated. This test keeps narrative_glove_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.narrative_glove_seq001_v001_seq001_v001 import synthesize, inject_narrative
    assert callable(synthesize), "synthesize must be callable"
    assert callable(inject_narrative), "inject_narrative must be callable"
    print(f"  ✓ narrative_glove_seq001_v001: 2 exports verified")

def test_synthesize_contract():
    """Data flow contract: synthesize(root) → output."""
    from src.narrative_glove_seq001_v001_seq001_v001 import synthesize
    # smoke test: function exists and is callable
    assert synthesize.__name__ == "synthesize"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = synthesize(root)
    assert result is not None, "synthesize returned None"
    print(f"  ✓ synthesize: contract holds")

def test_inject_narrative_contract():
    """Data flow contract: inject_narrative(root) → output."""
    from src.narrative_glove_seq001_v001_seq001_v001 import inject_narrative
    # smoke test: function exists and is callable
    assert inject_narrative.__name__ == "inject_narrative"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = inject_narrative(root)
    assert result is not None, "inject_narrative returned None"
    print(f"  ✓ inject_narrative: contract holds")

def run_interlink_test():
    """Run all interlink checks for narrative_glove_seq001_v001."""
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
    print(f"  narrative_glove_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
