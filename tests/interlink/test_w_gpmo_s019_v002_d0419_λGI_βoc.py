"""Interlink self-test for the active git plugin package."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_import():
    """Package import resolves to the active renamed orchestrator."""
    from pigeon_compiler.git_plugin import run

    assert callable(run), "run must be callable"


def test_run_contract():
    """The active git plugin package exports run()."""
    from pigeon_compiler.git_plugin import run

    assert run.__name__ == "run"


def run_interlink_test():
    """Run all interlink checks for the active git plugin package."""
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as exc:
            print(f"  x {test.__name__}: {exc}")
    total = len(tests)
    status = "INTERLINKED" if passed == total else f"{passed}/{total}"
    print(f"  pigeon_compiler.git_plugin: {status}")
    return passed == total


if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
