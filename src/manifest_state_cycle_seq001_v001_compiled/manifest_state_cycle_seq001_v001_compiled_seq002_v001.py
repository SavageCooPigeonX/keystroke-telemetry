"""manifest_state_cycle_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any

def render_manifest_state_write(result: dict[str, Any]) -> str:
    lines = [
        "# Manifest State Write Cycle",
        "",
        f"- status: `{result.get('status')}`",
        f"- prompt_hash: `{result.get('prompt_hash')}`",
        f"- rule: {result.get('rule')}",
        "",
        "## File Writes",
        "",
    ]
    for row in result.get("file_writes") or []:
        lines.append(f"- `{row.get('file')}` -> `{row.get('manifest')}` changed={row.get('changed')} reason={row.get('reason')}")
    if not result.get("file_writes"):
        lines.append("- `none`")
    lines.extend(["", "## Selected Manifests", ""])
    for row in result.get("selected_manifests") or []:
        lines.append(f"- `{row.get('manifest')}` source={row.get('source')} score={row.get('score', '')}")
    lines.extend(["", "## Manifest Syntax", ""])
    for row in (result.get("manifest_syntax_match") or {}).get("selected_manifests", [])[:10]:
        lines.append(f"- `{row.get('manifest')}` {row.get('classification')} tokens={', '.join(row.get('matched_tokens') or [])}")
    lines.extend(["", "## Folder Coupling", ""])
    for row in (result.get("folder_context_coupling") or {}).get("folders", [])[:10]:
        lines.append(f"- `{row.get('folder')}` autonomy={row.get('autonomy_score')} resistance={row.get('resistance_score')} mode={row.get('recommended_mode')}")
    return "\n".join(lines) + "\n"


def _selected_files(packet: dict[str, Any], syntax_files: list[dict[str, Any]]) -> list[str]:
    protocol = packet.get("manifest_state_protocol") or {}
    files = []
    for boundary in protocol.get("write_boundary") or []:
        folder = str(boundary.get("folder") or "")
        if folder:
            files.append(f"{folder}/MANIFEST.md")
    files.extend(str(row.get("file") or "") for row in syntax_files)
    files.extend(str(row.get("path") or "") for row in packet.get("file_name_changelog") or [])
    return [rel for rel in dict.fromkeys(file.replace("\\", "/") for file in files) if rel]
