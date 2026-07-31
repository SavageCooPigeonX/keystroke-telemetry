"""Interlink self-test for codex_compat_build_parser.

Auto-generated (rename-resistant). Keeps codex_compat_build_parser interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
from codex_compat.codex_compat_seq043_v001 import build_parser

def _load_mod():
    """Return the split parser module through its stable package."""
    import codex_compat.codex_compat_seq043_v001 as module

    return module

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['build_parser']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok codex_compat_build_parser: 1 exports verified")

def test_build_parser_contract():
    """Data flow contract: build_parser()."""
    mod = _load_mod()
    fn = getattr(mod, "build_parser")
    assert callable(fn), "build_parser must be callable"
    result = build_parser()
    assert result is not None, "build_parser returned None"
    print(f"  ok build_parser: contract holds")

def run_interlink_test():
    """Run all interlink checks for codex_compat_build_parser."""
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
    print(f"  codex_compat_build_parser: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
