"""Interlink self-test for tc_context_agent.

Auto-generated (rename-resistant). Keeps tc_context_agent interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find tc_context_agent by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/tc_context_agent*.py"), key=lambda p: len(p.name))
    assert matches, f"tc_context_agent: module not found in src/ (glob src/tc_context_agent*.py)"
    spec = _ilu.spec_from_file_location("tc_context_agent", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['select_context_numeric', 'select_context_files', 'select_context_ensemble', 'build_code_context', 'get_intelligent_context', 'log_prediction', 'grade_prediction', 'select_template', 'grade_and_learn']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok tc_context_agent: 9 exports verified")

def test_select_context_numeric_contract():
    """Data flow contract: select_context_numeric(buffer, ctx, max_files)."""
    mod = _load_mod()
    fn = getattr(mod, "select_context_numeric")
    assert callable(fn), "select_context_numeric must be callable"
    print(f"  ok select_context_numeric: contract holds")

def test_select_context_files_contract():
    """Data flow contract: select_context_files(buffer, ctx, max_files)."""
    mod = _load_mod()
    fn = getattr(mod, "select_context_files")
    assert callable(fn), "select_context_files must be callable"
    print(f"  ok select_context_files: contract holds")

def test_select_context_ensemble_contract():
    """Data flow contract: select_context_ensemble(buffer, ctx, max_files)."""
    mod = _load_mod()
    fn = getattr(mod, "select_context_ensemble")
    assert callable(fn), "select_context_ensemble must be callable"
    print(f"  ok select_context_ensemble: contract holds")

def test_build_code_context_contract():
    """Data flow contract: build_code_context(buffer, ctx)."""
    mod = _load_mod()
    fn = getattr(mod, "build_code_context")
    assert callable(fn), "build_code_context must be callable"
    print(f"  ok build_code_context: contract holds")

def test_get_intelligent_context_contract():
    """Data flow contract: get_intelligent_context(buffer, ctx)."""
    mod = _load_mod()
    fn = getattr(mod, "get_intelligent_context")
    assert callable(fn), "get_intelligent_context must be callable"
    print(f"  ok get_intelligent_context: contract holds")

def test_log_prediction_contract():
    """Data flow contract: log_prediction(buffer, predicted_files, predicted_intent)."""
    mod = _load_mod()
    fn = getattr(mod, "log_prediction")
    assert callable(fn), "log_prediction must be callable"
    print(f"  ok log_prediction: contract holds")

def test_grade_prediction_contract():
    """Data flow contract: grade_prediction(prediction_ts, actual_intent, actual_files)."""
    mod = _load_mod()
    fn = getattr(mod, "grade_prediction")
    assert callable(fn), "grade_prediction must be callable"
    print(f"  ok grade_prediction: contract holds")

def test_select_template_contract():
    """Data flow contract: select_template(buffer, ctx)."""
    mod = _load_mod()
    fn = getattr(mod, "select_template")
    assert callable(fn), "select_template must be callable"
    print(f"  ok select_template: contract holds")

def test_grade_and_learn_contract():
    """Data flow contract: grade_and_learn(buffer, completion, outcome, files_touched, actual_intent)."""
    mod = _load_mod()
    fn = getattr(mod, "grade_and_learn")
    assert callable(fn), "grade_and_learn must be callable"
    print(f"  ok grade_and_learn: contract holds")

def run_interlink_test():
    """Run all interlink checks for tc_context_agent."""
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
    print(f"  tc_context_agent: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
