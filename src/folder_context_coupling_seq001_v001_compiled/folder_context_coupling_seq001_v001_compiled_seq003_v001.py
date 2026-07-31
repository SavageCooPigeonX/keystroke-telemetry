"""folder_context_coupling_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .folder_context_coupling_seq001_v001_compiled_seq004_v001 import _edge_counts
from .folder_context_coupling_seq001_v001_compiled_seq005_v001 import _missing_trigger_repair
from .folder_context_coupling_seq001_v001_compiled_seq005_v001 import _mode
from .folder_context_coupling_seq001_v001_compiled_seq005_v001 import _overcap_files
from .folder_context_coupling_seq001_v001_compiled_seq005_v001 import _repo_file_scan
from .folder_context_coupling_seq001_v001_compiled_seq007_v001 import _folder_identity
from .folder_context_coupling_seq001_v001_compiled_seq009_v001 import _belongs
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import FILE_SCAN_CAP
from pathlib import Path
from typing import Any

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
