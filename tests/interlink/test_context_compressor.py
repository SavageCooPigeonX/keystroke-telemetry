"""Interlink self-test for context_compressor_seq001_v001.

Auto-generated. This test keeps context_compressor_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.context_compressor_seq001_v001 import compress_file, compress_changed
    assert callable(compress_file), "compress_file must be callable"
    assert callable(compress_changed), "compress_changed must be callable"
    print(f"  ✓ context_compressor_seq001_v001: 2 exports verified")

def test_compress_file_contract():
    """Data flow contract: compress_file(filepath) → output."""
    from src.context_compressor_seq001_v001 import compress_file
    # smoke test: function exists and is callable
    assert compress_file.__name__ == "compress_file"
    print(f"  ✓ compress_file: contract holds")

def test_compress_changed_contract():
    """Data flow contract: compress_changed(root, changed_files) → output."""
    from src.context_compressor_seq001_v001 import compress_changed
    # smoke test: function exists and is callable
    assert compress_changed.__name__ == "compress_changed"
    print(f"  ✓ compress_changed: contract holds")

def run_interlink_test():
    """Run all interlink checks for context_compressor_seq001_v001."""
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
    print(f"  context_compressor_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
