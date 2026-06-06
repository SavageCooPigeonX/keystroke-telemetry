"""Signal readers for Opus artifact memory."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def telemetry_read(telemetry: dict[str, Any], training: list[dict[str, Any]], edits: list[dict[str, Any]]) -> dict[str, Any]:
    latest_prompt = telemetry.get("latest_prompt") or {}
    last_training_ts = (training[-1] if training else {}).get("ts")
    age = _age_minutes(last_training_ts)
    status = "fresh" if age is not None and age < 60 else "stale_or_missing"
    return {
        "latest_prompt_ts": latest_prompt.get("ts"),
        "prompt_age_min": _age_minutes(latest_prompt.get("ts")),
        "deleted_words": telemetry.get("deleted_words") or latest_prompt.get("deleted_words") or [],
        "training_pairs": len(training),
        "training_pair_last_ts": last_training_ts,
        "training_pair_age_min": age,
        "training_pair_status": status,
        "edit_pairs": len(edits),
    }


def high_touch_files(git_touches: Counter[str], edits: list[dict[str, Any]], focus: list[str]) -> list[dict[str, Any]]:
    edit_counts = Counter(row.get("file", "") for row in edits if row.get("file"))
    focus_counts = Counter(focus)
    rows = []
    for file in set(git_touches) | set(edit_counts) | set(focus_counts):
        score = git_touches[file] + edit_counts[file] * 3 + focus_counts[file] * 6
        rows.append({"file": file, "score": score, "git_touches": git_touches[file], "edit_pairs": edit_counts[file]})
    return sorted(rows, key=lambda row: (-row["score"], row["file"]))


def file_death_areas(
    root: Path,
    git_touches: Counter[str],
    recent: Counter[str],
    edits: list[dict[str, Any]],
    focus: list[str],
) -> list[dict[str, Any]]:
    edit_counts = Counter(row.get("file", "") for row in edits if row.get("file"))
    candidates = []
    for file, touches in git_touches.most_common(80):
        path = root / file
        if path.exists() and path.suffix == ".py" and recent[file] == 0 and edit_counts[file] == 0 and touches >= 2:
            candidates.append(_death_row(root, file, "historically touched but absent from recent git/edit telemetry"))
    for file in focus:
        if file.endswith(".py") and (root / file).exists() and not nearby_tests(root, file):
            candidates.append(_death_row(root, file, "woke for this prompt without an obvious nearby test"))
    return _unique(candidates)[:10]


def compiler_probe(root: Path, compression: dict[str, Any]) -> dict[str, Any]:
    hook_text = _read(root / ".git" / "hooks" / "pre-push") + "\n" + _read(root / "scripts" / "install_pigeon_hooks.py")
    issues = []
    last = compression.get("last_incremental") or {}
    if not last:
        issues.append("context compressor has no build/compressed/STATS.json last_incremental record")
    if "run_context_compression" not in hook_text and "compress_changed" not in hook_text:
        issues.append("pre-push hook path does not call the context compressor")
    if compression and not last.get("files"):
        issues.append("last compressor run recorded zero files")
    return {
        "status": "needs_wiring" if issues else "wired",
        "issues": issues,
        "last_incremental": last,
        "artifact": "build/compressed/STATS.json",
    }


def file_dialogue(self_knowledge: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for packet in (self_knowledge.get("packets") or [])[:8]:
        scope = packet.get("mutation_scope") or {}
        rows.append({
            "file": packet.get("file", ""),
            "readiness": scope.get("readiness", ""),
            "quote": packet.get("file_quote") or packet.get("model_guide", "")[:180],
        })
    return rows


def memory_directive(high_touch: list[dict[str, Any]], focus: list[str]) -> str:
    hot = ", ".join(row["file"] for row in high_touch[:5]) or "none"
    focused = ", ".join(focus[:8]) or "none"
    return f"Opus should read this artifact, then ask focused files to explain risk. Hot files: {hot}. Focus: {focused}."


def focus_files(telemetry: dict[str, Any], graph: dict[str, Any], self_knowledge: dict[str, Any]) -> list[str]:
    latest = telemetry.get("latest_prompt") or {}
    files = list(latest.get("files_open") or []) + list(graph.get("focus_files") or [])
    files.extend(packet.get("file", "") for packet in self_knowledge.get("packets") or [])
    return [file for file in files if file]


def git_touch_counts(root: Path, limit: int) -> tuple[Counter[str], Counter[str]]:
    cmd = ["git", "log", f"--max-count={limit}", "--name-only", "--pretty=format:COMMIT"]
    try:
        out = subprocess.run(cmd, cwd=root, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    except Exception:
        return Counter(), Counter()
    commits: list[list[str]] = [[]]
    for line in out.splitlines():
        if line == "COMMIT":
            commits.append([])
        elif line.strip():
            commits[-1].append(line.strip())
    commits = [commit for commit in commits if commit]
    return Counter(file for c in commits for file in c), Counter(file for c in commits[:20] for file in c)


def nearby_tests(root: Path, file: str) -> list[str]:
    stem = Path(file).stem
    candidates = [root / f"test_{stem}.py", root / "tests" / f"test_{stem}.py"]
    return [str(path.relative_to(root)).replace("\\", "/") for path in candidates if path.exists()]


def _death_row(root: Path, file: str, reason: str) -> dict[str, Any]:
    return {"file": file, "reason": reason, "nearby_tests": nearby_tests(root, file)}


def _unique(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for row in rows:
        if row["file"] not in seen:
            seen.add(row["file"])
            unique.append(row)
    return unique


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _age_minutes(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return round((datetime.now(timezone.utc) - dt).total_seconds() / 60, 2)
    except ValueError:
        return None
