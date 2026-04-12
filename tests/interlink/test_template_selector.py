"""Interlink self-test for template_selector.

Auto-generated. This test keeps template_selector interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.template_selector import detect_mode, hydrate_templates, inject_active_template
    assert callable(detect_mode), "detect_mode must be callable"
    assert callable(hydrate_templates), "hydrate_templates must be callable"
    assert callable(inject_active_template), "inject_active_template must be callable"
    print(f"  ✓ template_selector: 3 exports verified")

def test_detect_mode_contract():
    """Data flow contract: detect_mode(root) → output."""
    from src.template_selector import detect_mode
    # smoke test: function exists and is callable
    assert detect_mode.__name__ == "detect_mode"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = detect_mode(root)
    assert result is not None, "detect_mode returned None"
    print(f"  ✓ detect_mode: contract holds")

def test_hydrate_templates_contract():
    """Data flow contract: hydrate_templates(root) → output."""
    from src.template_selector import hydrate_templates
    # smoke test: function exists and is callable
    assert hydrate_templates.__name__ == "hydrate_templates"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = hydrate_templates(root)
    assert result is not None, "hydrate_templates returned None"
    print(f"  ✓ hydrate_templates: contract holds")

def test_inject_active_template_contract():
    """Data flow contract: inject_active_template(root) → output."""
    from src.template_selector import inject_active_template
    # smoke test: function exists and is callable
    assert inject_active_template.__name__ == "inject_active_template"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = inject_active_template(root)
    assert result is not None, "inject_active_template returned None"
    print(f"  ✓ inject_active_template: contract holds")

def run_interlink_test():
    """Run all interlink checks for template_selector."""
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
    print(f"  template_selector: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
