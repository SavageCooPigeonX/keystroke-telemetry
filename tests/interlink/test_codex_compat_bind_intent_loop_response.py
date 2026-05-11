"""Interlink self-test for codex_compat_bind_intent_loop_response.

Auto-generated (rename-resistant). Keeps codex_compat_bind_intent_loop_response interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find codex_compat_bind_intent_loop_response by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/codex_compat_bind_intent_loop_response*.py"), key=lambda p: len(p.name))
    assert matches, f"codex_compat_bind_intent_loop_response: module not found in src/ (glob src/codex_compat_bind_intent_loop_response*.py)"
    spec = _ilu.spec_from_file_location("codex_compat_bind_intent_loop_response", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    print(f"  ok codex_compat_bind_intent_loop_response: module loads")

def run_interlink_test():
    """Run all interlink checks for codex_compat_bind_intent_loop_response."""
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
    print(f"  codex_compat_bind_intent_loop_response: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
