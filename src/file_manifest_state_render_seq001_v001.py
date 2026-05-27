"""Render managed MANIFEST.md blocks for file-sim state."""
from __future__ import annotations

from typing import Any

FOLDER_START = "<!-- manifest:file-sim-state -->"
FOLDER_END = "<!-- /manifest:file-sim-state -->"
GLOBAL_START = "<!-- manifest:global-file-sim-stage -->"
GLOBAL_END = "<!-- /manifest:global-file-sim-stage -->"


def render_folder_block(folder: str, rows: list[dict[str, Any]], audit: dict[str, Any]) -> str:
    intent = audit.get("intent") or {}
    metrics = audit.get("metrics") or {}
    lines = [
        FOLDER_START,
        "",
        "## File Sim State",
        "",
        f"- latest_intent: `{intent.get('intent_key', '')}`",
        f"- collaboration_score: `{audit.get('collaboration_score', 0)}`",
        f"- relationship_edges: `{metrics.get('relationship_edges', 0)}`",
        "- authority: proposals only; source rewrites require grader, validation, and operator approval",
        "- folder_role: local state room for file comments, context packing, compliance flags, and peer knowledge",
        "",
        "### Context Window",
        "",
        "| Priority | File | Load / reason |",
        "|---:|---|---|",
    ]
    for index, path in enumerate(_context_window(rows), 1):
        lines.append(f"| {index} | `{path}` | {_cell(_context_reason(path, rows))} |")
    lines.extend(["", "### File Proposals", "", "| Status | File | Plan | Gate |", "|---|---|---|---|"])
    for row in rows[:12]:
        lines.append(
            f"| {_proposal_status(row)} | `{row.get('from_file')}` | "
            f"{_cell(row.get('plan'))} | {_cell('; '.join(row.get('blockers') or []) or 'validation required')} |"
        )
    lines.extend(["", "### File Comments", "", "| File | Says | Shares with |", "|---|---|---|"])
    for row in rows[:12]:
        peers = ", ".join(f"`{item}`" for item in (row.get("to_files") or [])[:5]) or "`manifest`"
        lines.append(f"| `{row.get('from_file')}` | {_cell(row.get('quote'), 220)} | {peers} |")
    lines.extend(["", "### Pigeon Code / Problems", ""])
    problems = _folder_problems(rows)
    lines.extend(f"- {item}" for item in problems)
    if not problems:
        lines.append("- no file-sim compliance problems flagged for this folder")
    lines.extend(["", FOLDER_END])
    return "\n".join(lines)


def render_global_block(written: list[dict[str, Any]], audit: dict[str, Any]) -> str:
    intent = audit.get("intent") or {}
    lines = [
        GLOBAL_START,
        "",
        "## Global File Sim Stage",
        "",
        f"- latest_intent: `{intent.get('intent_key', '')}`",
        f"- verdict: `{audit.get('verdict', '')}`",
        f"- collaboration_score: `{audit.get('collaboration_score', 0)}`",
        "- rule: folder manifests hold local state; this root manifest stages cross-folder routing",
        "- next: load folder manifest state before context selection, then let grader approve proposals",
        "",
        "| Folder manifest | Comments | Changed |",
        "|---|---:|---|",
    ]
    for row in written[:20]:
        lines.append(f"| `{row.get('manifest')}` | {row.get('comments', 0)} | `{row.get('changed')}` |")
    if not written:
        lines.append("| `none` | 0 | `False` |")
    lines.extend(["", "### Global Blockers", ""])
    lines.extend(f"- {item}" for item in audit.get("missing_loops") or [])
    lines.extend(["", GLOBAL_END])
    return "\n".join(lines)


def _context_window(rows: list[dict[str, Any]]) -> list[str]:
    files = []
    for row in rows:
        files.append(str(row.get("from_file") or ""))
        files.extend(str(item) for item in row.get("to_files") or [])
    return _dedupe(files)[:18]


def _context_reason(path: str, rows: list[dict[str, Any]]) -> str:
    for row in rows:
        if row.get("from_file") == path:
            return row.get("plan") or row.get("learned") or "woke for this folder"
        if path in (row.get("to_files") or []):
            return f"peer context for {row.get('from_file')}"
    return "context peer"


def _proposal_status(row: dict[str, Any]) -> str:
    blockers = " ".join(row.get("blockers") or []).lower()
    if "missing validation" in blockers:
        return "blocked_missing_gate"
    if "approval" in blockers:
        return "grader_ready_pending"
    return "proposal_ready"


def _folder_problems(rows: list[dict[str, Any]]) -> list[str]:
    out = []
    for row in rows:
        for blocker in row.get("blockers") or []:
            if "over cap" in blocker or "validation" in blocker:
                out.append(f"`{row.get('from_file')}`: {blocker}")
    return _dedupe(out)[:12]


def _cell(value: Any, limit: int = 160) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:limit]


def _dedupe(items: Any) -> list[str]:
    seen = set()
    out = []
    for item in items:
        text = str(item or "")
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out
