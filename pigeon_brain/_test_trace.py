"""Quick smoke test for the trace hook."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from pigeon_brain.trace_hook_seq011_v001 import start_trace, stop_trace, peek_recent

root = Path(".")
start_trace(root)

# Import some pigeon modules to trigger trace events
try:
    from src.timestamp_utils_seq001_v001_d0314__millisecond_epoch_timestamp_utility_lc_pulse_telemetry_prompt import _now_ms
    _now_ms()
except Exception:
    pass

try:
    from src.models_seq002_v001_d0314__dataclasses_for_keystroke_events_and_lc_pulse_telemetry_prompt import KeyEvent
except Exception:
    pass

stop_trace()

events = peek_recent(50)
print(f"Captured {len(events)} trace events")

modules_seen = set()
for ev in events:
    m = ev.get("module", "?")
    modules_seen.add(m)

print(f"Modules touched: {len(modules_seen)}")
for m in sorted(modules_seen):
    short = m.split("_seq")[0] if "_seq" in m else m
    count = sum(1 for e in events if e.get("module") == m)
    print(f"  {short}: {count} events")

if events:
    print(f"\nSample event:")
    ev = events[0]
    for k, v in ev.items():
        print(f"  {k}: {v}")
