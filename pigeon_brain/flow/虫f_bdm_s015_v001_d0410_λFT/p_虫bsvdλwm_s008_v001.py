"""虫f_bdm_s015_v001_d0410_λFT_write_memory_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 60 lines | ~517 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def write_to_node_memory(
    root: Path,
    node: str,
    manifests: list[BugManifest],
    electron_id: str,
) -> None:
    """Extend latest node_memory entry with active_bugs field.

    Non-destructive: loads existing memory, finds the most recent entry
    for this node that matches electron_id, adds active_bugs to it.
    Falls back to appending a stub entry if no match found.
    """
    p = root / NODE_MEMORY_PATH
    memory: dict[str, Any] = {}
    if p.exists():
        memory = json.loads(p.read_text("utf-8"))

    node_record = memory.setdefault(node, {"entries": [], "policy": {}})
    entries: list[dict] = node_record.get("entries", [])

    relevant = [
        asdict(m) for m in manifests
        if node == m.origin_module or node in m.affected_chain
    ]
    if not relevant:
        return

    # Try to patch the matching electron entry
    matched = False
    for entry in reversed(entries):
        if entry.get("electron_id") == electron_id:
            entry["active_bugs"] = relevant
            matched = True
            break

    # No existing entry for this electron — write a stub so the chain leaves a mark
    if not matched:
        entries.append({
            "electron_id": electron_id,
            "task_seed": "[bug_manifest_chain injection]",
            "active_bugs": relevant,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        node_record["entries"] = entries[-200:]  # cap

    # Update policy: surface highest-severity active bug
    if relevant:
        worst = max(relevant, key=lambda x: x["severity"])
        node_record["policy"]["active_bug_warning"] = (
            f"{worst['bug_type']}:{worst['origin_module']} sev={worst['severity']:.2f}"
        )

    p.write_text(json.dumps(memory, indent=2, default=str), encoding="utf-8")
