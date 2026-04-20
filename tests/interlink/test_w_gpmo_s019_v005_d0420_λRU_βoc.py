"""Interlink self-test for w_gpmo_s019_v005_d0420_λRU_βoc.

Auto-generated. This test keeps w_gpmo_s019_v005_d0420_λRU_βoc interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from pigeon_compiler.git_plugin.w_gpmo_s019_v005_d0420_λRU_βoc import run
    assert callable(run), "run must be callable"
    print(f"  ✓ w_gpmo_s019_v005_d0420_λRU_βoc: 1 exports verified")

def test_run_contract():
    """Data flow contract: run() → output."""
    from pigeon_compiler.git_plugin.w_gpmo_s019_v005_d0420_λRU_βoc import run
    # smoke test: function exists and is callable
    assert run.__name__ == "run"
    result = run()
    assert result is not None, "run returned None"
    print(f"  ✓ run: contract holds")

def run_interlink_test():
    """Run all interlink checks for w_gpmo_s019_v005_d0420_λRU_βoc."""
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
    print(f"  w_gpmo_s019_v005_d0420_λRU_βoc: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
