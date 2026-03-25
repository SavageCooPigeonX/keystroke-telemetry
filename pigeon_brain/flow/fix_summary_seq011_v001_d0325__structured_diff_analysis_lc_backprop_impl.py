# ┌──────────────────────────────────────────────┐
# │  fix_summary — structured diff analysis        │
# │  pigeon_brain/flow                             │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-25T00:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  initial implementation
# ── /pulse ──
"""
The ground truth extractor. Converts raw git diffs into structured
fix summaries that the backward pass can compare against node predictions.

Pipeline: git diff → parse hunks → classify intent → generate summary
          → link to electron_id if available.

Intent classification is rule-based: import changes → rewrite_import,
function signature changes → rename_function, new guard clauses →
add_guard, etc.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | ~150 lines | ~1,100 tokens
# DESC:   structured_diff_analysis
# INTENT: backprop_impl
# LAST:   2026-03-25
# SESSIONS: 1
# ──────────────────────────────────────────────
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FIX_MEMORY_FILE = "fix_memory.json"

# Intent classification patterns (applied to diff lines)
INTENT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("rewrite_import", re.compile(r"^[+-]\s*(from|import)\s+", re.MULTILINE)),
    ("rename_function", re.compile(r"^[+-]\s*def\s+\w+", re.MULTILINE)),
    ("rename_class", re.compile(r"^[+-]\s*class\s+\w+", re.MULTILINE)),
    ("add_guard", re.compile(r"^[+]\s*(if|try|assert)\s+", re.MULTILINE)),
    ("fix_string", re.compile(r'^[+-]\s*["\']', re.MULTILINE)),
    ("modify_constant", re.compile(r"^[+-]\s*[A-Z_]{3,}\s*=", re.MULTILINE)),
    ("add_comment", re.compile(r"^[+]\s*#", re.MULTILINE)),
]


def get_last_diff(root: Path, n_commits: int = 1) -> str:
    """Get the unified diff of the last N commits."""
    try:
        result = subprocess.run(
            ["git", "diff", f"HEAD~{n_commits}", "HEAD", "--unified=3"],
            cwd=root, capture_output=True, text=True, timeout=15,
        )
        return result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


def parse_diff_files(diff_text: str) -> list[str]:
    """Extract file paths changed in a diff."""
    files = re.findall(r"^diff --git a/(.+?) b/", diff_text, re.MULTILINE)
    return list(dict.fromkeys(files))  # dedupe preserving order


def classify_intents(diff_text: str) -> list[str]:
    """Classify the types of changes in a diff."""
    found: list[str] = []
    for intent, pattern in INTENT_PATTERNS:
        if pattern.search(diff_text):
            found.append(intent)
    return found if found else ["unknown_change"]


def generate_fix_summary(
    root: Path,
    electron_id: str | None = None,
    diff_text: str | None = None,
) -> dict[str, Any]:
    """
    Generate a structured fix summary from the latest git diff.

    Returns a FixSummary dict.
    """
    if diff_text is None:
        diff_text = get_last_diff(root)

    if not diff_text.strip():
        return {"fix_id": "", "files_changed": [], "intents": [], "summary": "no diff"}

    files = parse_diff_files(diff_text)
    intents = classify_intents(diff_text)

    # Count additions/deletions
    additions = len(re.findall(r"^\+[^+]", diff_text, re.MULTILINE))
    deletions = len(re.findall(r"^-[^-]", diff_text, re.MULTILINE))

    # Build a 1-line summary
    intent_str = ", ".join(intents[:3])
    summary = f"{len(files)} files changed ({additions}+/{deletions}-): {intent_str}"

    fix_id = f"fix_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    return {
        "fix_id": fix_id,
        "related_electron_id": electron_id,
        "files_changed": files[:20],
        "intents": intents,
        "additions": additions,
        "deletions": deletions,
        "summary": summary,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


# ── Fix Memory: persistent bug signature patterns ──

def _fix_memory_path(root: Path) -> Path:
    return root / "pigeon_brain" / FIX_MEMORY_FILE


def load_fix_memory(root: Path) -> dict[str, Any]:
    """Load persistent fix memory."""
    p = _fix_memory_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"patterns": {}}


def record_fix_pattern(
    root: Path,
    fix_summary: dict[str, Any],
    success: bool,
) -> None:
    """
    Record a fix pattern in persistent fix memory.

    Builds bug-signature → approach → success/failure rate mappings.
    """
    memory = load_fix_memory(root)
    patterns = memory.setdefault("patterns", {})

    for intent in fix_summary.get("intents", []):
        # Build a signature from intent + file patterns
        files = fix_summary.get("files_changed", [])
        file_hint = files[0].split("/")[-1] if files else "unknown"
        signature = f"{intent}::{file_hint}"

        entry = patterns.setdefault(signature, {
            "count": 0, "successes": 0, "failures": 0,
            "last_seen": None, "files_involved": [],
        })
        entry["count"] += 1
        if success:
            entry["successes"] += 1
        else:
            entry["failures"] += 1
        entry["last_seen"] = datetime.now(timezone.utc).isoformat()
        # Track files (capped)
        for f in files[:3]:
            if f not in entry["files_involved"]:
                entry["files_involved"].append(f)
        entry["files_involved"] = entry["files_involved"][-10:]

    memory["patterns"] = patterns
    p = _fix_memory_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(memory, indent=2, default=str), encoding="utf-8")


def lookup_fix_pattern(root: Path, intent: str) -> list[dict]:
    """Look up known patterns matching an intent."""
    memory = load_fix_memory(root)
    matches = []
    for sig, data in memory.get("patterns", {}).items():
        if intent in sig:
            rate = data["successes"] / max(data["count"], 1)
            matches.append({"signature": sig, "success_rate": rate, **data})
    return sorted(matches, key=lambda m: m["count"], reverse=True)
