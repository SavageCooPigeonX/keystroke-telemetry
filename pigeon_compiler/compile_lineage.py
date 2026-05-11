"""Compile lineage writer for Pigeon split outputs.

The compiler renames one source file into many generated files. This module
records the identity bridge so tools that remember old names can resolve the
current generated file after a rename or split.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "pigeon_compile_lineage/v1"
ALIAS_SCHEMA = "file_identity_aliases/v1"


def write_compile_lineage(
    root: Path,
    source_file: Path,
    target_dir: Path,
    plan: dict[str, Any],
    results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Write per-compile lineage plus the global file identity alias map."""
    root = Path(root).resolve()
    source_file = Path(source_file).resolve()
    target_dir = Path(target_dir).resolve()
    source_rel = _rel(root, source_file)
    target_rel = _rel(root, target_dir)
    result_by_file = {
        str(row.get("file") or ""): row
        for row in (results or [])
        if isinstance(row, dict)
    }
    now = datetime.now(timezone.utc).isoformat()
    entries = []
    for index, cut in enumerate(plan.get("cuts") or [], 1):
        if not isinstance(cut, dict):
            continue
        generated_file = str(cut.get("new_file") or "").strip()
        if not generated_file:
            continue
        generated_rel = f"{target_rel}/{generated_file}".replace("\\", "/")
        generated_path = target_dir / generated_file
        symbols = _cut_symbols(cut)
        row = result_by_file.get(generated_file, {})
        line_count = row.get("lines")
        if line_count is None:
            line_count = _line_count(generated_path)
        entries.append({
            "seq": _seq_from_name(generated_file) or index,
            "version": _version_from_name(generated_file) or 1,
            "source_file": source_rel,
            "source_symbols": symbols,
            "generated_file": generated_rel,
            "generated_module": generated_path.stem,
            "identity_key": _identity_key(source_rel, symbols),
            "aliases": _aliases_for_cut(source_rel, symbols, generated_rel),
            "line_count": line_count,
            "status": row.get("status") or ("OK" if generated_path.exists() else "MISSING"),
            "reason": cut.get("reason", ""),
        })
    lineage = {
        "schema": SCHEMA,
        "compiled_at": now,
        "source_file": source_rel,
        "source_stem": source_file.stem,
        "target_dir": target_rel,
        "plan_strategy": plan.get("strategy", ""),
        "file_count": len(entries),
        "files": entries,
    }

    target_dir.mkdir(parents=True, exist_ok=True)
    _write_json(target_dir / "COMPILE_LINEAGE.json", lineage)
    (target_dir / "COMPILE_LINEAGE.md").write_text(_render_lineage(lineage), encoding="utf-8")

    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _append_jsonl(logs / "compile_lineage.jsonl", lineage)
    _merge_aliases(logs / "file_identity_aliases.json", lineage)
    return lineage


def resolve_identity_alias(root: Path, key: str) -> dict[str, Any]:
    """Resolve a remembered path or source symbol through compile aliases."""
    aliases = _load_json(Path(root) / "logs" / "file_identity_aliases.json")
    if not isinstance(aliases, dict):
        return {}
    normalized = str(key or "").strip().replace("\\", "/")
    rows = aliases.get("aliases") or {}
    if not isinstance(rows, dict):
        return {}
    return rows.get(normalized) or rows.get(normalized.lstrip("./")) or {}


def _merge_aliases(path: Path, lineage: dict[str, Any]) -> None:
    data = _load_json(path)
    if not isinstance(data, dict) or data.get("schema") != ALIAS_SCHEMA:
        data = {"schema": ALIAS_SCHEMA, "aliases": {}, "sources": {}}
    aliases = data.setdefault("aliases", {})
    sources = data.setdefault("sources", {})
    source_file = lineage.get("source_file", "")
    generated_files = []
    for entry in lineage.get("files") or []:
        generated = entry.get("generated_file", "")
        if generated:
            generated_files.append(generated)
        for alias in entry.get("aliases") or []:
            aliases[alias] = {
                "current_file": generated,
                "current_files": [generated] if generated else [],
                "source_file": source_file,
                "source_symbols": entry.get("source_symbols", []),
                "identity_key": entry.get("identity_key", ""),
                "compiled_at": lineage.get("compiled_at", ""),
            }
    if source_file:
        aliases[source_file] = {
            "current_file": generated_files[0] if generated_files else "",
            "current_files": generated_files,
            "source_file": source_file,
            "source_symbols": [],
            "identity_key": f"{source_file}::*",
            "compiled_at": lineage.get("compiled_at", ""),
        }
        sources[source_file] = {
            "target_dir": lineage.get("target_dir", ""),
            "compiled_at": lineage.get("compiled_at", ""),
            "current_files": generated_files,
        }
    _write_json(path, data)


def _cut_symbols(cut: dict[str, Any]) -> list[str]:
    symbols: list[str] = []
    for key in ("functions", "classes", "constants", "contents", "new_helpers"):
        for value in cut.get(key) or []:
            text = str(value).strip()
            if text and text not in symbols:
                symbols.append(text)
    return symbols


def _aliases_for_cut(source_rel: str, symbols: list[str], generated_rel: str) -> list[str]:
    aliases = [generated_rel]
    for symbol in symbols:
        aliases.extend([
            f"{source_rel}::{symbol}",
            f"{Path(source_rel).stem}::{symbol}",
            symbol,
        ])
    return list(dict.fromkeys(aliases))


def _identity_key(source_rel: str, symbols: list[str]) -> str:
    if not symbols:
        return f"{source_rel}::*"
    return f"{source_rel}::{'|'.join(symbols)}"


def _render_lineage(lineage: dict[str, Any]) -> str:
    lines = [
        f"# Compile Lineage - {lineage.get('source_file')}",
        "",
        f"- schema: `{lineage.get('schema')}`",
        f"- compiled_at: `{lineage.get('compiled_at')}`",
        f"- target_dir: `{lineage.get('target_dir')}`",
        f"- file_count: `{lineage.get('file_count')}`",
        "",
        "| Source Symbols | Generated File | Identity |",
        "|---|---|---|",
    ]
    for entry in lineage.get("files") or []:
        symbols = ", ".join(entry.get("source_symbols") or ["*"])
        lines.append(
            f"| `{symbols}` | `{entry.get('generated_file')}` | `{entry.get('identity_key')}` |"
        )
    lines.append("")
    return "\n".join(lines)


def _seq_from_name(name: str) -> int | None:
    match = re.search(r"_seq(\d+)_", name)
    return int(match.group(1)) if match else None


def _version_from_name(name: str) -> int | None:
    match = re.search(r"_v(\d+)\.py$", name)
    return int(match.group(1)) if match else None


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
