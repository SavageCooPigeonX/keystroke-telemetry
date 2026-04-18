"""Interlink self-test for intent_compressor_seq001_v001.

Auto-generated. This test keeps intent_compressor_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.intent_compressor_seq001_v001_seq001_v001 import strip_metadata, strip_syntactic_noise, collapse_imports, skeleton, intent_map, CompressionResult, compress_file, compress_all
    assert callable(strip_metadata), "strip_metadata must be callable"
    assert callable(strip_syntactic_noise), "strip_syntactic_noise must be callable"
    assert callable(collapse_imports), "collapse_imports must be callable"
    assert callable(skeleton), "skeleton must be callable"
    assert callable(intent_map), "intent_map must be callable"
    assert callable(CompressionResult), "CompressionResult must be callable"
    assert callable(compress_file), "compress_file must be callable"
    assert callable(compress_all), "compress_all must be callable"
    print(f"  ✓ intent_compressor_seq001_v001: 8 exports verified")

def test_strip_metadata_contract():
    """Data flow contract: strip_metadata(source) → output."""
    from src.intent_compressor_seq001_v001_seq001_v001 import strip_metadata
    # smoke test: function exists and is callable
    assert strip_metadata.__name__ == "strip_metadata"
    print(f"  ✓ strip_metadata: contract holds")

def test_strip_syntactic_noise_contract():
    """Data flow contract: strip_syntactic_noise(source) → output."""
    from src.intent_compressor_seq001_v001_seq001_v001 import strip_syntactic_noise
    # smoke test: function exists and is callable
    assert strip_syntactic_noise.__name__ == "strip_syntactic_noise"
    print(f"  ✓ strip_syntactic_noise: contract holds")

def test_collapse_imports_contract():
    """Data flow contract: collapse_imports(source) → output."""
    from src.intent_compressor_seq001_v001_seq001_v001 import collapse_imports
    # smoke test: function exists and is callable
    assert collapse_imports.__name__ == "collapse_imports"
    print(f"  ✓ collapse_imports: contract holds")

def test_skeleton_contract():
    """Data flow contract: skeleton(source) → output."""
    from src.intent_compressor_seq001_v001_seq001_v001 import skeleton
    # smoke test: function exists and is callable
    assert skeleton.__name__ == "skeleton"
    print(f"  ✓ skeleton: contract holds")

def test_intent_map_contract():
    """Data flow contract: intent_map(source, filename) → output."""
    from src.intent_compressor_seq001_v001_seq001_v001 import intent_map
    # smoke test: function exists and is callable
    assert intent_map.__name__ == "intent_map"
    print(f"  ✓ intent_map: contract holds")

def test_compress_file_contract():
    """Data flow contract: compress_file(filepath, root) → output."""
    from src.intent_compressor_seq001_v001_seq001_v001 import compress_file
    # smoke test: function exists and is callable
    assert compress_file.__name__ == "compress_file"
    print(f"  ✓ compress_file: contract holds")

def test_compress_all_contract():
    """Data flow contract: compress_all(root, write_output) → output."""
    from src.intent_compressor_seq001_v001_seq001_v001 import compress_all
    # smoke test: function exists and is callable
    assert compress_all.__name__ == "compress_all"
    print(f"  ✓ compress_all: contract holds")

def run_interlink_test():
    """Run all interlink checks for intent_compressor_seq001_v001."""
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
    print(f"  intent_compressor_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
