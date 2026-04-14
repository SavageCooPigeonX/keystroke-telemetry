"""虫f_bdm_s015_v001_d0410_λFT_bugmanifest_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 17 lines | ~182 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

@dataclass
class BugManifest:
    """A single live bug, tracked across the import graph."""
    bug_id: str
    bug_type: str           # "oc" | "hi" | "de" | "hc" | "dd" | "qn"
    severity: float         # 0.0–1.0 from BUG_SEVERITY
    origin_module: str      # module where the bug was first detected
    affected_chain: list[str] = field(default_factory=list)  # downstream dependents
    notes: str = ""
    resolved: bool = False
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
