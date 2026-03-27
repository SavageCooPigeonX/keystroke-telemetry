"""backward_seq007_loss_compute_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 17 lines | ~187 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from typing import Any
import re

def compute_loss(journal_entry: dict[str, Any]) -> float:
    """Composite loss from a prompt journal entry. Lower is better (0.0–1.0)."""
    signals = journal_entry.get("signals", {})
    rework = journal_entry.get("rework_score", 0.0)
    del_ratio = signals.get("deletion_ratio", 0.0)
    state = journal_entry.get("cognitive_state", "unknown")
    frustration = 1.0 if state in STATE_FRUSTRATION else 0.0
    ignored = max(del_ratio, rework) * 0.5
    loss = rework * 0.4 + del_ratio * 0.3 + frustration * 0.2 + ignored * 0.1
    return min(max(loss, 0.0), 1.0)


STATE_FRUSTRATION = {"frustrated", "confused", "struggling"}
