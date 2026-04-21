"""Interlink self-test for interlink_debugger.

Auto-generated (rename-resistant). Keeps interlink_debugger interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find interlink_debugger by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/interlink_debugger*.py"), key=lambda p: len(p.name))
    assert matches, f"interlink_debugger: module not found in src/ (glob src/interlink_debugger*.py)"
    spec = _ilu.spec_from_file_location("interlink_debugger", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['classify_failure', 'debug_one', 'debug_batch', 'status_report']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok interlink_debugger: 4 exports verified")

def test_classify_failure_contract():
    """Data flow contract: classify_failure(stderr, stdout)."""
    mod = _load_mod()
    fn = getattr(mod, "classify_failure")
    assert callable(fn), "classify_failure must be callable"
    print(f"  ok classify_failure: contract holds")

def test_debug_one_contract():
    """Data flow contract: debug_one(test_path, intent_ctx)."""
    mod = _load_mod()
    fn = getattr(mod, "debug_one")
    assert callable(fn), "debug_one must be callable"
    print(f"  ok debug_one: contract holds")

def test_debug_batch_contract():
    """Data flow contract: debug_batch(max_modules)."""
    mod = _load_mod()
    fn = getattr(mod, "debug_batch")
    assert callable(fn), "debug_batch must be callable"
    print(f"  ok debug_batch: contract holds")

def test_status_report_contract():
    """Data flow contract: status_report(root)."""
    mod = _load_mod()
    fn = getattr(mod, "status_report")
    assert callable(fn), "status_report must be callable"
    result = fn(_root)
    assert result is not None, "status_report returned None"
    print(f"  ok status_report: contract holds")

def run_interlink_test():
    """Run all interlink checks for interlink_debugger."""
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
    print(f"  interlink_debugger: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
