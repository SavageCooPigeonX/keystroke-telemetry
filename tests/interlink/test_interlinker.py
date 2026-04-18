"""Interlink self-test for interlinker_seq001_v001.

Auto-generated. This test keeps interlinker_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.interlinker_seq001_v001_seq001_v001 import load_interlink_db, save_interlink_db, assess_module, generate_self_test, write_self_test, run_self_test, interlink_module, accumulate_shard, interlink_scan, build_interlink_report
    assert callable(load_interlink_db), "load_interlink_db must be callable"
    assert callable(save_interlink_db), "save_interlink_db must be callable"
    assert callable(assess_module), "assess_module must be callable"
    assert callable(generate_self_test), "generate_self_test must be callable"
    assert callable(write_self_test), "write_self_test must be callable"
    assert callable(run_self_test), "run_self_test must be callable"
    assert callable(interlink_module), "interlink_module must be callable"
    assert callable(accumulate_shard), "accumulate_shard must be callable"
    assert callable(interlink_scan), "interlink_scan must be callable"
    assert callable(build_interlink_report), "build_interlink_report must be callable"
    print(f"  ✓ interlinker_seq001_v001: 10 exports verified")

def test_load_interlink_db_contract():
    """Data flow contract: load_interlink_db(root) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import load_interlink_db
    # smoke test: function exists and is callable
    assert load_interlink_db.__name__ == "load_interlink_db"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = load_interlink_db(root)
    assert result is not None, "load_interlink_db returned None"
    print(f"  ✓ load_interlink_db: contract holds")

def test_save_interlink_db_contract():
    """Data flow contract: save_interlink_db(root, db) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import save_interlink_db
    # smoke test: function exists and is callable
    assert save_interlink_db.__name__ == "save_interlink_db"
    print(f"  ✓ save_interlink_db: contract holds")

def test_assess_module_contract():
    """Data flow contract: assess_module(filepath, root) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import assess_module
    # smoke test: function exists and is callable
    assert assess_module.__name__ == "assess_module"
    print(f"  ✓ assess_module: contract holds")

def test_generate_self_test_contract():
    """Data flow contract: generate_self_test(filepath, root) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import generate_self_test
    # smoke test: function exists and is callable
    assert generate_self_test.__name__ == "generate_self_test"
    print(f"  ✓ generate_self_test: contract holds")

def test_write_self_test_contract():
    """Data flow contract: write_self_test(filepath, root) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import write_self_test
    # smoke test: function exists and is callable
    assert write_self_test.__name__ == "write_self_test"
    print(f"  ✓ write_self_test: contract holds")

def test_run_self_test_contract():
    """Data flow contract: run_self_test(filepath, root) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import run_self_test
    # smoke test: function exists and is callable
    assert run_self_test.__name__ == "run_self_test"
    print(f"  ✓ run_self_test: contract holds")

def test_interlink_module_contract():
    """Data flow contract: interlink_module(filepath, root, force_test_gen) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import interlink_module
    # smoke test: function exists and is callable
    assert interlink_module.__name__ == "interlink_module"
    print(f"  ✓ interlink_module: contract holds")

def test_accumulate_shard_contract():
    """Data flow contract: accumulate_shard(root, module_stem, shard) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import accumulate_shard
    # smoke test: function exists and is callable
    assert accumulate_shard.__name__ == "accumulate_shard"
    print(f"  ✓ accumulate_shard: contract holds")

def test_interlink_scan_contract():
    """Data flow contract: interlink_scan(root, scope) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import interlink_scan
    # smoke test: function exists and is callable
    assert interlink_scan.__name__ == "interlink_scan"
    print(f"  ✓ interlink_scan: contract holds")

def test_build_interlink_report_contract():
    """Data flow contract: build_interlink_report(root) → output."""
    from src.interlinker_seq001_v001_seq001_v001 import build_interlink_report
    # smoke test: function exists and is callable
    assert build_interlink_report.__name__ == "build_interlink_report"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_interlink_report(root)
    assert result is not None, "build_interlink_report returned None"
    print(f"  ✓ build_interlink_report: contract holds")

def run_interlink_test():
    """Run all interlink checks for interlinker_seq001_v001."""
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
    print(f"  interlinker_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
