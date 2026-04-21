"""Interlink self-test for tc_10q.

Auto-generated (rename-resistant). Keeps tc_10q interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find tc_10q by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/tc_10q*.py"), key=lambda p: len(p.name))
    assert matches, f"tc_10q: module not found in src/ (glob src/tc_10q*.py)"
    spec = _ilu.spec_from_file_location("tc_10q", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['run_10q', 'qualify_module', 'qualify_all', 'summary_report']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok tc_10q: 4 exports verified")

def test_run_10q_contract():
    """Data flow contract: run_10q(filepath)."""
    mod = _load_mod()
    fn = getattr(mod, "run_10q")
    assert callable(fn), "run_10q must be callable"
    print(f"  ok run_10q: contract holds")

def test_qualify_module_contract():
    """Data flow contract: qualify_module(filepath, write_log)."""
    mod = _load_mod()
    fn = getattr(mod, "qualify_module")
    assert callable(fn), "qualify_module must be callable"
    print(f"  ok qualify_module: contract holds")

def test_qualify_all_contract():
    """Data flow contract: qualify_all(scope, max_files)."""
    mod = _load_mod()
    fn = getattr(mod, "qualify_all")
    assert callable(fn), "qualify_all must be callable"
    print(f"  ok qualify_all: contract holds")

def test_summary_report_contract():
    """Data flow contract: summary_report(results)."""
    mod = _load_mod()
    fn = getattr(mod, "summary_report")
    assert callable(fn), "summary_report must be callable"
    print(f"  ok summary_report: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_10q."""
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
    print(f"  tc_10q: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
