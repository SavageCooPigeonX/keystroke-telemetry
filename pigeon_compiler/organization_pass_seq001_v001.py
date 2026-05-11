"""Whole-codebase organization pass for package-independent pigeon code."""
from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "pigeon_codebase_organization_plan/v1"
LATEST = "logs/pigeon_codebase_organization_plan_latest.json"
HISTORY = "logs/pigeon_codebase_organization_plan.jsonl"
MARKDOWN = "logs/pigeon_codebase_organization_plan.md"
MAX_PY_LINES = 200
SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
    ".venv",
}
TOP_SOURCE_DIRS = {"src", "pigeon_compiler", "pigeon_brain", "client", "scripts"}
ROOT_SRC_FAMILIES = {
    "batch": "src/batch_rewrite",
    "codex": "src/codex_runtime",
    "context": "src/context_orchestration",
    "deepseek": "src/deepseek_lane",
    "email": "src/dead_email_lane",
    "escalation": "src/escalation_engine",
    "file": "src/file_sim",
    "folder": "src/manifest_orchestration",
    "hush": "src/live_intent_runtime",
    "intent": "src/intent_keys",
    "manifest": "src/manifest_orchestration",
    "operator": "src/operator_state",
    "opus": "src/opus_orchestrator",
    "session": "src/session_macro_cycle",
    "tc": "src/thought_completer",
}


@dataclass(frozen=True)
class FileInfo:
    rel: str
    folder: str
    module: str
    line_count: int
    imports: tuple[str, ...]
    parse_error: str = ""


def build_organization_plan(
    root: Path,
    *,
    write: bool = True,
    file_limit: int | None = None,
) -> dict[str, Any]:
    """Scan the repo and produce a plan for folder-independent code rooms."""
    root = Path(root)
    files = _collect_python_files(root, file_limit=file_limit)
    module_index = {_module_name(root, path): path.relative_to(root).as_posix() for path in files}
    infos = [_file_info(root, path, module_index) for path in files]
    folder_rows = _folder_rows(root, infos)
    move_plan = _move_plan(root, infos)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "mode": "plan_only_no_moves",
        "root": str(root),
        "summary": _summary(infos, folder_rows, move_plan),
        "folder_rankings": folder_rows,
        "move_plan": move_plan,
        "compiler_policy": {
            "goal": "folders should be independently compilable rooms with explicit external edges",
            "canonical_rule": "imports and manifests bind to real paths; operator labels and mutation keys are metadata",
            "execution_rule": "apply moves only after import map, manifest update, py_compile, and focused tests",
            "pigeon_code_rule": "new extracted modules target <=200 lines and carry seq/version allocated from local siblings",
        },
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_outputs(root, result)
    return result


def render_organization_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Pigeon Codebase Organization Plan",
        "",
        f"- mode: `{plan.get('mode')}`",
        f"- files scanned: `{(plan.get('summary') or {}).get('files_scanned')}`",
        f"- candidate moves: `{(plan.get('summary') or {}).get('candidate_moves')}`",
        "",
        "## Folder Independence",
        "",
    ]
    for row in (plan.get("folder_rankings") or [])[:30]:
        lines.append(
            f"- `{row['folder']}` score={row['independence_score']} "
            f"mode={row['recommended_mode']} files={row['file_count']} "
            f"external={row['external_edge_count']} overcap={row['overcap_count']}"
        )
    lines.extend(["", "## Move Plan", ""])
    for row in (plan.get("move_plan") or [])[:40]:
        lines.append(
            f"- `{row['file']}` -> `{row['target_folder']}` "
            f"reason={row['reason']} gate={', '.join(row['validation_gate'])}"
        )
    lines.extend(["", "## Compiler Policy", ""])
    for key, value in (plan.get("compiler_policy") or {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def _collect_python_files(root: Path, *, file_limit: int | None) -> list[Path]:
    files = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        files.append(path)
        if file_limit and len(files) >= file_limit:
            break
    return files


def _file_info(root: Path, path: Path, module_index: dict[str, str]) -> FileInfo:
    rel = path.relative_to(root).as_posix()
    folder = _folder_of(rel)
    text = _read_text(path)
    imports: list[str] = []
    parse_error = ""
    try:
        tree = ast.parse(text)
        imports = _project_imports(tree, module_index)
    except SyntaxError as exc:
        parse_error = f"{exc.__class__.__name__}: {exc.msg}"
    return FileInfo(
        rel=rel,
        folder=folder,
        module=_module_name(root, path),
        line_count=text.count("\n") + (1 if text else 0),
        imports=tuple(imports),
        parse_error=parse_error,
    )


def _project_imports(tree: ast.AST, module_index: dict[str, str]) -> list[str]:
    imports: list[str] = []
    known_modules = set(module_index)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = _resolve_import(alias.name, known_modules)
                if target:
                    imports.append(module_index[target])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            base = node.module or ""
            for alias in node.names:
                target = _resolve_import(f"{base}.{alias.name}", known_modules) or _resolve_import(base, known_modules)
                if target:
                    imports.append(module_index[target])
    return tuple(dict.fromkeys(imports))


def _resolve_import(name: str, known_modules: set[str]) -> str:
    parts = name.split(".")
    for size in range(len(parts), 0, -1):
        candidate = ".".join(parts[:size])
        if candidate in known_modules:
            return candidate
    return ""


def _folder_rows(root: Path, infos: list[FileInfo]) -> list[dict[str, Any]]:
    by_folder: dict[str, list[FileInfo]] = defaultdict(list)
    for info in infos:
        by_folder[info.folder].append(info)
    rows = []
    for folder, members in by_folder.items():
        member_files = {item.rel for item in members}
        internal = external = 0
        external_targets: dict[str, int] = defaultdict(int)
        for item in members:
            for target in item.imports:
                if target in member_files:
                    internal += 1
                else:
                    external += 1
                    external_targets[_folder_of(target)] += 1
        overcap = [item.rel for item in members if item.line_count > MAX_PY_LINES]
        manifest = "MANIFEST.md" if folder == "." else f"{folder}/MANIFEST.md"
        manifest_exists = (root / manifest).exists()
        edge_count = internal + external
        edge_total = max(1, edge_count)
        local_ratio = 1.0 if edge_count == 0 else internal / edge_total
        overcap_penalty = min(len(overcap), 10) / 10
        manifest_bonus = 0.12 if manifest_exists else 0
        score = round(max(0, min(1, (local_ratio * 0.68) + manifest_bonus - (overcap_penalty * 0.24))), 4)
        rows.append({
            "folder": folder,
            "operator_label": _operator_label(folder),
            "manifest": manifest,
            "manifest_exists": manifest_exists,
            "file_count": len(members),
            "line_count": sum(item.line_count for item in members),
            "overcap_count": len(overcap),
            "overcap_files": overcap[:10],
            "parse_error_count": sum(1 for item in members if item.parse_error),
            "internal_edge_count": internal,
            "external_edge_count": external,
            "external_folders": [
                {"folder": key, "count": value}
                for key, value in sorted(external_targets.items(), key=lambda pair: (-pair[1], pair[0]))[:8]
            ],
            "independence_score": score,
            "recommended_mode": _mode(score, external, overcap, manifest_exists),
        })
    return sorted(rows, key=lambda row: (row["recommended_mode"] != "self_managed", -row["independence_score"], row["folder"]))


def _move_plan(root: Path, infos: list[FileInfo]) -> list[dict[str, Any]]:
    rows = []
    for info in infos:
        if not info.rel.startswith("src/") or "/" in info.rel.removeprefix("src/"):
            continue
        stem = Path(info.rel).stem
        target = _target_folder(stem)
        if not target or target == "src":
            continue
        if info.line_count <= MAX_PY_LINES and stem.startswith("__"):
            continue
        rows.append({
            "file": info.rel,
            "target_folder": target,
            "target_path": f"{target}/{Path(info.rel).name}",
            "reason": _move_reason(info, target),
            "line_count": info.line_count,
            "imports": list(info.imports)[:12],
            "validation_gate": [
                f"py -m py_compile {info.rel}",
                "git grep old import path",
                f"refresh {target}/MANIFEST.md",
            ],
            "apply_now": False,
        })
    return sorted(rows, key=lambda row: (-row["line_count"], row["target_folder"], row["file"]))[:120]


def _target_folder(stem: str) -> str:
    base = re.sub(r"_(?:seq|s)?\d{3,}.*$", "", stem)
    key = base.split("_", 1)[0].lower()
    return ROOT_SRC_FAMILIES.get(key, "")


def _move_reason(info: FileInfo, target: str) -> str:
    pressure = "overcap" if info.line_count > MAX_PY_LINES else "root-src-bucket"
    return f"{pressure}; family should compile inside {target} instead of source warehouse"


def _mode(score: float, external: int, overcap: list[str], manifest_exists: bool) -> str:
    if not manifest_exists or len(overcap) >= 3:
        return "needs_manifest_room"
    if score >= 0.66 and external <= 2:
        return "self_managed"
    if score >= 0.45:
        return "local_with_explicit_external_edges"
    return "compiler_reorganization_needed"


def _summary(infos: list[FileInfo], folders: list[dict[str, Any]], moves: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "files_scanned": len(infos),
        "folders_scanned": len(folders),
        "candidate_moves": len(moves),
        "overcap_files": sum(1 for item in infos if item.line_count > MAX_PY_LINES),
        "parse_errors": sum(1 for item in infos if item.parse_error),
        "self_managed_folders": sum(1 for row in folders if row["recommended_mode"] == "self_managed"),
        "needs_manifest_room": sum(1 for row in folders if row["recommended_mode"] == "needs_manifest_room"),
    }


def _operator_label(folder: str) -> str:
    if folder == ".":
        return "Root Manifest-inator"
    leaf = folder.strip("/").split("/")[-1]
    words = re.findall(r"[A-Za-z0-9]+", leaf.replace("_", " "))
    if not words:
        words = ["Symbolic", "Room"]
    return " ".join(word.title() for word in words[:3]) + "-inator"


def _folder_of(rel: str) -> str:
    parent = Path(rel).parent.as_posix()
    return "." if parent in {"", "."} else parent


def _module_name(root: Path, path: Path) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _write_outputs(root: Path, plan: dict[str, Any]) -> None:
    _write_json(root / LATEST, plan)
    _append_jsonl(root / HISTORY, plan)
    (root / MARKDOWN).write_text(render_organization_plan(plan), encoding="utf-8")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    root = Path.cwd()
    plan = build_organization_plan(root, write=True)
    summary = plan["summary"]
    print(
        f"scanned={summary['files_scanned']} folders={summary['folders_scanned']} "
        f"moves={summary['candidate_moves']} overcap={summary['overcap_files']}"
    )
    print(f"wrote {LATEST} and {MARKDOWN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_organization_plan", "render_organization_plan"]
