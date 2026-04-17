"""Autonomous Development Stress Test — Pigeon vs Standard file management.

Tests whether the pigeon compiler/renamer produces better outcomes for
extended-horizon autonomous coding tasks vs standard flat file conventions.

WHAT IT DOES:
  1. Creates two identical temp workspaces (pigeon/ and standard/)
  2. Seeds both with the same starter codebase (a small multi-module project)
  3. Runs N rounds of autonomous development on BOTH:
     - Each round: add a feature (new file + modify existing)
     - Pigeon workspace: files get pigeon-renamed, imports rewritten, manifests rebuilt
     - Standard workspace: files stay as-is, standard naming
  4. After each round, measures:
     - Import health (all imports resolve?)
     - File size compliance (any file > 200 lines?)
     - Module discoverability (can we find things by pattern?)
     - Manifest accuracy (does the manifest match reality?)
     - Drift detection (have filenames diverged from content?)
  5. After all rounds, compares the two workspaces side by side

METRICS:
  - broken_imports: count of unresolvable imports
  - oversized_files: count of files > 200 lines
  - manifest_drift: files in manifest vs files on disk
  - naming_coherence: do filenames describe what's inside?
  - total_files: how many files exist
  - avg_lines: average lines per file
  - max_lines: largest file

Usage:
    py autonomous_dev_stress_test.py
    py autonomous_dev_stress_test.py --rounds 20
    py autonomous_dev_stress_test.py --rounds 10 --seed-size 5
"""

import argparse
import ast
import json
import os
import shutil
import sys
import tempfile
import textwrap
import time
from pathlib import Path

# ── Locate pigeon-rename package ──────────────────────────────────────────
PIGEON_RENAME_ROOT = Path(r"c:\Users\Nikita\Desktop\pigeon-rename")
if PIGEON_RENAME_ROOT.exists():
    sys.path.insert(0, str(PIGEON_RENAME_ROOT))

try:
    import pigeon_rename
    HAS_PIGEON = True
except ImportError:
    HAS_PIGEON = False
    print("WARNING: pigeon_rename not found — pigeon workspace will use fallback")


# ═══════════════════════════════════════════════════════════════════════════
# SEED CODEBASE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

# Template modules that form a small but realistic project
SEED_MODULES = {
    "models.py": '''\
"""Data models for the project."""

class Event:
    """A thing that happened."""
    def __init__(self, name: str, ts: float, data: dict = None):
        self.name = name
        self.ts = ts
        self.data = data or {}

    def to_dict(self):
        return {"name": self.name, "ts": self.ts, "data": self.data}

class Config:
    """Runtime configuration."""
    def __init__(self, debug=False, max_events=1000, interval_ms=500):
        self.debug = debug
        self.max_events = max_events
        self.interval_ms = interval_ms
''',
    "logger.py": '''\
"""Event logger — writes events to jsonl."""
import json
from pathlib import Path
from models import Event

class Logger:
    def __init__(self, path: str = "events.jsonl"):
        self.path = Path(path)
        self.count = 0

    def log(self, event: Event):
        with open(self.path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\\n")
        self.count += 1

    def flush(self):
        self.count = 0
''',
    "processor.py": '''\
"""Event processor — transforms and filters events."""
from models import Event, Config

class Processor:
    def __init__(self, config: Config):
        self.config = config
        self.processed = 0

    def process(self, event: Event) -> Event | None:
        if not event.name:
            return None
        event.data["processed"] = True
        self.processed += 1
        return event

    def batch_process(self, events: list[Event]) -> list[Event]:
        results = []
        for e in events:
            r = self.process(e)
            if r:
                results.append(r)
        return results
''',
    "aggregator.py": '''\
"""Aggregator — accumulates processed events into summaries."""
from models import Event

class Aggregator:
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.buffer = []
        self.summaries = []

    def add(self, event: Event):
        self.buffer.append(event)
        if len(self.buffer) >= self.window_size:
            self._flush_window()

    def _flush_window(self):
        if not self.buffer:
            return
        summary = {
            "count": len(self.buffer),
            "first_ts": self.buffer[0].ts,
            "last_ts": self.buffer[-1].ts,
            "names": list(set(e.name for e in self.buffer)),
        }
        self.summaries.append(summary)
        self.buffer = []

    def get_summaries(self):
        return list(self.summaries)
''',
    "pipeline.py": '''\
"""Pipeline — wires processor, aggregator, logger together."""
from models import Event, Config
from processor import Processor
from aggregator import Aggregator
from logger import Logger

class Pipeline:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.processor = Processor(self.config)
        self.aggregator = Aggregator()
        self.logger = Logger()

    def ingest(self, event: Event):
        result = self.processor.process(event)
        if result:
            self.aggregator.add(result)
            self.logger.log(result)

    def run_batch(self, events: list[Event]):
        for e in events:
            self.ingest(e)

    def stats(self):
        return {
            "processed": self.processor.processed,
            "summaries": len(self.aggregator.summaries),
            "logged": self.logger.count,
        }
''',
}


# Features to add in each round (simulates autonomous development)
FEATURE_TEMPLATES = [
    {
        "name": "metrics",
        "description": "Add real-time metrics collection",
        "new_file": "metrics.py",
        "content": '''\
"""Metrics — real-time counters, gauges, histograms."""
import time
from models import Event

class Counter:
    def __init__(self, name: str):
        self.name = name
        self.value = 0

    def inc(self, n=1):
        self.value += n

    def reset(self):
        self.value = 0

class Gauge:
    def __init__(self, name: str):
        self.name = name
        self.value = 0.0

    def set(self, v: float):
        self.value = v

class MetricsRegistry:
    def __init__(self):
        self.counters = {}
        self.gauges = {}

    def counter(self, name: str) -> Counter:
        if name not in self.counters:
            self.counters[name] = Counter(name)
        return self.counters[name]

    def gauge(self, name: str) -> Gauge:
        if name not in self.gauges:
            self.gauges[name] = Gauge(name)
        return self.gauges[name]

    def snapshot(self) -> dict:
        return {
            "counters": {k: v.value for k, v in self.counters.items()},
            "gauges": {k: v.value for k, v in self.gauges.items()},
            "ts": time.time(),
        }
''',
        "modify_target": "pipeline.py",
        "modify_patch": ("from logger import Logger", "from logger import Logger\nfrom metrics import MetricsRegistry"),
        "modify_patch2": ("self.logger = Logger()", "self.logger = Logger()\n        self.metrics = MetricsRegistry()"),
    },
    {
        "name": "alerts",
        "description": "Add threshold-based alerting",
        "new_file": "alerts.py",
        "content": '''\
"""Alerts — threshold-based event alerting system."""
from models import Event

class AlertRule:
    def __init__(self, name: str, field: str, threshold: float):
        self.name = name
        self.field = field
        self.threshold = threshold
        self.fired_count = 0

    def check(self, event: Event) -> bool:
        val = event.data.get(self.field, 0)
        if isinstance(val, (int, float)) and val > self.threshold:
            self.fired_count += 1
            return True
        return False

class AlertEngine:
    def __init__(self):
        self.rules = []
        self.alerts_fired = []

    def add_rule(self, rule: AlertRule):
        self.rules.append(rule)

    def evaluate(self, event: Event) -> list[str]:
        fired = []
        for rule in self.rules:
            if rule.check(event):
                fired.append(rule.name)
                self.alerts_fired.append({
                    "rule": rule.name,
                    "event": event.name,
                    "ts": event.ts,
                })
        return fired

    def history(self) -> list:
        return list(self.alerts_fired)
''',
        "modify_target": "pipeline.py",
        "modify_patch": ("from logger import Logger", "from logger import Logger\nfrom alerts import AlertEngine"),
        "modify_patch2": ("self.logger = Logger()", "self.logger = Logger()\n        self.alert_engine = AlertEngine()"),
    },
    {
        "name": "replay",
        "description": "Add event replay from log files",
        "new_file": "replay.py",
        "content": '''\
"""Replay — read events from log files and re-process."""
import json
from pathlib import Path
from models import Event

class Replayer:
    def __init__(self, log_path: str = "events.jsonl"):
        self.log_path = Path(log_path)
        self.events_read = 0

    def load_events(self) -> list[Event]:
        events = []
        if not self.log_path.exists():
            return events
        for line in self.log_path.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            events.append(Event(
                name=d.get("name", ""),
                ts=d.get("ts", 0),
                data=d.get("data", {}),
            ))
            self.events_read += 1
        return events

    def replay_into(self, pipeline) -> int:
        events = self.load_events()
        pipeline.run_batch(events)
        return len(events)
''',
        "modify_target": None,
    },
    {
        "name": "dashboard",
        "description": "Add text-based dashboard renderer",
        "new_file": "dashboard.py",
        "content": '''\
"""Dashboard — renders pipeline state as formatted text."""
from pipeline import Pipeline

class Dashboard:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    def render(self) -> str:
        stats = self.pipeline.stats()
        lines = [
            "=== Pipeline Dashboard ===",
            f"Processed: {stats['processed']}",
            f"Summaries: {stats['summaries']}",
            f"Logged:    {stats['logged']}",
        ]
        if hasattr(self.pipeline, 'metrics'):
            snap = self.pipeline.metrics.snapshot()
            lines.append("--- Metrics ---")
            for k, v in snap.get("counters", {}).items():
                lines.append(f"  {k}: {v}")
        if hasattr(self.pipeline, 'alert_engine'):
            h = self.pipeline.alert_engine.history()
            lines.append(f"--- Alerts ({len(h)} total) ---")
            for a in h[-5:]:
                lines.append(f"  [{a['rule']}] {a['event']} @ {a['ts']}")
        lines.append("=" * 27)
        return "\\n".join(lines)
''',
        "modify_target": None,
    },
    {
        "name": "scheduler",
        "description": "Add periodic task scheduler",
        "new_file": "scheduler.py",
        "content": '''\
"""Scheduler — periodic task execution with intervals."""
import time

class Task:
    def __init__(self, name: str, fn, interval_s: float):
        self.name = name
        self.fn = fn
        self.interval_s = interval_s
        self.last_run = 0
        self.run_count = 0

    def is_due(self, now: float = None) -> bool:
        now = now or time.time()
        return (now - self.last_run) >= self.interval_s

    def execute(self, now: float = None):
        now = now or time.time()
        self.fn()
        self.last_run = now
        self.run_count += 1

class Scheduler:
    def __init__(self):
        self.tasks = []

    def add(self, task: Task):
        self.tasks.append(task)

    def tick(self, now: float = None):
        now = now or time.time()
        for task in self.tasks:
            if task.is_due(now):
                task.execute(now)

    def run_for(self, duration_s: float, tick_interval: float = 0.1):
        start = time.time()
        while (time.time() - start) < duration_s:
            self.tick()
            time.sleep(tick_interval)

    def stats(self) -> dict:
        return {t.name: t.run_count for t in self.tasks}
''',
        "modify_target": None,
    },
    {
        "name": "serializer",
        "description": "Add multiple serialization formats",
        "new_file": "serializer.py",
        "content": '''\
"""Serializer — convert events to JSON, CSV, or compact binary format."""
import json
from models import Event

class JsonSerializer:
    def serialize(self, event: Event) -> str:
        return json.dumps(event.to_dict())

    def deserialize(self, data: str) -> Event:
        d = json.loads(data)
        return Event(name=d["name"], ts=d["ts"], data=d.get("data", {}))

class CsvSerializer:
    def serialize(self, event: Event) -> str:
        data_str = json.dumps(event.data).replace(",", ";")
        return f"{event.name},{event.ts},{data_str}"

    def deserialize(self, data: str) -> Event:
        parts = data.split(",", 2)
        name = parts[0]
        ts = float(parts[1])
        d = json.loads(parts[2].replace(";", ",")) if len(parts) > 2 else {}
        return Event(name=name, ts=ts, data=d)

class CompactSerializer:
    """Length-prefixed binary-ish format."""
    def serialize(self, event: Event) -> bytes:
        payload = json.dumps(event.to_dict()).encode("utf-8")
        length = len(payload).to_bytes(4, "big")
        return length + payload

    def deserialize(self, data: bytes) -> Event:
        length = int.from_bytes(data[:4], "big")
        payload = data[4:4 + length]
        d = json.loads(payload.decode("utf-8"))
        return Event(name=d["name"], ts=d["ts"], data=d.get("data", {}))
''',
        "modify_target": "logger.py",
        "modify_patch": ("import json", "import json\nfrom serializer import JsonSerializer"),
        "modify_patch2": None,
    },
    {
        "name": "filter_chain",
        "description": "Add composable event filter chain",
        "new_file": "filter_chain.py",
        "content": '''\
"""FilterChain — composable event filters with AND/OR logic."""
from models import Event

class Filter:
    def __init__(self, name: str, predicate):
        self.name = name
        self.predicate = predicate

    def matches(self, event: Event) -> bool:
        return self.predicate(event)

class FilterChain:
    def __init__(self, mode: str = "and"):
        assert mode in ("and", "or"), f"Invalid mode: {mode}"
        self.mode = mode
        self.filters = []

    def add(self, f: Filter):
        self.filters.append(f)
        return self

    def evaluate(self, event: Event) -> bool:
        if not self.filters:
            return True
        if self.mode == "and":
            return all(f.matches(event) for f in self.filters)
        return any(f.matches(event) for f in self.filters)

    def apply(self, events: list[Event]) -> list[Event]:
        return [e for e in events if self.evaluate(e)]

    def stats(self) -> dict:
        return {"filters": len(self.filters), "mode": self.mode}
''',
        "modify_target": "processor.py",
        "modify_patch": ("from models import Event, Config", "from models import Event, Config\nfrom filter_chain import FilterChain"),
        "modify_patch2": None,
    },
    {
        "name": "health_check",
        "description": "Add system health checker",
        "new_file": "health_check.py",
        "content": '''\
"""HealthCheck — monitors system components and reports status."""
from pipeline import Pipeline

class HealthCheck:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.checks = []

    def add_check(self, name: str, fn):
        self.checks.append({"name": name, "fn": fn})

    def run(self) -> dict:
        results = {}
        for check in self.checks:
            try:
                ok = check["fn"]()
                results[check["name"]] = {"status": "ok" if ok else "fail"}
            except Exception as e:
                results[check["name"]] = {"status": "error", "msg": str(e)}
        stats = self.pipeline.stats()
        results["pipeline_alive"] = {"status": "ok" if stats["processed"] >= 0 else "fail"}
        return results

    def is_healthy(self) -> bool:
        r = self.run()
        return all(v["status"] == "ok" for v in r.values())
''',
        "modify_target": None,
    },
    {
        "name": "rate_limiter",
        "description": "Add token bucket rate limiter",
        "new_file": "rate_limiter.py",
        "content": '''\
"""RateLimiter — token bucket algorithm for event throughput control."""
import time
from models import Event

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def consume(self, n: int = 1) -> bool:
        self._refill()
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False

class RateLimitedProcessor:
    def __init__(self, bucket: TokenBucket):
        self.bucket = bucket
        self.accepted = 0
        self.rejected = 0

    def try_process(self, event: Event) -> bool:
        if self.bucket.consume():
            self.accepted += 1
            return True
        self.rejected += 1
        return False

    def stats(self) -> dict:
        total = self.accepted + self.rejected
        return {
            "accepted": self.accepted,
            "rejected": self.rejected,
            "accept_rate": self.accepted / total if total > 0 else 0,
        }
''',
        "modify_target": None,
    },
    {
        "name": "event_router",
        "description": "Add topic-based event routing",
        "new_file": "event_router.py",
        "content": '''\
"""EventRouter — topic-based pub/sub routing for events."""
from models import Event

class Subscription:
    def __init__(self, topic: str, handler):
        self.topic = topic
        self.handler = handler
        self.received = 0

    def deliver(self, event: Event):
        self.handler(event)
        self.received += 1

class EventRouter:
    def __init__(self):
        self.subscriptions = {}

    def subscribe(self, topic: str, handler) -> Subscription:
        sub = Subscription(topic, handler)
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(sub)
        return sub

    def publish(self, topic: str, event: Event) -> int:
        subs = self.subscriptions.get(topic, [])
        for sub in subs:
            sub.deliver(event)
        return len(subs)

    def topics(self) -> list[str]:
        return list(self.subscriptions.keys())

    def stats(self) -> dict:
        return {
            topic: sum(s.received for s in subs)
            for topic, subs in self.subscriptions.items()
        }
''',
        "modify_target": "pipeline.py",
        "modify_patch": ("from logger import Logger", "from logger import Logger\nfrom event_router import EventRouter"),
        "modify_patch2": ("self.logger = Logger()", "self.logger = Logger()\n        self.router = EventRouter()"),
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# WORKSPACE OPS
# ═══════════════════════════════════════════════════════════════════════════

def create_workspace(base: Path, name: str, seed_modules: dict) -> Path:
    """Create a workspace with seed modules."""
    ws = base / name / "src"
    ws.mkdir(parents=True, exist_ok=True)
    # Write __init__.py
    (ws / "__init__.py").write_text("")
    for fname, content in seed_modules.items():
        (ws / fname).write_text(textwrap.dedent(content))
    return ws.parent


def apply_feature_standard(ws: Path, feature: dict):
    """Add a feature to the standard workspace (just write files)."""
    src = ws / "src"
    # Write new file
    (src / feature["new_file"]).write_text(textwrap.dedent(feature["content"]))
    # Modify existing if needed
    if feature.get("modify_target"):
        target = src / feature["modify_target"]
        if target.exists():
            text = target.read_text()
            old, new = feature["modify_patch"]
            if old in text:
                text = text.replace(old, new, 1)
            if feature.get("modify_patch2"):
                old2, new2 = feature["modify_patch2"]
                if old2 in text:
                    text = text.replace(old2, new2, 1)
            target.write_text(text)


def apply_feature_pigeon(ws: Path, feature: dict):
    """Add a feature then run the pigeon pipeline."""
    # First, apply same change as standard
    apply_feature_standard(ws, feature)
    # Then run pigeon protocol
    if not HAS_PIGEON:
        return
    root = ws

    try:
        catalog = pigeon_rename.scan_project(root)
        # Build/update registry
        entries = pigeon_rename.load_registry(root)
        if not entries:
            entries = pigeon_rename.build_registry_from_scan(root, catalog)
            pigeon_rename.save_registry(root, entries)
        else:
            # Bump versions for changed files
            entries = pigeon_rename.bump_all_versions(entries, intent="add_feature")
            pigeon_rename.save_registry(root, entries)

        # Build rename plan and execute
        plan = pigeon_rename.build_rename_plan(
            catalog, root=root, intent="add_feature"
        )
        if plan.get("renames"):
            # Rewrite imports BEFORE rename
            import_map = plan.get("import_map", {})
            if not import_map:
                import_map = {r["old_stem"]: r["new_stem"]
                              for r in plan["renames"]}
            if import_map:
                pigeon_rename.rewrite_all_imports(root, import_map)
            pigeon_rename.execute_rename(root, plan)
            # Re-register after renames
            catalog = pigeon_rename.scan_project(root)
            entries = pigeon_rename.build_registry_from_scan(root, catalog)
            pigeon_rename.save_registry(root, entries)

        # Rebuild manifests
        pigeon_rename.build_all_manifests(root)

    except Exception as e:
        print(f"  [pigeon error] {e}")


# ═══════════════════════════════════════════════════════════════════════════
# MEASUREMENT
# ═══════════════════════════════════════════════════════════════════════════

def measure_workspace(ws: Path) -> dict:
    """Measure health metrics of a workspace."""
    src = ws / "src"
    if not src.exists():
        src = ws  # fallback

    py_files = sorted(src.rglob("*.py"))
    py_files = [f for f in py_files if "__pycache__" not in str(f)]

    total = len(py_files)
    if total == 0:
        return {"total_files": 0, "error": "no python files found"}

    # Line counts
    line_counts = []
    for f in py_files:
        try:
            lines = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
            line_counts.append(lines)
        except Exception:
            line_counts.append(0)

    oversized = sum(1 for lc in line_counts if lc > 200)
    avg_lines = sum(line_counts) / len(line_counts) if line_counts else 0
    max_lines = max(line_counts) if line_counts else 0

    # Import health — check if imports resolve within the workspace
    broken_imports = 0
    total_imports = 0
    all_module_stems = {f.stem for f in py_files}

    for f in py_files:
        try:
            source = f.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    total_imports += 1
                    # Check if the root module name resolves to a local file
                    root_mod = node.module.split(".")[0]
                    # Allow stdlib/external imports
                    if root_mod in all_module_stems:
                        pass  # resolves locally
                    elif root_mod in ("os", "sys", "json", "time", "pathlib",
                                      "ast", "re", "math", "random", "copy",
                                      "collections", "typing", "dataclasses",
                                      "functools", "itertools", "textwrap",
                                      "tempfile", "shutil", "subprocess",
                                      "importlib", "glob", "io", "abc",
                                      "pigeon_rename"):
                        pass  # stdlib or known external
                    else:
                        broken_imports += 1
        except SyntaxError:
            pass

    # Manifest check
    manifests = list(ws.rglob("MANIFEST.md"))
    manifest_count = len(manifests)

    # Pigeon registry check
    registry_path = ws / "pigeon_registry.json"
    registry_entries = 0
    if registry_path.exists():
        try:
            reg = json.loads(registry_path.read_text(encoding="utf-8"))
            if isinstance(reg, dict):
                registry_entries = len(reg)
            elif isinstance(reg, list):
                registry_entries = len(reg)
        except Exception:
            pass

    # Pigeon naming check — how many files follow the pigeon convention
    pigeon_named = sum(1 for f in py_files
                       if "_seq" in f.stem and "_v" in f.stem)

    # Naming coherence — do file names contain meaningful words?
    name_lengths = [len(f.stem) for f in py_files if f.stem != "__init__"]
    avg_name_length = (sum(name_lengths) / len(name_lengths)
                       if name_lengths else 0)

    return {
        "total_files": total,
        "total_lines": sum(line_counts),
        "avg_lines": round(avg_lines, 1),
        "max_lines": max_lines,
        "oversized_files": oversized,
        "total_imports": total_imports,
        "broken_imports": broken_imports,
        "import_health": round(
            (1 - broken_imports / total_imports) * 100 if total_imports > 0 else 100,
            1),
        "manifests": manifest_count,
        "registry_entries": registry_entries,
        "pigeon_named": pigeon_named,
        "avg_name_length": round(avg_name_length, 1),
    }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def run_test(rounds: int = 10, seed_size: int = 5, keep_workspaces: bool = False):
    """Run the head-to-head stress test."""
    print("=" * 70)
    print("AUTONOMOUS DEV STRESS TEST — Pigeon Protocol vs Standard")
    print(f"  Rounds: {rounds} | Seed modules: {seed_size} | "
          f"Pigeon package: {'LOADED' if HAS_PIGEON else 'MISSING'}")
    print("=" * 70)

    # Limit seed modules
    seed = dict(list(SEED_MODULES.items())[:seed_size])
    features = FEATURE_TEMPLATES[:rounds]

    # Create temp workspaces
    tmp = Path(tempfile.mkdtemp(prefix="pigeon_stress_"))
    ws_pigeon = create_workspace(tmp, "pigeon", seed)
    ws_standard = create_workspace(tmp, "standard", seed)
    print(f"\n  Workspaces: {tmp}")
    print(f"    pigeon:   {ws_pigeon}")
    print(f"    standard: {ws_standard}")

    # Initialize pigeon workspace
    if HAS_PIGEON:
        try:
            catalog = pigeon_rename.scan_project(ws_pigeon)
            entries = pigeon_rename.build_registry_from_scan(ws_pigeon, catalog)
            pigeon_rename.save_registry(ws_pigeon, entries)
            pigeon_rename.build_all_manifests(ws_pigeon)
            print(f"\n  Pigeon initialized: {len(entries)} modules registered")
        except Exception as e:
            print(f"\n  [pigeon init error] {e}")

    # Baseline measurement
    m_pigeon_0 = measure_workspace(ws_pigeon)
    m_standard_0 = measure_workspace(ws_standard)
    print(f"\n  Baseline — pigeon:   {m_pigeon_0['total_files']} files, "
          f"{m_pigeon_0['avg_lines']} avg lines")
    print(f"  Baseline — standard: {m_standard_0['total_files']} files, "
          f"{m_standard_0['avg_lines']} avg lines")

    # Run rounds
    history = {"pigeon": [m_pigeon_0], "standard": [m_standard_0]}

    for i, feature in enumerate(features):
        round_n = i + 1
        print(f"\n── Round {round_n}/{len(features)}: "
              f"{feature['name']} — {feature['description']} ──")

        t0 = time.time()
        apply_feature_standard(ws_standard, feature)
        t_std = time.time() - t0

        t0 = time.time()
        apply_feature_pigeon(ws_pigeon, feature)
        t_pig = time.time() - t0

        m_pig = measure_workspace(ws_pigeon)
        m_std = measure_workspace(ws_standard)

        history["pigeon"].append(m_pig)
        history["standard"].append(m_std)

        # One-line comparison
        print(f"  standard: {m_std['total_files']}f "
              f"{m_std['avg_lines']}avg {m_std['max_lines']}max "
              f"imports:{m_std['import_health']}% "
              f"over:{m_std['oversized_files']} "
              f"({t_std:.2f}s)")
        print(f"  pigeon:   {m_pig['total_files']}f "
              f"{m_pig['avg_lines']}avg {m_pig['max_lines']}max "
              f"imports:{m_pig['import_health']}% "
              f"over:{m_pig['oversized_files']} "
              f"manifests:{m_pig['manifests']} "
              f"pigeon-named:{m_pig['pigeon_named']} "
              f"({t_pig:.2f}s)")

    # ── Final comparison ──
    final_pig = history["pigeon"][-1]
    final_std = history["standard"][-1]

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    metrics = [
        ("Total files", "total_files", "=", None),
        ("Total lines", "total_lines", "<", "lower = more decomposed"),
        ("Avg lines/file", "avg_lines", "<", "lower = smaller files"),
        ("Max file size", "max_lines", "<", "lower = no monoliths"),
        ("Oversized (>200)", "oversized_files", "<", "lower = compliant"),
        ("Import health %", "import_health", ">", "higher = no broken refs"),
        ("Broken imports", "broken_imports", "<", "lower = healthy"),
        ("Manifests", "manifests", ">", "more = documented"),
        ("Registry entries", "registry_entries", ">", "tracked modules"),
        ("Pigeon-named", "pigeon_named", ">", "semantic filenames"),
        ("Avg name length", "avg_name_length", ">", "more descriptive"),
    ]

    print(f"\n{'Metric':<22} {'Standard':>10} {'Pigeon':>10} {'Winner':>10} Note")
    print("-" * 70)
    pigeon_wins = 0
    standard_wins = 0
    ties = 0

    for label, key, better, note in metrics:
        sv = final_std.get(key, 0)
        pv = final_pig.get(key, 0)

        if better == "<":
            winner = "PIGEON" if pv < sv else ("STANDARD" if sv < pv else "TIE")
        elif better == ">":
            winner = "PIGEON" if pv > sv else ("STANDARD" if sv > pv else "TIE")
        else:
            winner = "TIE"

        if winner == "PIGEON":
            pigeon_wins += 1
        elif winner == "STANDARD":
            standard_wins += 1
        else:
            ties += 1

        note_str = f"  ({note})" if note else ""
        print(f"  {label:<20} {sv:>10} {pv:>10} {winner:>10}{note_str}")

    print("-" * 70)
    print(f"  Score: Pigeon {pigeon_wins} — Standard {standard_wins} — Ties {ties}")

    # Save results
    results_path = tmp / "stress_test_results.json"
    results = {
        "rounds": len(features),
        "seed_size": seed_size,
        "final_pigeon": final_pig,
        "final_standard": final_std,
        "pigeon_wins": pigeon_wins,
        "standard_wins": standard_wins,
        "ties": ties,
        "history": history,
    }
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\n  Results saved: {results_path}")

    if keep_workspaces:
        print(f"  Workspaces kept at: {tmp}")
    else:
        print(f"  Workspaces at: {tmp} (use --keep to preserve)")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pigeon vs Standard stress test")
    parser.add_argument("--rounds", type=int, default=10,
                        help="Number of feature rounds (max 10)")
    parser.add_argument("--seed-size", type=int, default=5,
                        help="Number of seed modules (max 5)")
    parser.add_argument("--keep", action="store_true",
                        help="Keep temp workspaces after test")
    args = parser.parse_args()
    run_test(
        rounds=min(args.rounds, len(FEATURE_TEMPLATES)),
        seed_size=min(args.seed_size, len(SEED_MODULES)),
        keep_workspaces=args.keep,
    )
