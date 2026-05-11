"""File self-knowledge packets for Codex dynamic context.

The goal is compact residue: every selected file gets a tiny, durable note that
future prompt assembly can reuse without reading the whole file again.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 111 lines | ~948 tokens
# DESC:   file_self_knowledge_packets_for
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_name(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("name") or item.get("file") or item.get("path") or "").strip()
    return str(item or "").strip()


def _read_quote(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    for line in text.splitlines()[:80]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(('"""', "'''", "#", "//", "<!--")):
            return stripped[:220]
    return text.strip().splitlines()[0][:220] if text.strip() else ""


def _owns_from_name(name: str, prompt: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", f"{name} {prompt}".lower())
    stop = {"src", "py", "json", "md", "the", "and", "for", "with", "this", "that"}
    owns: list[str] = []
    for token in tokens:
        if token in stop or token in owns:
            continue
        owns.append(token)
        if len(owns) >= 8:
            break
    return owns


def build_file_self_knowledge(
    root: Path,
    files: list[Any] | None = None,
    prompt: str = "",
    limit: int = 8,
    write: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    selected = [_file_name(item) for item in (files or [])]
    selected = [name for name in selected if name][:limit]

    packets: list[dict[str, Any]] = []
    for name in selected:
        path = root / name
        exists = path.exists()
        packets.append({
            "file": name,
            "exists": exists,
            "owns": _owns_from_name(name, prompt),
            "mutation_scope": {
                "readiness": "inspect_before_edit" if exists else "missing_or_virtual",
                "reason": "selected by dynamic context for the current prompt",
            },
            "validates_with": [
                f"py -m py_compile {name}" if name.endswith(".py") else "git diff --check",
            ],
            "file_quote": _read_quote(path),
            "residue_comment": (
                f"{name}: selected for `{prompt[:80]}`; keep one response note about "
                "what was learned, changed, or left risky."
            ),
        })

    result = {
        "schema": "file_self_knowledge/v1",
        "status": "ok",
        "ts": _utc_now(),
        "operator_read": (
            f"{len(packets)} selected file(s) have residue packets for future Codex/Copilot context."
        ),
        "packets": packets,
    }

    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "file_self_knowledge_latest.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        lines = ["# File Self-Knowledge", "", f"- updated: `{result['ts']}`", ""]
        for packet in packets:
            lines.append(f"- `{packet['file']}` readiness `{packet['mutation_scope']['readiness']}`")
            if packet.get("file_quote"):
                lines.append(f"  - says: {packet['file_quote']}")
            lines.append(f"  - residue: {packet['residue_comment']}")
        (logs / "file_self_knowledge_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result
