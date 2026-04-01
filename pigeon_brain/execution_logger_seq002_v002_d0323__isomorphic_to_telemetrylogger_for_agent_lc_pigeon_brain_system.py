# @pigeon: seq=002 | role=execution_logger | depends=[models] | exports=[ExecutionLogger] | tokens=~600
"""Execution telemetry logger — isomorphic to TelemetryLogger for agent flows.

Captures per-transition events as files call other files. Each event is
a self-contained JSON block (schema: execution_telemetry/v1). Tracks
electrons (intent units) through their lifecycle.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 157 lines | ~1,556 tokens
# DESC:   isomorphic_to_telemetrylogger_for_agent
# INTENT: pigeon_brain_system
# LAST:   2026-03-23 @ 465cbfa
# SESSIONS: 1
# ──────────────────────────────────────────────

import json
import uuid
import time
from pathlib import Path
from dataclasses import asdict

from .models_seq001_v002_d0323__型层包_isomorphic_to_keystroke_models_lc_pigeon_brain_system import (
    SCHEMA_VERSION, ExecutionEvent, Electron,
    ElectronStatus, EventType, DeathCause,
)

STALL_THRESHOLD_MS = 10_000   # 10s without event = stalled
LOOP_THRESHOLD = 3            # visiting same node 3x = loop


class ExecutionLogger:
    def __init__(self, log_dir: str = "logs/execution", live_print: bool = False):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = uuid.uuid4().hex[:12]
        self.events_file = self.log_dir / f"exec_events_{self.session_id}.jsonl"
        self.summary_file = self.log_dir / f"exec_summary_{self.session_id}.json"
        self.live_print = live_print
        self.electrons: dict[str, Electron] = {}
        self._seq = 0
        self._handle = open(self.events_file, "a", encoding="utf-8")

    def _now(self) -> int:
        return int(time.time() * 1000)

    def start_electron(self, job_id: str = "", context: dict = None) -> str:
        """Birth an electron — a tracked intent entering the graph."""
        if not job_id:
            job_id = uuid.uuid4().hex[:10]
        now = self._now()
        e = Electron(job_id=job_id, status=ElectronStatus.FLOWING,
                     birth_ms=now, last_event_ms=now)
        self.electrons[job_id] = e
        self._emit(EventType.START, "", "", job_id, "in_progress",
                   context or {})
        return job_id

    def log_call(self, from_file: str, to_file: str, job_id: str,
                 context: dict = None) -> None:
        """Log a file→file transition for an electron."""
        e = self.electrons.get(job_id)
        if not e:
            return
        now = self._now()
        delta = now - e.last_event_ms
        e.last_event_ms = now
        e.total_calls += 1
        e.path.append(to_file)
        # Loop detection
        visit_count = e.path.count(to_file)
        if visit_count >= LOOP_THRESHOLD:
            e.loop_count += 1
            e.status = ElectronStatus.LOOPING
        self._emit(EventType.CALL, from_file, to_file, job_id,
                   e.status, context or {}, delta)

    def log_return(self, from_file: str, to_file: str, job_id: str,
                   context: dict = None) -> None:
        """Log a successful return from a call."""
        e = self.electrons.get(job_id)
        if not e:
            return
        now = self._now()
        delta = now - e.last_event_ms
        e.last_event_ms = now
        self._emit(EventType.RETURN, from_file, to_file, job_id,
                   "success", context or {}, delta)

    def log_error(self, file: str, job_id: str, error: str,
                  cause: str = "exception") -> None:
        """Log an electron death by error."""
        e = self.electrons.get(job_id)
        if not e:
            return
        now = self._now()
        e.status = ElectronStatus.DEAD
        e.death_cause = cause
        e.total_errors += 1
        e.last_event_ms = now
        self._emit(EventType.ERROR, file, "", job_id, "fail",
                   {"error": error[:200], "cause": cause},
                   now - e.last_event_ms)

    def complete_electron(self, job_id: str) -> None:
        """Mark an electron as successfully completed."""
        e = self.electrons.get(job_id)
        if not e:
            return
        e.status = ElectronStatus.COMPLETE
        e.last_event_ms = self._now()
        duration = e.last_event_ms - e.birth_ms
        e.latency_score = round(min(1.0, (duration / 60_000) * 0.5 +
                                    e.total_errors * 0.2 +
                                    e.loop_count * 0.15), 3)

    def check_stalls(self) -> list[str]:
        """Find electrons that haven't emitted events recently."""
        now = self._now()
        stalled = []
        for jid, e in self.electrons.items():
            if e.status in (ElectronStatus.DEAD, ElectronStatus.COMPLETE):
                continue
            if now - e.last_event_ms > STALL_THRESHOLD_MS:
                e.status = ElectronStatus.STALLED
                stalled.append(jid)
        return stalled

    def _emit(self, event_type, from_file, to_file, job_id,
              status, context, delta=0):
        self._seq += 1
        block = {
            "schema": SCHEMA_VERSION, "seq": self._seq,
            "session_id": self.session_id, "timestamp_ms": self._now(),
            "event_type": event_type, "from_file": from_file,
            "to_file": to_file, "job_id": job_id,
            "status": status, "delta_ms": delta, "context": context,
        }
        self._handle.write(json.dumps(block) + "\n")
        self._handle.flush()
        if self.live_print:
            print(json.dumps(block, indent=2))

    def write_summary(self) -> dict:
        """Write session summary — like TelemetryLogger._write_summary."""
        electrons = [asdict(e) for e in self.electrons.values()]
        summary = {
            "schema": SCHEMA_VERSION,
            "session_id": self.session_id,
            "total_electrons": len(electrons),
            "alive": sum(1 for e in self.electrons.values()
                         if e.status == ElectronStatus.FLOWING),
            "dead": sum(1 for e in self.electrons.values()
                        if e.status == ElectronStatus.DEAD),
            "complete": sum(1 for e in self.electrons.values()
                           if e.status == ElectronStatus.COMPLETE),
            "electrons": electrons,
        }
        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary

    def close(self):
        self.write_summary()
        self._handle.close()
