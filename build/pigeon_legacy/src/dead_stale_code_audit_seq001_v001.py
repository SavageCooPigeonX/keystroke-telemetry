"""Dead/stale code path audit for the telemetry repo.

This is the bridge between git archaeology and current source health:
deleted paths explain what was intentionally killed, while live files are
scored for orphaned imports, version shadows, stale surfaces, and mutation
lineage.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "dead_stale_code_audit/v1"
MARK = "@@DEAD_STALE@@"

SOURCE_DIRS = ("src", "client", "scripts", "pigeon_brain", "pigeon_compiler")
EXCLUDE_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    "venv",
    "node_modules",
    "logs",
}
ENTRYPOINT_NAMES = {"__init__.py", "__main__.py", "codex_compat.py", "test_all.py"}


def audit_dead_stale_code_paths(root: Path, write: bool = True, limit: int = 60) -> dict[str, Any]:
    """Audit dead/stale source paths and reconstruct why older paths died."""
    root = Path(root)
    now = _now()
    files = _source_files(root)
    text_index = _text_index(files)
    reference_index = _reference_index(text_index)
    import_index = _import_index(root, files)
    mutation_events = _git_mutation_events(root)
    deletion_groups = _summarize_deletions(mutation_events)
    lineage_by_identity = _lineage_by_identity(mutation_events)
    version_groups = _version_groups(files)
    file_identity_growth = _load_file_identity_growth(root)

    findings = []
    for path in files:
        rel = _rel(root, path)
        meta = _file_meta(root, path, text_index, reference_index, import_index, version_groups, lineage_by_identity, file_identity_growth)
        suspicion = _suspicion(meta)
        if suspicion["score"] <= 0:
            continue
        findings.append({
            "schema": "dead_stale_code_finding/v1",
            "path": rel,
            "identity": meta["identity"],
            "status": suspicion["status"],
            "score": suspicion["score"],
            "signals": suspicion["signals"],
            "reconstructed_reason": _reconstruct_live_reason(meta, suspicion),
            "suggested_action": _suggest_live_action(meta, suspicion),
            "meta": meta,
        })
    findings.sort(key=lambda item: (item["score"], len(item["signals"])), reverse=True)
    top_findings = findings[: max(1, int(limit or 60))]
    dead_paths = _dead_path_findings(mutation_events, limit=limit)
    summary = {
        "schema": SCHEMA,
        "ts": now,
        "root": str(root),
        "source_file_count": len(files),
        "findings_count": len(findings),
        "dead_event_count": len([event for event in mutation_events if event.get("event_type") == "delete"]),
        "rename_event_count": len([event for event in mutation_events if event.get("event_type") == "rename"]),
        "category_counts": Counter(item["status"] for item in findings),
        "deletion_groups": deletion_groups,
        "top_findings": top_findings,
        "dead_paths": dead_paths,
        "paths": {
            "json": "logs/dead_stale_code_audit_latest.json",
            "markdown": "logs/dead_stale_code_audit_latest.md",
            "findings": "logs/dead_stale_code_findings.jsonl",
        },
    }
    summary["category_counts"] = dict(summary["category_counts"])
    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        _write_json(logs / "dead_stale_code_audit_latest.json", summary)
        _write_jsonl(logs / "dead_stale_code_findings.jsonl", top_findings)
        (logs / "dead_stale_code_audit_latest.md").write_text(render_dead_stale_code_audit(summary), encoding="utf-8")
    return summary


def render_dead_stale_code_audit(summary: dict[str, Any]) -> str:
    lines = [
        "# Dead / Stale Code Path Audit",
        "",
        f"- generated_at: `{summary.get('ts', '')}`",
        f"- source_files_scanned: `{summary.get('source_file_count', 0)}`",
        f"- live_findings: `{summary.get('findings_count', 0)}`",
        f"- deleted_events_seen: `{summary.get('dead_event_count', 0)}`",
        f"- rename_events_seen: `{summary.get('rename_event_count', 0)}`",
        "",
        "## What Got Killed",
        "",
    ]
    groups = summary.get("deletion_groups") if isinstance(summary.get("deletion_groups"), dict) else {}
    for name, data in groups.items():
        lines.extend([
            f"### {name}",
            "",
            f"- count: `{data.get('count', 0)}`",
            f"- reconstructed why: {data.get('why', '')}",
        ])
        samples = data.get("samples") if isinstance(data.get("samples"), list) else []
        for sample in samples[:6]:
            lines.append(f"- `{sample.get('path')}` via `{sample.get('short')}` - {sample.get('subject', '')[:140]}")
        lines.append("")

    lines.extend([
        "## Live Stale Suspects",
        "",
    ])
    for item in (summary.get("top_findings") or [])[:25]:
        lines.extend([
            f"### `{item.get('path')}`",
            "",
            f"- status: `{item.get('status')}` score `{item.get('score')}`",
            f"- signals: `{', '.join(item.get('signals') or [])}`",
            f"- reconstructed why: {item.get('reconstructed_reason')}",
            f"- suggested action: {item.get('suggested_action')}",
        ])
        lineage = ((item.get("meta") or {}).get("lineage") or [])[:2]
        for event in lineage:
            lines.append(f"- lineage: `{event.get('event_type')}` `{event.get('old_path')}` -> `{event.get('new_path')}` ({event.get('short')})")
        header = (item.get("meta") or {}).get("header_intent")
        if header:
            lines.append(f"- header intent: {header[:180]}")
        lines.append("")

    lines.extend([
        "## Recently Dead Paths",
        "",
    ])
    for item in (summary.get("dead_paths") or [])[:30]:
        lines.extend([
            f"- `{item.get('path')}`",
            f"  - category: `{item.get('category')}`",
            f"  - why: {item.get('why')}",
            f"  - commit: `{item.get('short')}` {item.get('subject', '')[:120]}",
        ])
    lines.extend([
        "",
        "## Read This As",
        "",
        "Do not delete every suspect. The correct loop is: mark generated/artifact paths as intentional,",
        "fold useful mutation history into file identities, and only remove a live orphan after import checks",
        "and tests prove no runtime path still calls it.",
        "",
    ])
    return "\n".join(lines)


def _source_files(root: Path) -> list[Path]:
    out = []
    for directory in SOURCE_DIRS:
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            parts = set(path.relative_to(root).parts)
            if parts & EXCLUDE_PARTS:
                continue
            out.append(path)
    for path in root.glob("*.py"):
        if path.name.startswith("_tmp_"):
            continue
        out.append(path)
    return sorted(set(out), key=lambda item: item.as_posix().lower())


def _text_index(files: list[Path]) -> dict[str, str]:
    index = {}
    for path in files:
        try:
            index[path.as_posix()] = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            index[path.as_posix()] = ""
    return index


def _reference_index(text_index: dict[str, str]) -> dict[str, set[str]]:
    refs: dict[str, set[str]] = defaultdict(set)
    for key, text in text_index.items():
        for token in set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)):
            refs[token].add(key)
        for token in set(re.findall(r"[A-Za-z][A-Za-z0-9]+", key.replace("\\", "/"))):
            refs[token].add(key)
    return refs


def _import_index(root: Path, files: list[Path]) -> dict[str, Any]:
    imported_names: Counter = Counter()
    importers: dict[str, set[str]] = defaultdict(set)
    for path in files:
        rel = _rel(root, path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        except OSError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = str(alias.name or "")
                    imported_names[name] += 1
                    imported_names[name.rsplit(".", 1)[-1]] += 1
                    importers[name].add(rel)
                    importers[name.rsplit(".", 1)[-1]].add(rel)
            elif isinstance(node, ast.ImportFrom):
                module = str(node.module or "")
                if module:
                    imported_names[module] += 1
                    imported_names[module.rsplit(".", 1)[-1]] += 1
                    importers[module].add(rel)
                    importers[module.rsplit(".", 1)[-1]].add(rel)
                for alias in node.names:
                    name = str(alias.name or "")
                    imported_names[name] += 1
                    importers[name].add(rel)
    return {
        "imported_names": imported_names,
        "importers": importers,
    }


def _file_meta(
    root: Path,
    path: Path,
    text_index: dict[str, str],
    reference_index: dict[str, set[str]],
    import_index: dict[str, Any],
    version_groups: dict[str, list[dict[str, Any]]],
    lineage_by_identity: dict[str, list[dict[str, Any]]],
    growth: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rel = _rel(root, path)
    text = text_index.get(path.as_posix(), "")
    identity = _identity(path)
    base = _identity_base(identity)
    token_names = _name_variants(root, path)
    textual_refs = _textual_reference_count(path, reference_index, token_names)
    import_refs = _import_reference_count(rel, identity, base, import_index)
    versions = version_groups.get(base, [])
    latest = versions[-1] if versions else {}
    growth_row = growth.get(rel) or growth.get(path.as_posix()) or {}
    return {
        "rel": rel,
        "identity": identity,
        "identity_base": base,
        "module_path": _module_path(root, path),
        "line_count": len(text.splitlines()),
        "textual_refs": textual_refs,
        "import_refs": import_refs,
        "referenced_by_seen": growth_row.get("referenced_by_seen"),
        "imports_seen": growth_row.get("imports_seen"),
        "interlink_score": growth_row.get("interlink_score"),
        "version_rank": _version_rank(path.name),
        "latest_version_rank": latest.get("rank"),
        "version_group_size": len(versions),
        "latest_in_group": bool(latest and latest.get("path") == rel),
        "lineage": lineage_by_identity.get(base, [])[:6],
        "header_intent": _header_intent(text),
        "is_entrypoint": path.name in ENTRYPOINT_NAMES or "if __name__ == \"__main__\"" in text,
        "is_test": rel.startswith("test_") or "/test_" in rel or rel.startswith("scripts/"),
        "is_generated_output": _is_generated_output(rel),
    }


def _suspicion(meta: dict[str, Any]) -> dict[str, Any]:
    score = 0
    signals = []
    if meta["textual_refs"] == 0 and meta["import_refs"] == 0 and not meta["is_entrypoint"]:
        score += 35
        signals.append("no_text_or_import_refs")
    elif meta["import_refs"] == 0 and not meta["is_entrypoint"]:
        score += 16
        signals.append("no_import_refs")
    if meta.get("referenced_by_seen") == 0 and not meta["is_entrypoint"]:
        score += 18
        signals.append("identity_growth_saw_zero_references")
    if meta["version_group_size"] > 1 and not meta["latest_in_group"]:
        score += 30
        signals.append("shadowed_by_newer_version")
    if meta["is_generated_output"]:
        score += 22
        signals.append("generated_or_compiler_output")
    if meta["line_count"] == 0:
        score += 40
        signals.append("empty_file")
    if meta["line_count"] > 900 and meta["import_refs"] == 0:
        score += 15
        signals.append("large_unimported_surface")
    if meta["is_test"]:
        score -= 14
        signals.append("test_or_script_surface")
    if meta["is_entrypoint"]:
        score -= 30
        signals.append("entrypoint_guard")
    score = max(0, score)
    if score >= 70:
        status = "likely_dead"
    elif score >= 45:
        status = "stale_suspect"
    elif score >= 20:
        status = "watch"
    else:
        status = "low_signal"
    return {"score": score, "status": status, "signals": signals}


def _reconstruct_live_reason(meta: dict[str, Any], suspicion: dict[str, Any]) -> str:
    signals = set(suspicion.get("signals") or [])
    if "generated_or_compiler_output" in signals:
        return "Looks like generated/compiler output that survived a previous artifact cleanup."
    if "shadowed_by_newer_version" in signals:
        return "Identity has newer sequence/version siblings; this file was probably mutated forward and left as a stale shard."
    if "no_text_or_import_refs" in signals and meta.get("lineage"):
        latest = meta["lineage"][0]
        return f"Current file has no live references but carries mutation lineage from {latest.get('short')}: {latest.get('subject', '')[:120]}"
    if "identity_growth_saw_zero_references" in signals:
        return "The live identity-growth pass saw imports but no inbound references, so the file is awake in sims but not proven in runtime."
    if "large_unimported_surface" in signals:
        return "Large code surface with no import refs; likely an old standalone tool, test harness, or migrated module."
    return "Low-confidence stale signal; inspect before deleting."


def _suggest_live_action(meta: dict[str, Any], suspicion: dict[str, Any]) -> str:
    signals = set(suspicion.get("signals") or [])
    if "generated_or_compiler_output" in signals:
        return "Move to ignored generated-output lane or delete after verifying no tests import it."
    if "shadowed_by_newer_version" in signals:
        return "Compare against newest sibling, port any unique behavior, then retire this path."
    if "no_text_or_import_refs" in signals:
        return "Run import/text search and targeted tests; if clean, mark as dead and remove."
    if "identity_growth_saw_zero_references" in signals:
        return "Either add a real caller or derank it from future context windows."
    return "Keep but mark watch until another mutation confirms ownership."


def _git_mutation_events(root: Path) -> list[dict[str, Any]]:
    args = [
        "log",
        "--name-status",
        "--find-renames",
        "--find-copies",
        "--date=iso",
        f"--pretty=format:{MARK}%x09%H%x09%ad%x09%s",
    ]
    try:
        output = _git(root, args)
    except Exception:
        return []
    events = []
    current: dict[str, str] | None = None
    for line in output.splitlines():
        if line.startswith(MARK + "\t"):
            parts = line.split("\t", 3)
            current = {
                "commit": parts[1],
                "short": parts[1][:7],
                "date": parts[2],
                "subject": parts[3] if len(parts) > 3 else "",
            }
            continue
        if not current or not line.strip():
            continue
        event = _event_from_status_line(line)
        if event:
            events.append({**current, **event, "category": _death_category(event, current)})
    return events


def _event_from_status_line(line: str) -> dict[str, str] | None:
    parts = line.split("\t")
    if len(parts) < 2:
        return None
    status = parts[0]
    kind_match = re.match(r"[A-Z]+", status)
    kind = kind_match.group(0) if kind_match else status[:1]
    if kind in {"R", "C"} and len(parts) >= 3:
        return {
            "status": status,
            "event_type": "rename" if kind == "R" else "copy",
            "old_path": parts[1],
            "new_path": parts[2],
            "path": parts[2],
        }
    if kind == "D":
        return {"status": status, "event_type": "delete", "old_path": parts[1], "new_path": "", "path": parts[1]}
    if kind == "A":
        return {"status": status, "event_type": "add", "old_path": "", "new_path": parts[1], "path": parts[1]}
    if kind == "M":
        return {"status": status, "event_type": "modify", "old_path": "", "new_path": parts[1], "path": parts[1]}
    return None


def _death_category(event: dict[str, str], commit: dict[str, str]) -> str:
    path = str(event.get("old_path") or event.get("new_path") or event.get("path") or "").lower()
    subject = str(commit.get("subject") or "").lower()
    if event.get("event_type") == "rename":
        return "mutated_identity"
    if any(bit in path for bit in ("operator_profile", "query_memory", "rework_log", "file_profiles", "file_heat_map", "heal_log", "rollback_logs")):
        return "privacy_or_runtime_scrub"
    if any(bit in subject for bit in ("sensitive", "scrub", "gitignore")):
        return "privacy_or_runtime_scrub"
    if path.startswith("build/") or ".egg-info" in path or "compiler_output" in path or "/output/" in path:
        return "generated_artifact_purge"
    if any(bit in path for bit in ("_tmp", "stress", "deep_test", "verify_", "test_logs", "stress_logs", "tmp_")):
        return "temp_or_stress_cleanup"
    if any(bit in subject for bit in ("auto-rename", "rename", "split", "compressed filename")):
        return "superseded_by_mutation"
    if path.endswith(".md") or "docs/" in path or "manifest" in path:
        return "stale_docs_cleanup"
    return "unclassified_dead_path"


def _summarize_deletions(events: list[dict[str, Any]]) -> dict[str, Any]:
    why = {
        "privacy_or_runtime_scrub": "Intentionally removed tracked personal/runtime data from source control.",
        "generated_artifact_purge": "Build/compiler output was killed because source should be canonical, not generated copies.",
        "temp_or_stress_cleanup": "One-off probes, stress harnesses, and temp scripts were cleaned after serving their diagnostic purpose.",
        "superseded_by_mutation": "Older package shards were replaced by renamed/split/compressed identities.",
        "stale_docs_cleanup": "Docs/log summaries stopped matching live architecture and were removed instead of kept as truth.",
        "unclassified_dead_path": "Deleted without enough naming or commit context to classify safely.",
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if event.get("event_type") != "delete":
            continue
        grouped[event.get("category", "unclassified_dead_path")].append(event)
    out = {}
    for category, rows in sorted(grouped.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        out[category] = {
            "count": len(rows),
            "why": why.get(category, "Deleted for unknown reason."),
            "samples": [
                {
                    "path": row.get("old_path") or row.get("path"),
                    "short": row.get("short"),
                    "subject": row.get("subject"),
                    "date": row.get("date"),
                }
                for row in rows[:8]
            ],
        }
    return out


def _dead_path_findings(events: list[dict[str, Any]], limit: int = 60) -> list[dict[str, Any]]:
    why = {
        "privacy_or_runtime_scrub": "privacy/runtime data was intentionally removed from tracking",
        "generated_artifact_purge": "generated output was purged so source stays canonical",
        "temp_or_stress_cleanup": "temporary diagnostic path served its purpose and was removed",
        "superseded_by_mutation": "older identity was superseded by rename/split/compression",
        "stale_docs_cleanup": "documentation/log artifact no longer represented live state",
        "unclassified_dead_path": "unknown; inspect commit before copying the pattern",
    }
    out = []
    for event in events:
        if event.get("event_type") != "delete":
            continue
        category = event.get("category", "unclassified_dead_path")
        out.append({
            "path": event.get("old_path") or event.get("path"),
            "category": category,
            "why": why.get(category, "unknown"),
            "short": event.get("short"),
            "subject": event.get("subject"),
            "date": event.get("date"),
        })
    return out[: max(1, int(limit or 60))]


def _lineage_by_identity(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        if event.get("event_type") not in {"rename", "copy", "add", "modify"}:
            continue
        for path_key in ("old_path", "new_path", "path"):
            path = str(event.get(path_key) or "")
            if not path:
                continue
            base = _identity_base(Path(path).stem)
            out[base].append(event)
    return out


def _version_groups(files: list[Path]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in files:
        base = _identity_base(path.stem)
        groups[base].append({"path": path.as_posix().replace("\\", "/"), "rank": _version_rank(path.name)})
    for rows in groups.values():
        rows.sort(key=lambda item: item["rank"])
    return groups


def _load_file_identity_growth(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "logs" / "file_identity_growth.jsonl"
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-2000:]
    except OSError:
        return out
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        file_path = str(row.get("file") or "").replace("\\", "/")
        if file_path:
            out[file_path] = row
    return out


def _textual_reference_count(path: Path, reference_index: dict[str, set[str]], names: list[str]) -> int:
    self_key = path.as_posix()
    files = set()
    for name in names:
        if not name or name in {"__init__", "__main__"}:
            continue
        files.update(reference_index.get(name, set()))
        files.update(reference_index.get(name.replace(".", "_"), set()))
        files.update(reference_index.get(name.rsplit(".", 1)[-1], set()))
    files.discard(self_key)
    return len(files)


def _import_reference_count(rel: str, identity: str, base: str, import_index: dict[str, Any]) -> int:
    imported = import_index.get("imported_names") if isinstance(import_index.get("imported_names"), Counter) else Counter()
    variants = {identity, base, Path(rel).stem, _module_path_from_rel(rel)}
    return sum(int(imported.get(name, 0)) for name in variants if name)


def _name_variants(root: Path, path: Path) -> list[str]:
    rel = _rel(root, path)
    stem = path.stem
    return _dedupe([
        stem,
        _identity_base(stem),
        _module_path_from_rel(rel),
        Path(rel).with_suffix("").as_posix(),
    ])


def _identity(path: Path) -> str:
    return path.stem


def _identity_base(name: str) -> str:
    text = str(name or "")
    text = re.sub(r"_seq\d+_v\d+(?:_seq\d+_v\d+)?", "", text)
    text = re.sub(r"_s\d+_v\d+(?:_d\d+)?", "", text)
    text = re.sub(r"_v\d+(?:_d\d+)?", "", text)
    text = re.sub(r"_d\d{4}", "", text)
    text = re.sub(r"_[a-z]*rename_cascade$", "", text)
    text = re.sub(r"__+", "_", text).strip("_")
    return text or name


def _version_rank(name: str) -> tuple[int, int, int]:
    seq = _first_int(re.findall(r"(?:seq|_s)(\d+)", name), 0)
    ver = _first_int(re.findall(r"_v(\d+)", name), 0)
    date = _first_int(re.findall(r"_d(\d+)", name), 0)
    return (seq, ver, date)


def _first_int(values: list[str], default: int) -> int:
    if not values:
        return default
    try:
        return int(values[-1])
    except ValueError:
        return default


def _module_path(root: Path, path: Path) -> str:
    return _module_path_from_rel(_rel(root, path))


def _module_path_from_rel(rel: str) -> str:
    return str(Path(rel).with_suffix("")).replace("\\", ".").replace("/", ".")


def _is_generated_output(rel: str) -> bool:
    lower = rel.lower()
    return "compiler_output" in lower or "/output/" in lower or lower.startswith("build/")


def _header_intent(text: str) -> str:
    lines = text.splitlines()[:80]
    hits = []
    for line in lines:
        stripped = line.strip()
        if any(key in stripped for key in ("DESC:", "INTENT:", "EDIT_WHY:", "Triggered by:", "Intent:")):
            hits.append(stripped.lstrip("# ").strip())
    if hits:
        return " | ".join(hits[:4])
    try:
        tree = ast.parse(text)
        doc = ast.get_docstring(tree)
        if doc:
            return doc.splitlines()[0][:240]
    except SyntaxError:
        pass
    return ""


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def _git(root: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def _dedupe(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    repo = Path.cwd()
    result = audit_dead_stale_code_paths(repo, write=True)
    print(json.dumps({
        "schema": result["schema"],
        "source_file_count": result["source_file_count"],
        "findings_count": result["findings_count"],
        "dead_event_count": result["dead_event_count"],
        "paths": result["paths"],
    }, indent=2, ensure_ascii=False))
