"""Interlink self-test for codebase_detector_seq001_v001.

Auto-generated. This test keeps codebase_detector_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.codebase_detector_seq001_v001_seq001_v001 import CodebaseProfile, detect_codebase
    assert callable(CodebaseProfile), "CodebaseProfile must be callable"
    assert callable(detect_codebase), "detect_codebase must be callable"
    print(f"  ✓ codebase_detector_seq001_v001: 2 exports verified")

def test_detect_codebase_contract():
    """Data flow contract: detect_codebase(root) → output."""
    from src.codebase_detector_seq001_v001_seq001_v001 import detect_codebase
    # smoke test: function exists and is callable
    assert detect_codebase.__name__ == "detect_codebase"
    # safe to call with test root
    root = Path(__file__).resolve().parents[2]
    result = detect_codebase(root)
    assert result is not None, "detect_codebase returned None"
    print(f"  ✓ detect_codebase: contract holds")

def run_interlink_test():
    """Run all interlink checks for codebase_detector_seq001_v001."""
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
    print(f"  codebase_detector_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
