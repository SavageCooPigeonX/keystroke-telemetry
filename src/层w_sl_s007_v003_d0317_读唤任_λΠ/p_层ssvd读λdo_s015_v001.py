"""层w_sl_s007_v003_d0317_读唤任_λΠ_demo_orchestrator_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 75 lines | ~562 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json
import time

def run_demo():
    """Run a standalone demo of the streaming server."""
    print("=" * 60)
    print("  STREAMING TELEMETRY DEMO")
    print("=" * 60)

    server = StreamingTelemetryServer(log_dir="demo_logs", port=8787, live_print=False)
    server.start()

    time.sleep(0.5)

    # Simulate typing
    server.start_message()
    buf = _sim_type(server, "Hello world, this is a test of the streaming layer")
    server.submit_message(buf)

    time.sleep(0.3)

    # Simulate typo + correction
    server.start_message()
    buf = _sim_type(server, "Waht is the ")  # typo
    buf = _sim_backspace(server, buf, 12)     # delete it all
    buf = _sim_type(server, "What is the meaning of everything?", buf)
    server.submit_message(buf)

    time.sleep(0.3)

    # Simulate discard
    server.start_message()
    buf = _sim_type(server, "Actually never mind this whole thing")
    server.discard_message(buf)

    time.sleep(0.5)

    # Print dashboard
    print("\n" + server.get_dashboard())

    # Print metrics
    print("\nMETRICS:")
    print(json.dumps(server.metrics.get_summary(), indent=2))

    # Print alerts
    alerts = server.alert_engine.get_alerts()
    if alerts:
        print(f"\nALERTS ({len(alerts)}):")
        for a in alerts:
            print(f"  [{a['severity']}] {a['message']}")

    # Print aggregation snapshot
    print("\nAGGREGATION:")
    snap = server.aggregator.get_snapshot()
    for ws, data in snap["windows"].items():
        print(f"  [{int(ws)//1000}s] events={data['event_count']} wpm={data['estimated_wpm']} "
              f"del%={data['deletion_ratio']}")

    # Test replay
    print("\nREPLAY:")
    replay = SessionReplay(str(server.logger.events_file))
    replay.load()
    print(f"  Events: {replay.event_count()}")
    print(f"  Duration: {replay.duration_ms()}ms")
    msgs = replay.summarize_messages()
    for m in msgs:
        print(f"  [{m['message_id'][:8]}] {m['events']} events, "
              f"del%={m['deletion_ratio']}, dur={m['duration_ms']}ms")

    server.stop()

    print("\n" + "=" * 60)
    print("  DEMO COMPLETE ✓")
    print("=" * 60)
