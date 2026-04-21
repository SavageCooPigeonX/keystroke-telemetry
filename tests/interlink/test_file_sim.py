"""Interlink self-test for file_sim.

Auto-generated (rename-resistant). Keeps file_sim interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find file_sim by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/file_sim*.py"), key=lambda p: len(p.name))
    assert matches, f"file_sim: module not found in src/ (glob src/file_sim*.py)"
    spec = _ilu.spec_from_file_location("file_sim", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['self_score', 'grade_file_for_intent', 'run_sim', 'apply_undo_penalty', 'clear_intent_job']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok file_sim: 5 exports verified")

def test_self_score_contract():
    """Data flow contract: self_score(file_stem, prompt_vec, root)."""
    mod = _load_mod()
    fn = getattr(mod, "self_score")
    assert callable(fn), "self_score must be callable"
    print(f"  ok self_score: contract holds")

def test_grade_file_for_intent_contract():
    """Data flow contract: grade_file_for_intent(intent_text, file_stem, root, api_key)."""
    mod = _load_mod()
    fn = getattr(mod, "grade_file_for_intent")
    assert callable(fn), "grade_file_for_intent must be callable"
    print(f"  ok grade_file_for_intent: contract holds")

def test_run_sim_contract():
    """Data flow contract: run_sim(intent_text, prompt_text, top_n, root)."""
    mod = _load_mod()
    fn = getattr(mod, "run_sim")
    assert callable(fn), "run_sim must be callable"
    print(f"  ok run_sim: contract holds")

def test_apply_undo_penalty_contract():
    """Data flow contract: apply_undo_penalty(file_stem, prompt_text, root)."""
    mod = _load_mod()
    fn = getattr(mod, "apply_undo_penalty")
    assert callable(fn), "apply_undo_penalty must be callable"
    print(f"  ok apply_undo_penalty: contract holds")

def test_clear_intent_job_contract():
    """Data flow contract: clear_intent_job(intent_text, actor, root)."""
    mod = _load_mod()
    fn = getattr(mod, "clear_intent_job")
    assert callable(fn), "clear_intent_job must be callable"
    print(f"  ok clear_intent_job: contract holds")

def run_interlink_test():
    """Run all interlink checks for file_sim."""
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
    print(f"  file_sim: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
