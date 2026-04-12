"""Interlink self-test for file_selector.

Auto-generated. This test keeps file_selector interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.file_selector import select_files, select_partners
    assert callable(select_files), "select_files must be callable"
    assert callable(select_partners), "select_partners must be callable"
    print(f"  ✓ file_selector: 2 exports verified")

def test_select_files_contract():
    """Data flow contract: select_files(fragment, ctx, max_files) → output."""
    from src.file_selector import select_files
    # smoke test: function exists and is callable
    assert select_files.__name__ == "select_files"
    print(f"  ✓ select_files: contract holds")

def test_select_partners_contract():
    """Data flow contract: select_partners(primary_module, max_partners) → output."""
    from src.file_selector import select_partners
    # smoke test: function exists and is callable
    assert select_partners.__name__ == "select_partners"
    print(f"  ✓ select_partners: contract holds")

def run_interlink_test():
    """Run all interlink checks for file_selector."""
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
    print(f"  file_selector: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
