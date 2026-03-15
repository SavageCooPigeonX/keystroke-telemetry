"""streaming_layer_demo_functions_seq013_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 46 lines | ~394 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json
import time

def _run_demo_print_summary(server):
    import json
    from streaming_server import SessionReplay
    
    print("\n" + server.get_dashboard())
    print("\nMETRICS:")
    print(json.dumps(server.metrics.get_summary(), indent=2))
    
    alerts = server.alert_engine.get_alerts()
    if alerts:
        print(f"\nALERTS ({len(alerts)}):")
        for a in alerts:
            print(f"  [{a['severity']}] {a['message']}")
    
    print("\nAGGREGATION:")
    snap = server.aggregator.get_snapshot()
    for ws, data in snap["windows"].items():
        print(f"  [{int(ws)//1000}s] events={data['event_count']} wpm={data['estimated_wpm']} "
              f"del%={data['deletion_ratio']}")
    
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
def _run_demo_setup_server():
    import time
    from streaming_server import StreamingTelemetryServer
    server = StreamingTelemetryServer(log_dir="demo_logs", port=8787, live_print=False)
    server.start()
    time.sleep(0.5)
    return server
def _run_demo_print_header():
    print("=" * 60)
    print("  STREAMING TELEMETRY DEMO")
    print("=" * 60)
