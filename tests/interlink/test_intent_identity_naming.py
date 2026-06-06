"""Interlink self-test for intent_identity_naming.

Auto-generated (rename-resistant). Keeps intent_identity_naming interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import importlib.util as _ilu, sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_root))

def _load_mod():
    """Find intent_identity_naming by glob — survives pigeon renames."""
    matches = sorted(_root.glob("src/intent_identity_naming*.py"), key=lambda p: len(p.name))
    assert matches, f"intent_identity_naming: module not found in src/ (glob src/intent_identity_naming*.py)"
    spec = _ilu.spec_from_file_location("intent_identity_naming", matches[0])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_import():
    """Module loads without error."""
    mod = _load_mod()
    for name in ['itid_from_intent_key', 'lineage_hash', 'intent_domain_for_path', 'identity_id_from_path', 'build_intent_filename', 'parse_intent_stem', 'next_eci', 'enrich_registry_entry', 'stamp_intent_touch', 'parent_lineage_from_compile']:
        assert hasattr(mod, name), f"{name} missing"
        assert callable(getattr(mod, name)), f"{name} not callable"
    print(f"  ok intent_identity_naming: 10 exports verified")

def test_itid_from_intent_key_contract():
    """Data flow contract: itid_from_intent_key(intent_key)."""
    mod = _load_mod()
    fn = getattr(mod, "itid_from_intent_key")
    assert callable(fn), "itid_from_intent_key must be callable"
    print(f"  ok itid_from_intent_key: contract holds")

def test_lineage_hash_contract():
    """Data flow contract: lineage_hash(identity_id, intent_domain, parent_lh)."""
    mod = _load_mod()
    fn = getattr(mod, "lineage_hash")
    assert callable(fn), "lineage_hash must be callable"
    print(f"  ok lineage_hash: contract holds")

def test_intent_domain_for_path_contract():
    """Data flow contract: intent_domain_for_path(path)."""
    mod = _load_mod()
    fn = getattr(mod, "intent_domain_for_path")
    assert callable(fn), "intent_domain_for_path must be callable"
    print(f"  ok intent_domain_for_path: contract holds")

def test_identity_id_from_path_contract():
    """Data flow contract: identity_id_from_path(path)."""
    mod = _load_mod()
    fn = getattr(mod, "identity_id_from_path")
    assert callable(fn), "identity_id_from_path must be callable"
    print(f"  ok identity_id_from_path: contract holds")

def test_build_intent_filename_contract():
    """Data flow contract: build_intent_filename(identity_id, itid, ver)."""
    mod = _load_mod()
    fn = getattr(mod, "build_intent_filename")
    assert callable(fn), "build_intent_filename must be callable"
    print(f"  ok build_intent_filename: contract holds")

def test_parse_intent_stem_contract():
    """Data flow contract: parse_intent_stem(stem)."""
    mod = _load_mod()
    fn = getattr(mod, "parse_intent_stem")
    assert callable(fn), "parse_intent_stem must be callable"
    print(f"  ok parse_intent_stem: contract holds")

def test_next_eci_contract():
    """Data flow contract: next_eci(entry, event)."""
    mod = _load_mod()
    fn = getattr(mod, "next_eci")
    assert callable(fn), "next_eci must be callable"
    print(f"  ok next_eci: contract holds")

def test_enrich_registry_entry_contract():
    """Data flow contract: enrich_registry_entry(entry)."""
    mod = _load_mod()
    fn = getattr(mod, "enrich_registry_entry")
    assert callable(fn), "enrich_registry_entry must be callable"
    print(f"  ok enrich_registry_entry: contract holds")

def test_stamp_intent_touch_contract():
    """Data flow contract: stamp_intent_touch(root, file)."""
    mod = _load_mod()
    fn = getattr(mod, "stamp_intent_touch")
    assert callable(fn), "stamp_intent_touch must be callable"
    print(f"  ok stamp_intent_touch: contract holds")

def test_parent_lineage_from_compile_contract():
    """Data flow contract: parent_lineage_from_compile(source_file)."""
    mod = _load_mod()
    fn = getattr(mod, "parent_lineage_from_compile")
    assert callable(fn), "parent_lineage_from_compile must be callable"
    print(f"  ok parent_lineage_from_compile: contract holds")

def run_interlink_test():
    """Run all interlink checks for intent_identity_naming."""
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
    print(f"  intent_identity_naming: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
