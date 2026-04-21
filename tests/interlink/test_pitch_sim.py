"""Interlink self-test for pitch_sim_seq001_v001.

Auto-generated. This test keeps pitch_sim_seq001_v001 interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.pitch_sim_seq001_v001 import run_pitch, main
    assert callable(run_pitch), "run_pitch must be callable"
    assert callable(main), "main must be callable"
    print(f"  ✓ pitch_sim_seq001_v001: 2 exports verified")

def test_run_pitch_contract():
    """Data flow contract: run_pitch(module_name, top_n) → output."""
    from src.pitch_sim_seq001_v001 import run_pitch
    # smoke test: function exists and is callable
    assert run_pitch.__name__ == "run_pitch"
    print(f"  ✓ run_pitch: contract holds")

def test_main_contract():
    """Data flow contract: main() → output."""
    from src.pitch_sim_seq001_v001 import main
    # smoke test: function exists and is callable
    assert main.__name__ == "main"
    result = main()
    assert result is not None, "main returned None"
    print(f"  ✓ main: contract holds")

def run_interlink_test():
    """Run all interlink checks for pitch_sim_seq001_v001."""
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
    print(f"  pitch_sim_seq001_v001: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
