"""codex_compat_add_file_sim_focus_files_seq041_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _add_file_sim_focus_files(pack: dict[str, Any]) -> None:
    """Promote file-sim proposals into focus files when selectors are sparse."""
    focus = pack.setdefault("focus_files", [])
    if not isinstance(focus, list):
        pack["focus_files"] = []
        focus = pack["focus_files"]
    seen = {
        str(item.get("name") or "")
        for item in focus
        if isinstance(item, dict) and item.get("name")
    }
    file_sim = pack.get("file_sim") if isinstance(pack.get("file_sim"), dict) else {}
    for proposal in (file_sim.get("proposals") or [])[:8]:
        if not isinstance(proposal, dict):
            continue
        name = str(proposal.get("path") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        focus.append({
            "name": name,
            "reason": "file_sim_proposal",
            "score": proposal.get("interlink_score"),
            "decision": proposal.get("decision"),
        })
