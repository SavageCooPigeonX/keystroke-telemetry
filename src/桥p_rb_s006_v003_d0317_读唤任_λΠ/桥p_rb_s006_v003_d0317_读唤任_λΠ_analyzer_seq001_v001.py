"""桥p_rb_s006_v003_d0317_读唤任_λΠ_analyzer_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 103 lines | ~1,050 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

class HesitationAnalyzer:
    """Analyzes telemetry summaries to produce hesitation-per-file signals."""

    def __init__(self, summary_dir: str = "logs"):
        self.summary_dir = Path(summary_dir)

    def load_sessions(self) -> list[dict]:
        """Load all session summaries from the log directory."""
        sessions = []
        for f in sorted(self.summary_dir.glob("summary_*.json")):
            with open(f, encoding="utf-8") as fh:
                sessions.append(json.load(fh))
        return sessions

    def compute_operator_profile(self) -> dict:
        """Aggregate across all sessions to build an operator cognitive profile.

        Returns:
            {
                total_sessions, total_messages, total_keystrokes,
                avg_wpm, avg_hesitation_score, discard_rate,
                pause_frequency, deletion_ratio,
                profile_confidence: "low"|"medium"|"high"
            }
        """
        sessions = self.load_sessions()
        all_msgs = []
        for s in sessions:
            all_msgs.extend(s.get("messages", []))

        if not all_msgs:
            return {"total_sessions": 0, "profile_confidence": "none"}

        total_keys = sum(m["total_keystrokes"] for m in all_msgs)
        total_dels = sum(m["total_deletions"] for m in all_msgs)
        total_inserts = sum(m["total_inserts"] for m in all_msgs)
        total_pauses = sum(len(m["typing_pauses"]) for m in all_msgs)
        discards = sum(1 for m in all_msgs if m["deleted"])
        total_duration_ms = sum(
            max(m["end_time_ms"] - m["start_time_ms"], 1) for m in all_msgs
        )

        # WPM estimate: 1 word ≈ 5 chars, only count inserts
        total_duration_min = total_duration_ms / 60_000
        avg_wpm = round((total_inserts / 5) / max(total_duration_min, 0.01), 1)

        hesitation_scores = [m.get("hesitation_score", 0) for m in all_msgs]
        avg_hes = round(sum(hesitation_scores) / len(hesitation_scores), 3) if hesitation_scores else 0

        # Confidence: need ≥3 sessions with ≥5 messages each for "high"
        if len(sessions) >= 5 and len(all_msgs) >= 15:
            confidence = "high"
        elif len(sessions) >= 3 and len(all_msgs) >= 8:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "total_sessions": len(sessions),
            "total_messages": len(all_msgs),
            "total_keystrokes": total_keys,
            "avg_wpm": avg_wpm,
            "avg_hesitation_score": avg_hes,
            "discard_rate": round(discards / max(len(all_msgs), 1), 3),
            "deletion_ratio": round(total_dels / max(total_keys, 1), 3),
            "pause_frequency": round(total_pauses / max(len(all_msgs), 1), 2),
            "profile_confidence": confidence,
        }

    def resistance_signal(self) -> dict:
        """Produce a signal compatible with pigeon compiler's resistance input.

        Maps hesitation metrics → resistance adjustment:
          hesitation_score > 0.5 → suggests file causes cognitive friction
          discard_rate > 0.3 → user frequently abandons messages about this topic
        """
        profile = self.compute_operator_profile()
        if profile["profile_confidence"] == "none":
            return {"adjustment": 0.0, "reason": "no data", "profile": profile}

        hes = profile["avg_hesitation_score"]
        discard = profile["discard_rate"]

        # Resistance bump: high hesitation/discard → file should be split more aggressively
        adjustment = round(min((hes * 0.3) + (discard * 0.2), 0.3), 3)

        reasons = []
        if hes > 0.4:
            reasons.append(f"high hesitation ({hes})")
        if discard > 0.3:
            reasons.append(f"high discard rate ({discard})")
        if profile["deletion_ratio"] > 0.25:
            reasons.append(f"heavy rewriting ({profile['deletion_ratio']})")

        return {
            "adjustment": adjustment,
            "reason": "; ".join(reasons) if reasons else "nominal",
            "profile": profile,
        }
