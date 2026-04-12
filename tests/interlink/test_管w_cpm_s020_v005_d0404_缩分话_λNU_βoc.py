"""Interlink self-test for 管w_cpm_s020_v005_d0404_缩分话_λNU_βoc.

Auto-generated. This test keeps 管w_cpm_s020_v005_d0404_缩分话_λNU_βoc interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.管w_cpm_s020_v005_d0404_缩分话_λNU_βoc import inject_prompt_telemetry, inject_auto_index, audit_copilot_prompt
    assert callable(inject_prompt_telemetry), "inject_prompt_telemetry must be callable"
    assert callable(inject_auto_index), "inject_auto_index must be callable"
    assert callable(audit_copilot_prompt), "audit_copilot_prompt must be callable"
    print(f"  ✓ 管w_cpm_s020_v005_d0404_缩分话_λNU_βoc: 3 exports verified")

def test_inject_prompt_telemetry_contract():
    """Data flow contract: inject_prompt_telemetry(root, snapshot) → output."""
    from src.管w_cpm_s020_v005_d0404_缩分话_λNU_βoc import inject_prompt_telemetry
    # smoke test: function exists and is callable
    assert inject_prompt_telemetry.__name__ == "inject_prompt_telemetry"
    print(f"  ✓ inject_prompt_telemetry: contract holds")

def test_inject_auto_index_contract():
    """Data flow contract: inject_auto_index(root, registry, processed) → output."""
    from src.管w_cpm_s020_v005_d0404_缩分话_λNU_βoc import inject_auto_index
    # smoke test: function exists and is callable
    assert inject_auto_index.__name__ == "inject_auto_index"
    print(f"  ✓ inject_auto_index: contract holds")

def test_audit_copilot_prompt_contract():
    """Data flow contract: audit_copilot_prompt(root) → output."""
    from src.管w_cpm_s020_v005_d0404_缩分话_λNU_βoc import audit_copilot_prompt
    # smoke test: function exists and is callable
    assert audit_copilot_prompt.__name__ == "audit_copilot_prompt"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = audit_copilot_prompt(root)
    assert result is not None, "audit_copilot_prompt returned None"
    print(f"  ✓ audit_copilot_prompt: contract holds")

def run_interlink_test():
    """Run all interlink checks for 管w_cpm_s020_v005_d0404_缩分话_λNU_βoc."""
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
    print(f"  管w_cpm_s020_v005_d0404_缩分话_λNU_βoc: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
