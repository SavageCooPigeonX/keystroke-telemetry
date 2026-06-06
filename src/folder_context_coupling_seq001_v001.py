"""Folder autonomy and coupling audit for manifest-managed sims."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import ast
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.manifest_syntax_matcher_seq001_v001 import match_manifest_syntax

LATEST = "logs/folder_context_coupling_latest.json"
HISTORY = "logs/folder_context_coupling.jsonl"
MARKDOWN = "logs/folder_context_coupling.md"
FILE_SCAN_CAP = 600
OVERCAP_LINE_LIMIT = 800
PACKAGE_RANK_SCAN_CAP = 40
AST_IDENTITY_FILE_CAP = 6


def build_folder_context_coupling(
    root: Path,
    prompt: str,
    *,
    focus_files: list[str] | None = None,
    selected_manifests: list[dict[str, Any]] | None = None,
    write: bool = True,
) -> dict[str, Any]:
    """Measure whether folder context can stay local without losing sim coherence."""
    root = Path(root)
    focus_files = [rel.replace("\\", "/") for rel in (focus_files or [])]
    manifest_match = {}
    if selected_manifests is None:
        manifest_match = match_manifest_syntax(root, prompt + " " + " ".join(focus_files), limit=10, write=False)
        selected_manifests = manifest_match.get("selected_manifests") or []
    folders = _selected_folders(selected_manifests, focus_files)
    graph = _json(root / "logs" / "file_relationship_graph.json")
    syntax = _json(root / "logs" / "operator_syntax_triggers.json")
    overcap_index = _manifest_overcap_index(root)
    folder_rows = [_folder_row(root, folder, focus_files, graph, syntax, overcap_index) for folder in folders]
    package_rows = [
        _folder_row(root, folder, focus_files, graph, syntax, overcap_index)
        for folder in _package_folders(root, folders)
    ]
    package_rankings = _rank_packages(package_rows)
    edges = _folder_edges(graph, folders)
    result = {
        "schema": "folder_context_coupling/v1",
        "ts": _now(),
        "prompt": prompt,
        "selected_manifests": selected_manifests,
        "folders": folder_rows,
        "package_rankings": package_rankings,
        "cross_folder_edges": edges,
        "deepseek_manifest_manager": _deepseek_packet(prompt, folder_rows, edges),
        "policy": {
            "local_first": "folder manifest owns folder state and should satisfy local sim if autonomy_score >= 0.65",
            "coherence_gate": "pull external manifests only for explicit graph edge, selected syntax match, or missing trigger repair",
            "bad_folder_smell": "one manifest with low syntax coverage, high resistance, many external dependencies, scan-cap pressure, or overcap files",
            "dead_path": "email delivery is not considered progress; manifests, receipts, and rankings are the progress artifacts",
        },
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_folder_context_coupling(result), encoding="utf-8")
    return result


def render_folder_context_coupling(result: dict[str, Any]) -> str:
    lines = ["# Folder Context Coupling", "", f"- prompt: {result.get('prompt', '')}", ""]
    lines.extend(["## Folders", ""])
    for row in result.get("folders") or []:
        lines.append(
            f"- `{row.get('folder')}` label={row.get('operator_label')!r} autonomy={row.get('autonomy_score')} "
            f"resistance={row.get('resistance_score')} mode={row.get('recommended_mode')} "
            f"scan_cap_hit={row.get('scan_cap_hit')} overcap={row.get('overcap_file_count')}"
        )
    lines.extend(["", "## Package Ranking", ""])
    for row in result.get("package_rankings") or []:
        lines.append(
            f"- rank {row.get('rank')}: `{row.get('folder')}` label={row.get('operator_label')!r} "
            f"mode={row.get('recommended_mode')} "
            f"autonomy={row.get('autonomy_score')} resistance={row.get('resistance_score')} "
            f"external={row.get('external_edge_count')} overcap={row.get('overcap_file_count')}"
        )
    lines.extend(["", "## Cross-Folder Edges", ""])
    for edge in result.get("cross_folder_edges") or []:
        lines.append(f"- `{edge.get('from_folder')}` -> `{edge.get('to_folder')}` weight={edge.get('weight')}")
    packet = result.get("deepseek_manifest_manager") or {}
    lines.extend(["", "## DeepSeek Manifest Manager", "", packet.get("prompt", "")])
    return "\n".join(lines) + "\n"


def _folder_row(
    root: Path,
    folder: str,
    focus_files: list[str],
    graph: dict[str, Any],
    syntax: dict[str, Any],
    overcap_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    manifest = "MANIFEST.md" if folder == "." else f"{folder}/MANIFEST.md"
    local_files, scan_cap_hit = _repo_file_scan(root, folder)
    local_files = [rel for rel in local_files if _belongs(rel, folder)]
    touched = [rel for rel in focus_files if _belongs(rel, folder)]
    syntax_rows = [row for row in (syntax.get("files") or {}).values() if _belongs(str(row.get("file") or ""), folder)]
    internal, external = _edge_counts(graph, folder)
    overcap_files = _overcap_files(local_files, overcap_index)
    identity = _folder_identity(root, folder, local_files)
    syntax_coverage = len(syntax_rows) / max(1, len(local_files))
    local_ratio = internal / max(1, internal + external)
    overcap_pressure = min(len(overcap_files), 10) / 10
    breadth_pressure = 1.0 if scan_cap_hit else min(len(local_files) / FILE_SCAN_CAP, 1.0) * 0.2
    raw_autonomy = (min(syntax_coverage, 1) * 0.42) + (local_ratio * 0.34) + (min(len(touched), 3) / 3 * 0.12)
    autonomy = round(max(0, raw_autonomy - (overcap_pressure * 0.28) - (breadth_pressure * 0.18)), 4)
    resistance = round(min(1, (external / max(1, internal + external)) * 0.45 + (1 - min(syntax_coverage, 1)) * 0.25 + (overcap_pressure * 0.2) + (breadth_pressure * 0.1)), 4)
    return {
        "folder": folder,
        "operator_label": identity["operator_label"],
        "identity_tokens": identity["identity_tokens"],
        "identity_source": identity["identity_source"],
        "manifest": manifest,
        "local_file_count": len(local_files),
        "scan_cap_hit": scan_cap_hit,
        "focus_file_count": len(touched),
        "syntax_profile_count": len(syntax_rows),
        "syntax_coverage": round(syntax_coverage, 4),
        "internal_edge_count": internal,
        "external_edge_count": external,
        "overcap_file_count": len(overcap_files),
        "overcap_files": overcap_files[:8],
        "autonomy_score": autonomy,
        "resistance_score": resistance,
        "recommended_mode": _mode(autonomy, resistance, scan_cap_hit, len(overcap_files)),
        "missing_trigger_repair": _missing_trigger_repair(folder, local_files, syntax_rows),
    }


def _deepseek_packet(prompt: str, folders: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    weak = [row for row in folders if row["recommended_mode"] != "self_managed"]
    lines = [
        "You are the DeepSeek manifest manager.",
        f"Operator prompt: {prompt}",
        "Goal: improve folder autonomy while preserving simulation coherence.",
        "Rules: write folder state only to that folder MANIFEST.md; root MANIFEST.md gets synthesis only.",
        "Prioritize missing syntax triggers for weak folders before adding cross-folder dependencies.",
    ]
    for row in weak[:8]:
        lines.append(
            f"- repair {row['folder']}: mode={row['recommended_mode']} "
            f"autonomy={row['autonomy_score']} resistance={row['resistance_score']}"
        )
    for edge in edges[:8]:
        lines.append(f"- keep coherence edge {edge['from_folder']} -> {edge['to_folder']} weight={edge['weight']}")
    return {"mode": "manifest_manager_advisory", "weak_folder_count": len(weak), "prompt": "\n".join(lines)}


def _selected_folders(selected_manifests: list[dict[str, Any]], focus_files: list[str]) -> list[str]:
    folders = []
    for row in selected_manifests:
        folder = str(row.get("folder") or ".")
        folders.append(folder or ".")
    folders.extend(_folder_of(rel) for rel in focus_files)
    return list(dict.fromkeys(folder for folder in folders if folder))


def _folder_edges(graph: dict[str, Any], folders: list[str]) -> list[dict[str, Any]]:
    weights: dict[tuple[str, str], float] = defaultdict(float)
    folder_set = set(folders)
    for edge in graph.get("edges") or []:
        src, dst = _folder_of(str(edge.get("from") or "")), _folder_of(str(edge.get("to") or ""))
        if src != dst and (src in folder_set or dst in folder_set):
            weights[(src, dst)] += float(edge.get("weight") or 0)
    rows = [{"from_folder": a, "to_folder": b, "weight": round(w, 4)} for (a, b), w in weights.items()]
    return sorted(rows, key=lambda row: row["weight"], reverse=True)


def _edge_counts(graph: dict[str, Any], folder: str) -> tuple[int, int]:
    internal = external = 0
    for edge in graph.get("edges") or []:
        a, b = _folder_of(str(edge.get("from") or "")), _folder_of(str(edge.get("to") or ""))
        if a == folder and b == folder:
            internal += 1
        elif a == folder or b == folder:
            external += 1
    return internal, external


def _missing_trigger_repair(folder: str, local_files: list[str], syntax_rows: list[dict[str, Any]]) -> list[str]:
    known = {str(row.get("file") or "") for row in syntax_rows}
    return [rel for rel in local_files if rel not in known][:8]


def _mode(autonomy: float, resistance: float, scan_cap_hit: bool = False, overcap_file_count: int = 0) -> str:
    if scan_cap_hit or overcap_file_count >= 3:
        return "deepseek_manifest_manager_repair"
    if autonomy >= 0.65 and resistance <= 0.35:
        return "self_managed"
    if resistance >= 0.55:
        return "deepseek_manifest_manager_repair"
    return "local_with_selected_external_manifests"


def _repo_file_scan(root: Path, folder: str) -> tuple[list[str], bool]:
    base = root if folder == "." else root / folder
    if not base.exists():
        return [], False
    rows = []
    for path in base.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".md", ".js", ".jsx", ".ts", ".tsx", ".ps1"}:
            rows.append(path.relative_to(root).as_posix())
            if len(rows) > FILE_SCAN_CAP:
                return rows[:FILE_SCAN_CAP], True
    return rows, False


def _overcap_files(local_files: list[str], overcap_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [overcap_index[rel] for rel in local_files if rel in overcap_index],
        key=lambda row: str(row["file"]),
    )


def _manifest_overcap_index(root: Path) -> dict[str, dict[str, Any]]:
    manifest = root / "MANIFEST.md"
    rows: dict[str, dict[str, Any]] = {}
    for line in _read_prefix(manifest, 16000).splitlines():
        if not line.startswith("| `"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 3 or not (parts[0].startswith("`") and parts[0].endswith("`")):
            continue
        file_name = parts[0].strip("`")
        try:
            line_count = int(parts[1])
        except ValueError:
            continue
        if line_count > OVERCAP_LINE_LIMIT:
            rows[file_name] = {"file": file_name, "line_floor": line_count, "limit": OVERCAP_LINE_LIMIT}
    return rows


def _line_count_over(path: Path, limit: int) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for idx, _line in enumerate(handle, start=1):
                if idx > limit:
                    return idx
        return idx if "idx" in locals() else 0
    except Exception:
        return 0


def _folder_identity(root: Path, folder: str, local_files: list[str]) -> dict[str, Any]:
    token_scores: dict[str, int] = defaultdict(int)
    path_tokens = _path_identity_tokens(folder)
    for token in path_tokens:
        token_scores[token] += 12

    manifest = root / ("MANIFEST.md" if folder == "." else f"{folder}/MANIFEST.md")
    if manifest.exists():
        for token in _split_identity_text(_read_prefix(manifest, 2400)):
            token_scores[token] += 2

    ast_sources = 0
    for rel in [row for row in local_files if row.endswith(".py")][:AST_IDENTITY_FILE_CAP]:
        try:
            tree = ast.parse(_read_prefix(root / rel, 12000))
        except Exception:
            continue
        ast_sources += 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for token in _split_identity_text(node.name):
                    token_scores[token] += 3
        doc = ast.get_docstring(tree) or ""
        for token in _split_identity_text(doc[:1200]):
            token_scores[token] += 1

    scored_tokens = [
        token
        for token, _score in sorted(token_scores.items(), key=lambda item: (-item[1], item[0]))
        if token not in _IDENTITY_STOPWORDS
    ]
    tokens = list(dict.fromkeys(path_tokens + scored_tokens))[:4]
    if not tokens:
        tokens = ["folder", "context"]
    label = _operator_label(path_tokens if folder in {"", ".", "src"} else tokens)
    return {
        "operator_label": label,
        "identity_tokens": tokens,
        "identity_source": "path+manifest+ast" if ast_sources else "path+manifest",
    }


def _operator_label(tokens: list[str]) -> str:
    title = " ".join(token.replace("_", " ").title() for token in tokens[:3])
    return f"{title}-inator"


def _path_identity_tokens(folder: str) -> list[str]:
    if folder in {"", "."}:
        return ["root", "manifest"]
    if folder == "src":
        return ["source", "warehouse"]
    leaf = folder.replace("\\", "/").rstrip("/").split("/")[-1]
    tokens = [token for token in _split_identity_text(leaf) if token not in _IDENTITY_STOPWORDS]
    return tokens or [token for token in _split_identity_text(folder) if token not in _IDENTITY_STOPWORDS]


def _read_prefix(path: Path, max_chars: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except Exception:
        return ""


def _split_identity_text(text: str) -> list[str]:
    chars = []
    for ch in text.replace("\\", "/"):
        if ch.isalnum():
            chars.append(ch.lower())
        else:
            chars.append(" ")
    raw = "".join(chars).split()
    pieces = []
    for token in raw:
        pieces.extend(_split_camel(token))
    return [piece for piece in pieces if len(piece) >= 3 and not piece.isdigit()]


def _split_camel(token: str) -> list[str]:
    pieces: list[str] = []
    start = 0
    for idx in range(1, len(token)):
        if token[idx].isupper() and not token[idx - 1].isupper():
            pieces.append(token[start:idx].lower())
            start = idx
    pieces.append(token[start:].lower())
    return pieces


_IDENTITY_STOPWORDS = {
    "ago",
    "and",
    "any",
    "are",
    "bool",
    "class",
    "def",
    "dict",
    "file",
    "files",
    "folder",
    "from",
    "get",
    "import",
    "json",
    "list",
    "local",
    "none",
    "path",
    "pigeon",
    "project",
    "repo",
    "return",
    "self",
    "seq001",
    "str",
    "true",
    "v001",
    "with",
}


def _package_folders(root: Path, selected_folders: list[str]) -> list[str]:
    folders = list(dict.fromkeys(selected_folders))
    for selected in selected_folders:
        base = root if selected == "." else root / selected
        if not base.exists():
            continue
        for manifest in base.rglob("MANIFEST.md"):
            rel = manifest.parent.relative_to(root).as_posix()
            folder = "." if rel == "." else rel
            if selected == "." and "/" in folder:
                continue
            folders.append(folder)
            if len(folders) >= PACKAGE_RANK_SCAN_CAP:
                break
    return list(dict.fromkeys(folders))


def _rank_packages(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(
        rows,
        key=lambda row: (
            row.get("recommended_mode") != "self_managed",
            row.get("scan_cap_hit", False),
            row.get("overcap_file_count", 0),
            row.get("resistance_score", 1),
            -row.get("autonomy_score", 0),
            row.get("external_edge_count", 0),
            row.get("folder", ""),
        ),
    )
    ranked = []
    for idx, row in enumerate(ordered[:30], start=1):
        ranked.append({"rank": idx, **row})
    return ranked


def _folder_of(rel: str) -> str:
    parent = Path(rel.strip("\"'")).parent.as_posix()
    return "." if parent in {"", "."} else parent


def _belongs(rel: str, folder: str) -> bool:
    clean = rel.replace("\\", "/").strip("/")
    folder = folder.strip("/")
    return bool(clean) and (folder in {"", "."} or clean == folder or clean.startswith(folder + "/"))


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["build_folder_context_coupling", "render_folder_context_coupling"]
