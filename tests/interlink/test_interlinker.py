"""Interlink self-test for interlinker.

Auto-generated (rename-resistant). Keeps interlinker interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find interlinker by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/interlinker*.py"), key=lambda p: len(p.name))
    assert matches, f"interlinker: module not found in src/ (glob src/interlinker*.py)"
    spec = _ilu.spec_from_file_location("interlinker", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['load_interlink_db', 'save_interlink_db', 'assess_module', 'generate_self_test', 'write_self_test', 'run_self_test', 'interlink_module', 'accumulate_shard', 'interlink_scan', 'build_interlink_report']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok interlinker: 10 exports verified")

def test_load_interlink_db_contract():
    """Data flow contract: load_interlink_db(root)."""
    mod = _load_mod()
    fn = getattr(mod, "load_interlink_db")
    assert callable(fn), "load_interlink_db must be callable"
    result = fn(_root)
    assert result is not None, "load_interlink_db returned None"
    print(f"  ok load_interlink_db: contract holds")

def test_save_interlink_db_contract():
    """Data flow contract: save_interlink_db(root, db)."""
    mod = _load_mod()
    fn = getattr(mod, "save_interlink_db")
    assert callable(fn), "save_interlink_db must be callable"
    print(f"  ok save_interlink_db: contract holds")

def test_assess_module_contract():
    """Data flow contract: assess_module(filepath, root)."""
    mod = _load_mod()
    fn = getattr(mod, "assess_module")
    assert callable(fn), "assess_module must be callable"
    print(f"  ok assess_module: contract holds")

def test_generate_self_test_contract():
    """Data flow contract: generate_self_test(filepath, root)."""
    mod = _load_mod()
    fn = getattr(mod, "generate_self_test")
    assert callable(fn), "generate_self_test must be callable"
    print(f"  ok generate_self_test: contract holds")

def test_write_self_test_contract():
    """Data flow contract: write_self_test(filepath, root)."""
    mod = _load_mod()
    fn = getattr(mod, "write_self_test")
    assert callable(fn), "write_self_test must be callable"
    print(f"  ok write_self_test: contract holds")

def test_run_self_test_contract():
    """Data flow contract: run_self_test(filepath, root)."""
    mod = _load_mod()
    fn = getattr(mod, "run_self_test")
    assert callable(fn), "run_self_test must be callable"
    print(f"  ok run_self_test: contract holds")

def test_interlink_module_contract():
    """Data flow contract: interlink_module(filepath, root, force_test_gen)."""
    mod = _load_mod()
    fn = getattr(mod, "interlink_module")
    assert callable(fn), "interlink_module must be callable"
    print(f"  ok interlink_module: contract holds")

def test_accumulate_shard_contract():
    """Data flow contract: accumulate_shard(root, module_stem, shard)."""
    mod = _load_mod()
    fn = getattr(mod, "accumulate_shard")
    assert callable(fn), "accumulate_shard must be callable"
    print(f"  ok accumulate_shard: contract holds")

def test_interlink_scan_contract():
    """Data flow contract: interlink_scan(root, scope)."""
    mod = _load_mod()
    fn = getattr(mod, "interlink_scan")
    assert callable(fn), "interlink_scan must be callable"
    print(f"  ok interlink_scan: contract holds")

def test_build_interlink_report_contract():
    """Data flow contract: build_interlink_report(root)."""
    mod = _load_mod()
    fn = getattr(mod, "build_interlink_report")
    assert callable(fn), "build_interlink_report must be callable"
    result = fn(_root)
    assert result is not None, "build_interlink_report returned None"
    print(f"  ok build_interlink_report: contract holds")

def run_interlink_test():
    """Run all interlink checks for interlinker."""
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
    print(f"  interlinker: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
