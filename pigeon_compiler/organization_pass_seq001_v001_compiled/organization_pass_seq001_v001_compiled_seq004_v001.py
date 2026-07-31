"""organization_pass_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .organization_pass_seq001_v001_compiled_seq005_v001 import _mode
from .organization_pass_seq001_v001_compiled_seq006_v001 import _folder_of
from .organization_pass_seq001_v001_compiled_seq006_v001 import _operator_label
from .organization_pass_seq001_v001_compiled_seq007_v001 import FileInfo
from .organization_pass_seq001_v001_compiled_seq007_v001 import MAX_PY_LINES
from collections import defaultdict
from pathlib import Path
from typing import Any
import re

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
