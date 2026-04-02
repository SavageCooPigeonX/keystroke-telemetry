"""drift_seq003_baseline_store_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v003 | 31 lines | ~299 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 2
# ──────────────────────────────────────────────

class BaselineStore:
    """In-memory operator baseline storage.

    Override fetch_history() to pull from your database instead.
    """

    def __init__(self):
        self._sessions: dict = {}  # operator_id -> [summary_dicts]

    def record(self, operator_id: str, summary: dict):
        """Record a message summary for baseline computation."""
        if operator_id not in self._sessions:
            self._sessions[operator_id] = []
        self._sessions[operator_id].append(summary)
        # Keep last 200
        if len(self._sessions[operator_id]) > 200:
            self._sessions[operator_id] = self._sessions[operator_id][-200:]

    def fetch_history(self, operator_id: str, limit: int = 200) -> list:
        """Fetch historic summaries for an operator."""
        return (self._sessions.get(operator_id) or [])[-limit:]
