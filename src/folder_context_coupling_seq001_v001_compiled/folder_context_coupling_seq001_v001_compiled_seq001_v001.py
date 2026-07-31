"""folder_context_coupling_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .folder_context_coupling_seq001_v001_compiled_seq002_v001 import render_folder_context_coupling
from .folder_context_coupling_seq001_v001_compiled_seq003_v001 import _folder_row
from .folder_context_coupling_seq001_v001_compiled_seq004_v001 import _deepseek_packet
from .folder_context_coupling_seq001_v001_compiled_seq004_v001 import _folder_edges
from .folder_context_coupling_seq001_v001_compiled_seq004_v001 import _selected_folders
from .folder_context_coupling_seq001_v001_compiled_seq005_v001 import _manifest_overcap_index
from .folder_context_coupling_seq001_v001_compiled_seq009_v001 import _json
from .folder_context_coupling_seq001_v001_compiled_seq009_v001 import _package_folders
from .folder_context_coupling_seq001_v001_compiled_seq009_v001 import _rank_packages
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import HISTORY
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import LATEST
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import MARKDOWN
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import _append_jsonl
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import _now
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import _write_json
from pathlib import Path
from src.manifest_syntax_matcher_seq001_v001 import match_manifest_syntax
from typing import Any
import json

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
