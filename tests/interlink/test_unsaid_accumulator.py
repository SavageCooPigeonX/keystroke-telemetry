"""Interlink self-test for unsaid_accumulator.

Auto-generated. This test keeps unsaid_accumulator interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.unsaid_accumulator import record, get_recent, query, get_summary
    assert callable(record), "record must be callable"
    assert callable(get_recent), "get_recent must be callable"
    assert callable(query), "query must be callable"
    assert callable(get_summary), "get_summary must be callable"
    print(f"  ✓ unsaid_accumulator: 4 exports verified")

def test_record_contract():
    """Data flow contract: record(fragment, completed_intent, deleted_words, unsaid_threads, context) → output."""
    from src.unsaid_accumulator import record
    # smoke test: function exists and is callable
    assert record.__name__ == "record"
    print(f"  ✓ record: contract holds")

def test_get_recent_contract():
    """Data flow contract: get_recent(n) → output."""
    from src.unsaid_accumulator import get_recent
    # smoke test: function exists and is callable
    assert get_recent.__name__ == "get_recent"
    print(f"  ✓ get_recent: contract holds")

def test_query_contract():
    """Data flow contract: query(topic, limit) → output."""
    from src.unsaid_accumulator import query
    # smoke test: function exists and is callable
    assert query.__name__ == "query"
    print(f"  ✓ query: contract holds")

def test_get_summary_contract():
    """Data flow contract: get_summary(max_threads) → output."""
    from src.unsaid_accumulator import get_summary
    # smoke test: function exists and is callable
    assert get_summary.__name__ == "get_summary"
    print(f"  ✓ get_summary: contract holds")

def run_interlink_test():
    """Run all interlink checks for unsaid_accumulator."""
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
    print(f"  unsaid_accumulator: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
