"""folder_context_coupling_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .folder_context_coupling_seq001_v001_compiled_seq008_v001 import _read_prefix
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import FILE_SCAN_CAP
from .folder_context_coupling_seq001_v001_compiled_seq010_v001 import OVERCAP_LINE_LIMIT
from pathlib import Path
from typing import Any

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
