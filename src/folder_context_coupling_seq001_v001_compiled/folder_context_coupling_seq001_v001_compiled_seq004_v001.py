"""folder_context_coupling_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .folder_context_coupling_seq001_v001_compiled_seq009_v001 import _folder_of
from collections import defaultdict
from typing import Any

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
