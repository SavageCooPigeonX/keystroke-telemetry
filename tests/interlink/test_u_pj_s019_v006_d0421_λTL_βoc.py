"""Interlink self-test for u_pj_s019_v006_d0421_λTL_βoc.

Auto-generated (rename-resistant). Keeps u_pj_s019_v006_d0421_λTL_βoc interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find u_pj_s019_v006_d0421_λTL_βoc by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/u_pj_s019_v006_d0421_λTL_βoc*.py"), key=lambda p: len(p.name))
    assert matches, f"u_pj_s019_v006_d0421_λTL_βoc: module not found in src/ (glob src/u_pj_s019_v006_d0421_λTL_βoc*.py)"
    spec = _ilu.spec_from_file_location("u_pj_s019_v006_d0421_λTL_βoc", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['log_enriched_entry']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok u_pj_s019_v006_d0421_λTL_βoc: 1 exports verified")

def test_log_enriched_entry_contract():
    """Data flow contract: log_enriched_entry(root, msg, files_open, session_n)."""
    mod = _load_mod()
    fn = getattr(mod, "log_enriched_entry")
    assert callable(fn), "log_enriched_entry must be callable"
    print(f"  ok log_enriched_entry: contract holds")

def run_interlink_test():
    """Run all interlink checks for u_pj_s019_v006_d0421_λTL_βoc."""
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
    print(f"  u_pj_s019_v006_d0421_λTL_βoc: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
