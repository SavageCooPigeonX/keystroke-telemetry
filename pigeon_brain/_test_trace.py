"""Quick smoke test for the trace hook."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from glob import glob
import importlib, os

def _pb_import(pattern, *attrs):
    hits = glob(f'pigeon_brain/{pattern}_v*.py')
    if not hits:
        raise ImportError(f'{pattern}* not found')
    mod = importlib.import_module('pigeon_brain.' + os.path.splitext(os.path.basename(hits[0]))[0])
    return tuple(getattr(mod, a) for a in attrs) if len(attrs) > 1 else getattr(mod, attrs[0])

start_trace, stop_trace, peek_recent = _pb_import('trace_hook_seq011', 'start_trace', 'stop_trace', 'peek_recent')

root = Path(".")
start_trace(root)

# Import some pigeon modules to trigger trace events
try:
    from src._resolve import src_import
    _now_ms = src_import('timestamp_utils_seq001', '_now_ms')
    _now_ms()
except Exception:
    pass

try:
    KeyEvent = src_import('models_seq002', 'KeyEvent')
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
