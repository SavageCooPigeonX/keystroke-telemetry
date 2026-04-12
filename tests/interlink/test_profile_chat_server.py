"""Interlink self-test for profile_chat_server.

Auto-generated. This test keeps profile_chat_server interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.profile_chat_server import ChatHandler, ThreadedHTTPServer, main
    assert callable(ChatHandler), "ChatHandler must be callable"
    assert callable(ThreadedHTTPServer), "ThreadedHTTPServer must be callable"
    assert callable(main), "main must be callable"
    print(f"  ✓ profile_chat_server: 3 exports verified")

def test_main_contract():
    """Data flow contract: main() → output."""
    from src.profile_chat_server import main
    # smoke test: function exists and is callable
    assert main.__name__ == "main"
    result = main()
    assert result is not None, "main returned None"
    print(f"  ✓ main: contract holds")

def run_interlink_test():
    """Run all interlink checks for profile_chat_server."""
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
    print(f"  profile_chat_server: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
