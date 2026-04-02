# @pigeon: seq=001 | role=models | depends=[] | exports=[ExecutionEvent,Electron] | tokens=~350
"""Dataclasses for execution telemetry — isomorphic to keystroke models."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 64 lines | ~424 tokens
# DESC:   isomorphic_to_keystroke_models
# INTENT: pigeon_brain_system
# LAST:   2026-03-23 @ 465cbfa
# SESSIONS: 1
# ──────────────────────────────────────────────

from dataclasses import dataclass, field
from enum import Enum

SCHEMA_VERSION = "execution_telemetry/v1"


class EventType(str, Enum):
    START = "start"
    CALL = "call"
    RETURN = "return"
    ERROR = "error"
    TIMEOUT = "timeout"
    LOOP = "loop"


class ElectronStatus(str, Enum):
    PENDING = "pending"
    FLOWING = "flowing"
    BLOCKED = "blocked"
    STALLED = "stalled"
    LOOPING = "looping"
    DEAD = "dead"
    COMPLETE = "complete"


class DeathCause(str, Enum):
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    LOOP = "loop"
    MAX_ATTEMPTS = "max_attempts"
    STALE_IMPORT = "stale_import"


@dataclass
class ExecutionEvent:
    """Single event in an electron's lifecycle — like KeyEvent for agents."""
    schema: str = SCHEMA_VERSION
    timestamp_ms: int = 0
    event_type: str = "call"
    from_file: str = ""
    to_file: str = ""
    job_id: str = ""
    status: str = "in_progress"
    delta_ms: int = 0
    context: dict = field(default_factory=dict)


@dataclass
class Electron:
    """A tracked unit of intent flowing through the graph — like MessageDraft."""
    job_id: str = ""
    status: str = "pending"
    birth_ms: int = 0
    last_event_ms: int = 0
    path: list = field(default_factory=list)       # files visited in order
    events: list = field(default_factory=list)      # all events
    death_cause: str = ""
    total_calls: int = 0
    total_errors: int = 0
    loop_count: int = 0
    latency_score: float = 0.0                      # like hesitation_score
