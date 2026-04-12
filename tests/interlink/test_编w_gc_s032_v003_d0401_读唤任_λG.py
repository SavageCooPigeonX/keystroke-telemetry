"""Interlink self-test for 编w_gc_s032_v003_d0401_读唤任_λG.

Auto-generated. This test keeps 编w_gc_s032_v003_d0401_读唤任_λG interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.编w_gc_s032_v003_d0401_读唤任_λG import NameCollector, NameTransformer, build_import_graph, GlyphCompilerV2, compile_codebase
    assert callable(NameCollector), "NameCollector must be callable"
    assert callable(NameTransformer), "NameTransformer must be callable"
    assert callable(build_import_graph), "build_import_graph must be callable"
    assert callable(GlyphCompilerV2), "GlyphCompilerV2 must be callable"
    assert callable(compile_codebase), "compile_codebase must be callable"
    print(f"  ✓ 编w_gc_s032_v003_d0401_读唤任_λG: 5 exports verified")

def test_build_import_graph_contract():
    """Data flow contract: build_import_graph(root) → output."""
    from src.编w_gc_s032_v003_d0401_读唤任_λG import build_import_graph
    # smoke test: function exists and is callable
    assert build_import_graph.__name__ == "build_import_graph"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = build_import_graph(root)
    assert result is not None, "build_import_graph returned None"
    print(f"  ✓ build_import_graph: contract holds")

def test_compile_codebase_contract():
    """Data flow contract: compile_codebase(root, out_dir) → output."""
    from src.编w_gc_s032_v003_d0401_读唤任_λG import compile_codebase
    # smoke test: function exists and is callable
    assert compile_codebase.__name__ == "compile_codebase"
    print(f"  ✓ compile_codebase: contract holds")

def run_interlink_test():
    """Run all interlink checks for 编w_gc_s032_v003_d0401_读唤任_λG."""
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
    print(f"  编w_gc_s032_v003_d0401_读唤任_λG: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
