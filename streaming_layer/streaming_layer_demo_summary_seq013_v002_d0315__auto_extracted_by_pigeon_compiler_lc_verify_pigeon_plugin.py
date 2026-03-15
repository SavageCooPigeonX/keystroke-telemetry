"""streaming_layer_demo_summary_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v002 | 42 lines | ~365 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import json

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
