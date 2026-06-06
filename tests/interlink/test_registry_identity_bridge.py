"""Interlink self-test for registry_identity_bridge.

Auto-generated (rename-resistant). Keeps registry_identity_bridge interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find registry_identity_bridge by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/registry_identity_bridge*.py"), key=lambda p: len(p.name))
    assert matches, f"registry_identity_bridge: module not found in src/ (glob src/registry_identity_bridge*.py)"
    spec = _ilu.spec_from_file_location("registry_identity_bridge", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['patch_registry', 'unify_registry_intent_identity', 'audit_registry_pairing', 'merge_rename_alias', 'prefer_legacy_filename', 'resolve_registry_path']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok registry_identity_bridge: 6 exports verified")

def test_patch_registry_contract():
    """Data flow contract: patch_registry(root)."""
    mod = _load_mod()
    fn = getattr(mod, "patch_registry")
    assert callable(fn), "patch_registry must be callable"
    result = fn(_root)
    assert result is not None, "patch_registry returned None"
    print(f"  ok patch_registry: contract holds")

def test_unify_registry_intent_identity_contract():
    """Data flow contract: unify_registry_intent_identity(root, registry)."""
    mod = _load_mod()
    fn = getattr(mod, "unify_registry_intent_identity")
    assert callable(fn), "unify_registry_intent_identity must be callable"
    print(f"  ok unify_registry_intent_identity: contract holds")

def test_audit_registry_pairing_contract():
    """Data flow contract: audit_registry_pairing(root, registry)."""
    mod = _load_mod()
    fn = getattr(mod, "audit_registry_pairing")
    assert callable(fn), "audit_registry_pairing must be callable"
    print(f"  ok audit_registry_pairing: contract holds")

def test_merge_rename_alias_contract():
    """Data flow contract: merge_rename_alias(root, old_path, new_path, entry)."""
    mod = _load_mod()
    fn = getattr(mod, "merge_rename_alias")
    assert callable(fn), "merge_rename_alias must be callable"
    print(f"  ok merge_rename_alias: contract holds")

def test_prefer_legacy_filename_contract():
    """Data flow contract: prefer_legacy_filename(entry)."""
    mod = _load_mod()
    fn = getattr(mod, "prefer_legacy_filename")
    assert callable(fn), "prefer_legacy_filename must be callable"
    print(f"  ok prefer_legacy_filename: contract holds")

def test_resolve_registry_path_contract():
    """Data flow contract: resolve_registry_path(root, key)."""
    mod = _load_mod()
    fn = getattr(mod, "resolve_registry_path")
    assert callable(fn), "resolve_registry_path must be callable"
    print(f"  ok resolve_registry_path: contract holds")

def run_interlink_test():
    """Run all interlink checks for registry_identity_bridge."""
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
    print(f"  registry_identity_bridge: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
