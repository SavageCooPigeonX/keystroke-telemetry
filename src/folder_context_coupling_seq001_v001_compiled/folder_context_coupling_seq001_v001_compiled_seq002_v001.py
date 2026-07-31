"""folder_context_coupling_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any

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
