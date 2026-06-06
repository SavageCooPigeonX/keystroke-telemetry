"""Bounded codebase search and job memory for Opus orchestration."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LATEST = "logs/opus_coding_area_memory_latest.json"
MARKDOWN = "logs/opus_coding_area_memory.md"
SKIP = {".git", "build", "logs", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}


def build_opus_coding_area_memory(root: Path, prompt: str, *, write: bool = True, limit: int = 15) -> dict[str, Any]:
    """Search codebase by prompt keywords and emit Opus-safe file jobs."""
    root = Path(root)
    keywords = _keywords(prompt)
    matches = _search(root, keywords, limit=max(limit, 8))
    jobs = [_job(row, prompt) for row in matches[:limit]]
    result = {
        "schema": "opus_coding_area_memory/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "keywords": keywords,
        "blocks": matches[:limit],
        "file_jobs": jobs,
        "orchestration_contract": {
            "opus": "writes search queries, job queue, memory notes, and grading criteria",
            "gemini_file": "explains local context, neighbors, risks, and tests for each file",
            "deepseek": "writes bounded patch and test artifacts only after approved backward pass",
            "grader": "applies only scoped changes with passing validations and memory update",
            "direct_opus_code_execution": False,
        },
        "paths": {"latest": LATEST, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        (root / MARKDOWN).write_text(render_coding_area_memory(result), encoding="utf-8")
    return result


def render_coding_area_memory(memory: dict[str, Any]) -> str:
    lines = ["# Opus Coding Area Memory", "", f"- prompt: {memory.get('prompt', '')}"]
    lines.append(f"- keywords: {', '.join(memory.get('keywords') or [])}")
    lines.extend(["", "## Search Blocks"])
    for block in memory.get("blocks") or []:
        lines.append(f"- `{block['file']}` score={block['score']} lines={block['lines']}")
    lines.extend(["", "## File Jobs"])
    for job in memory.get("file_jobs") or []:
        lines.append(f"- `{job['job_id']}` {job['target_file']} -> {job['mode']}")
    return "\n".join(lines) + "\n"


def _search(root: Path, keywords: list[str], *, limit: int) -> list[dict[str, Any]]:
    rows = []
    for path in root.rglob("*.py"):
        if any(part in SKIP for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        text = _read(path)
        hay = f"{rel}\n{text}".lower()
        hits = [word for word in keywords if word in hay]
        if not hits:
            continue
        score = len(set(hits)) * 10 + sum(hay.count(word) for word in set(hits))
        rows.append({"file": rel, "score": score, "hits": sorted(set(hits)), "lines": _snippets(text, hits)})
    return sorted(rows, key=lambda row: (-row["score"], row["file"]))[:limit]


def _job(block: dict[str, Any], prompt: str) -> dict[str, Any]:
    target = block["file"]
    job_id = "ocam-" + hashlib.sha1(f"{target}|{prompt}".encode("utf-8")).hexdigest()[:12]
    return {
        "schema": "opus_file_job/v1",
        "job_id": job_id,
        "status": "proposed",
        "mode": "gemini_context_then_deepseek_patch_artifact",
        "target_file": target,
        "search_hits": block.get("hits", []),
        "allowed_outputs": ["patch artifact", "test artifact", "memory note"],
        "approval_gate": "backward pass approves scope before DeepSeek writes",
        "validation": [f"py -m py_compile {target}", "git diff --check"],
    }


def _snippets(text: str, hits: list[str]) -> list[dict[str, Any]]:
    lines = text.splitlines()
    snippets = []
    lowered = [line.lower() for line in lines]
    for idx, line in enumerate(lowered):
        if any(hit in line for hit in hits):
            start = max(0, idx - 1)
            end = min(len(lines), idx + 2)
            snippets.append({"start": start + 1, "text": "\n".join(lines[start:end])[:600]})
        if len(snippets) >= 2:
            break
    return snippets


def _keywords(prompt: str) -> list[str]:
    stop = {"the", "and", "that", "with", "from", "this", "have", "into", "code", "file", "files", "opus"}
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", prompt.lower())
    return list(dict.fromkeys(word for word in words if word not in stop))[:18]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
