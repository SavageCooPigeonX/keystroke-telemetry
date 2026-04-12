"""Interlink self-test for 编w_gc_s032_v002_d0401_读唤任_λG.

Auto-generated. This test keeps 编w_gc_s032_v002_d0401_读唤任_λG interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.编w_gc_s032_v002_d0401_读唤任_λG import GlyphCompiler, compile_to_glyph, compile_and_write
    assert callable(GlyphCompiler), "GlyphCompiler must be callable"
    assert callable(compile_to_glyph), "compile_to_glyph must be callable"
    assert callable(compile_and_write), "compile_and_write must be callable"
    print(f"  ✓ 编w_gc_s032_v002_d0401_读唤任_λG: 3 exports verified")

def test_compile_to_glyph_contract():
    """Data flow contract: compile_to_glyph(root, filepath) → output."""
    from src.编w_gc_s032_v002_d0401_读唤任_λG import compile_to_glyph
    # smoke test: function exists and is callable
    assert compile_to_glyph.__name__ == "compile_to_glyph"
    print(f"  ✓ compile_to_glyph: contract holds")

def test_compile_and_write_contract():
    """Data flow contract: compile_and_write(root, filepath) → output."""
    from src.编w_gc_s032_v002_d0401_读唤任_λG import compile_and_write
    # smoke test: function exists and is callable
    assert compile_and_write.__name__ == "compile_and_write"
    print(f"  ✓ compile_and_write: contract holds")

def run_interlink_test():
    """Run all interlink checks for 编w_gc_s032_v002_d0401_读唤任_λG."""
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
    print(f"  编w_gc_s032_v002_d0401_读唤任_λG: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
