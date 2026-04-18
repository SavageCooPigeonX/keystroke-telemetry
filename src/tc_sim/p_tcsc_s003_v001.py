"""tc_sim_seq001_v001_classes_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 49 lines | ~372 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field
import os
import re

@dataclass
class TypingSession:
    """One complete typing session: first keystroke → submit/discard."""
    index: int
    events: list[dict] = field(default_factory=list)
    final_buffer: str = ''
    context: str = 'editor'
    start_ts: int = 0
    end_ts: int = 0
    duration_ms: int = 0
    keystroke_count: int = 0
    backspace_count: int = 0
    pause_points: list[dict] = field(default_factory=list)

    @property
    def deletion_ratio(self) -> float:
        if self.keystroke_count == 0:
            return 0.0
        return self.backspace_count / self.keystroke_count


@dataclass
class PausePoint:
    """A moment where the operator paused long enough to trigger completion."""
    ts: int
    buffer: str
    pause_ms: int
    buffer_after: str  # what the buffer looked like after they resumed typing
    final_text: str    # what was ultimately submitted
    position_pct: float  # how far into the session (0.0-1.0)


@dataclass
class SimResult:
    """Result of replaying one pause point through Gemini."""
    pause: PausePoint
    prediction: str = ''
    latency_ms: int = 0
    # Accuracy metrics
    exact_match: bool = False
    prefix_match_len: int = 0
    word_overlap: float = 0.0
    continuation_captured: str = ''  # what they actually typed after the pause
    context_files: list[str] = field(default_factory=list)
