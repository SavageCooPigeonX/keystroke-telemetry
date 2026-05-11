"""Manifest read/write protocol for file-sim prompt execution."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


def build_manifest_state_protocol(root: Path, graph: dict[str, Any], context: dict[str, Any], changed: list[str]) -> dict[str, Any]:
    root = Path(root)
    selected = [_path(row) for row in (context.get("selected_files") or context.get("files") or [])]
    intent_files = [file for intent in graph.get("intents") or [] for file in intent.get("files") or []]
    sim_files = [str(row) for row in dict.fromkeys([*selected, *changed, *intent_files]) if str(row)]
    manifests = _manifest_paths(root, graph, sim_files)
    manifest_syntax = _manifest_syntax(root, graph, context, sim_files, manifests)
    manifests = list(dict.fromkeys([*manifests, *[row.get("manifest", "") for row in manifest_syntax.get("selected_manifests", [])]]))
    return {
        "schema": "manifest_state_protocol/v1",
        "status": "manifest_context_loaded" if manifests else "manifest_context_missing",
        "execution_gate": "codex_or_copilot_must_read_manifests_before_mutation",
        "state_docs": {
            "master": "MANIFEST.md",
            "folder": "one MANIFEST.md per folder",
            "folder_write_rule": "files write learned state only to their folder MANIFEST.md",
        },
        "read_set": [_manifest_row(root, rel) for rel in manifests],
        "write_boundary": _write_boundary(sim_files),
        "master_intent_keys": _master_intent_keys(graph),
        "shattered_intent_keys": _shattered_intent_keys(graph),
        "manifest_syntax_match": manifest_syntax,
        "cross_folder_sim": _cross_folder_sim(sim_files, manifests),
    }


def render_manifest_state_prompt(protocol: dict[str, Any]) -> list[str]:
    lines = [
        "## Manifest State Gate",
        f"- status: `{protocol.get('status')}`",
        "- master state doc: `MANIFEST.md`",
        "- folder state docs: one unified `MANIFEST.md` per folder.",
        "- Codex/Copilot must read the manifest read set before code mutation.",
        "- Files may write learned state only to their own folder manifest.",
        "- Files may read selected external folder manifests during cross-folder sim.",
        "- Opus/master manifest owns master intent key synthesis across folder shards.",
        "",
        "## Manifest Read Set",
    ]
    for row in protocol.get("read_set", [])[:16]:
        lines.append(f"- `{row.get('manifest')}` :: exists={row.get('exists')} hash={row.get('hash')}")
    lines.extend(["", "## Shattered Intent Keys"])
    for row in protocol.get("shattered_intent_keys", [])[:16]:
        lines.append(f"- `{row.get('intent_key')}` -> `{row.get('manifest')}` bins={row.get('numeric_bins')}")
    lines.extend(["", "## Manifest Syntax Matches"])
    for row in (protocol.get("manifest_syntax_match") or {}).get("selected_manifests", [])[:12]:
        lines.append(f"- `{row.get('manifest')}` score={row.get('score')} tokens={', '.join(row.get('matched_tokens') or [])}")
    return lines


def _manifest_syntax(root: Path, graph: dict[str, Any], context: dict[str, Any], files: list[str], manifests: list[str]) -> dict[str, Any]:
    prompt = " ".join([
        str(graph.get("prompt") or ""),
        " ".join(_master_intent_keys(graph)),
        " ".join(files),
    ])
    try:
        from src.manifest_syntax_matcher_seq001_v001 import match_manifest_syntax

        return match_manifest_syntax(root, prompt, limit=8, candidate_manifests=manifests, write=False)
    except Exception as exc:
        return {"schema": "manifest_syntax_match/error", "error": str(exc), "selected_manifests": []}


def _manifest_paths(root: Path, graph: dict[str, Any], files: list[str]) -> list[str]:
    out = ["MANIFEST.md"]
    for intent in graph.get("intents") or []:
        manifest = str(intent.get("manifest_path") or "")
        if manifest:
            out.append(manifest)
    for rel in files:
        path = Path(str(rel).strip("\"'"))
        parts = path.parts
        for index in range(len(parts), 0, -1):
            candidate = Path(*parts[:index]) / "MANIFEST.md"
            if (root / candidate).exists():
                out.append(candidate.as_posix())
                break
    return list(dict.fromkeys(rel.replace("\\", "/") for rel in out if rel))


def _manifest_row(root: Path, rel: str) -> dict[str, Any]:
    path = root / rel
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    return {
        "manifest": rel,
        "exists": path.exists(),
        "hash": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12] if text else "",
        "excerpt": text[:1400],
    }


def _write_boundary(files: list[str]) -> list[dict[str, Any]]:
    folders = sorted({str(Path(str(rel).strip("\"'")).parent).replace("\\", "/") for rel in files if str(rel)})
    rows = []
    for folder in folders:
        if folder and folder != ".":
            rows.append({
                "folder": folder,
                "may_write": f"{folder}/MANIFEST.md",
                "may_read_external_manifests": True,
                "rule": "own_folder_state_only",
            })
    return rows[:40]


def _master_intent_keys(graph: dict[str, Any]) -> list[str]:
    return [str(intent.get("intent_key")) for intent in graph.get("intents") or [] if intent.get("intent_key")]


def _shattered_intent_keys(graph: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for intent in graph.get("intents") or []:
        key = str(intent.get("intent_key") or "")
        rows.append({
            "intent_key": key,
            "segment": intent.get("segment", ""),
            "manifest": intent.get("manifest_path", "MANIFEST.md"),
            "files": intent.get("files", [])[:8],
            "numeric_bins": _bins(_tokens(" ".join([key, str(intent.get("segment") or "")]))),
        })
    return rows


def _cross_folder_sim(files: list[str], manifests: list[str]) -> dict[str, Any]:
    folders = sorted({str(Path(str(rel).strip("\"'")).parent).replace("\\", "/") for rel in files if str(rel)})
    return {
        "selected_folders": [folder for folder in folders if folder and folder != "."][:40],
        "selected_manifests": manifests[:40],
        "learning_rule": "selected folder manifests can teach each other via read-only sim; writes stay local",
    }


def _path(row: Any) -> str:
    if isinstance(row, dict):
        return str(row.get("path") or row.get("file") or row.get("target") or row.get("name") or "")
    return str(row)


def _tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[a-zA-Z0-9]+", text.lower().replace("_", " ")) if len(tok) > 2]


def _bins(tokens: list[str]) -> list[int]:
    bins = [0] * 8
    for tok in tokens:
        bins[int(hashlib.sha256(tok.encode("utf-8")).hexdigest()[:2], 16) % len(bins)] += 1
    return bins
