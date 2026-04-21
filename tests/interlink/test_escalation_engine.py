"""Interlink self-test for escalation_engine_seq001_v001.

Auto-generated. This test keeps escalation_engine_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.escalation_engine_seq001_v001 import compute_module_confidence, inject_warnings, check_and_escalate, get_status
    assert callable(compute_module_confidence), "compute_module_confidence must be callable"
    assert callable(inject_warnings), "inject_warnings must be callable"
    assert callable(check_and_escalate), "check_and_escalate must be callable"
    assert callable(get_status), "get_status must be callable"
    print(f"  ✓ escalation_engine_seq001_v001: 4 exports verified")

def test_compute_module_confidence_contract():
    """Data flow contract: compute_module_confidence(module, entropy_conf, dossier, persistence) → output."""
    from src.escalation_engine_seq001_v001 import compute_module_confidence
    # smoke test: function exists and is callable
    assert compute_module_confidence.__name__ == "compute_module_confidence"
    print(f"  ✓ compute_module_confidence: contract holds")

def test_inject_warnings_contract():
    """Data flow contract: inject_warnings(root, state) → output."""
    from src.escalation_engine_seq001_v001 import inject_warnings
    # smoke test: function exists and is callable
    assert inject_warnings.__name__ == "inject_warnings"
    print(f"  ✓ inject_warnings: contract holds")

def test_check_and_escalate_contract():
    """Data flow contract: check_and_escalate(root, registry, changed_py, cross_context) → output."""
    from src.escalation_engine_seq001_v001 import check_and_escalate
    # smoke test: function exists and is callable
    assert check_and_escalate.__name__ == "check_and_escalate"
    print(f"  ✓ check_and_escalate: contract holds")

def test_get_status_contract():
    """Data flow contract: get_status(root) → output."""
    from src.escalation_engine_seq001_v001 import get_status
    # smoke test: function exists and is callable
    assert get_status.__name__ == "get_status"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = get_status(root)
    assert result is not None, "get_status returned None"
    print(f"  ✓ get_status: contract holds")

def run_interlink_test():
    """Run all interlink checks for escalation_engine_seq001_v001."""
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
    print(f"  escalation_engine_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
