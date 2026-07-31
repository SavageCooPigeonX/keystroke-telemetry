"""organization_pass_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .organization_pass_seq001_v001_compiled_seq007_v001 import SKIP_PARTS
from pathlib import Path
from typing import Any
import re

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
