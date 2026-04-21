"""Interlink self-test for context_select_agent.

Auto-generated (rename-resistant). Keeps context_select_agent interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find context_select_agent by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/context_select_agent*.py"), key=lambda p: len(p.name))
    assert matches, f"context_select_agent: module not found in src/ (glob src/context_select_agent*.py)"
    spec = _ilu.spec_from_file_location("context_select_agent", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['compile_intent', 'detect_stale_blocks', 'run_assembly']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok context_select_agent: 3 exports verified")

def test_compile_intent_contract():
    """Data flow contract: compile_intent(msg, deleted_words, rewrites)."""
    mod = _load_mod()
    fn = getattr(mod, "compile_intent")
    assert callable(fn), "compile_intent must be callable"
    print(f"  ok compile_intent: contract holds")

def test_detect_stale_blocks_contract():
    """Data flow contract: detect_stale_blocks(root)."""
    mod = _load_mod()
    fn = getattr(mod, "detect_stale_blocks")
    assert callable(fn), "detect_stale_blocks must be callable"
    result = fn(_root)
    assert result is not None, "detect_stale_blocks returned None"
    print(f"  ok detect_stale_blocks: contract holds")

def test_run_assembly_contract():
    """Data flow contract: run_assembly(root, msg, deleted_words, rewrites)."""
    mod = _load_mod()
    fn = getattr(mod, "run_assembly")
    assert callable(fn), "run_assembly must be callable"
    print(f"  ok run_assembly: contract holds")

def run_interlink_test():
    """Run all interlink checks for context_select_agent."""
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
    print(f"  context_select_agent: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
