"""Interlink self-test for 层w_sl_s007_v003_d0317_读唤任_λΠ.

Auto-generated. This test keeps 层w_sl_s007_v003_d0317_读唤任_λΠ interlinked.
When this passes + pigeon cap + entropy shed → module sleeps.
Module keeps learning via intent shards while sleeping.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def test_import():
    """Module imports without error."""
    from src.层w_sl_s007_v003_d0317_读唤任_λΠ import StreamClient, AggregationBucket, Alert, StreamFormatter, ConnectionPool, EventAggregator, MetricsCollector, AlertEngine, SessionReplay, LiveDashboard, TelemetryHTTPHandler, StreamingTelemetryServer, run_demo
    assert callable(StreamClient), "StreamClient must be callable"
    assert callable(AggregationBucket), "AggregationBucket must be callable"
    assert callable(Alert), "Alert must be callable"
    assert callable(StreamFormatter), "StreamFormatter must be callable"
    assert callable(ConnectionPool), "ConnectionPool must be callable"
    assert callable(EventAggregator), "EventAggregator must be callable"
    assert callable(MetricsCollector), "MetricsCollector must be callable"
    assert callable(AlertEngine), "AlertEngine must be callable"
    assert callable(SessionReplay), "SessionReplay must be callable"
    assert callable(LiveDashboard), "LiveDashboard must be callable"
    assert callable(TelemetryHTTPHandler), "TelemetryHTTPHandler must be callable"
    assert callable(StreamingTelemetryServer), "StreamingTelemetryServer must be callable"
    assert callable(run_demo), "run_demo must be callable"
    print(f"  ✓ 层w_sl_s007_v003_d0317_读唤任_λΠ: 13 exports verified")

def test_run_demo_contract():
    """Data flow contract: run_demo() → output."""
    from src.层w_sl_s007_v003_d0317_读唤任_λΠ import run_demo
    # smoke test: function exists and is callable
    assert run_demo.__name__ == "run_demo"
    result = run_demo()
    assert result is not None, "run_demo returned None"
    print(f"  ✓ run_demo: contract holds")

def run_interlink_test():
    """Run all interlink checks for 层w_sl_s007_v003_d0317_读唤任_λΠ."""
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
    print(f"  层w_sl_s007_v003_d0317_读唤任_λΠ: {status}")
    return passed == total

if __name__ == "__main__":
    success = run_interlink_test()
    raise SystemExit(0 if success else 1)
