"""root_sim_key_file_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .root_sim_key_file_seq001_v001_compiled_seq006_v001 import _cell
from typing import Any

def render_root_sim_key_file(result: dict[str, Any]) -> str:
    lines = [
        "# Root Sim Keys",
        "",
        "One root navigation file for every file/key called into the latest sim surfaces.",
        "",
        f"- called: `{result.get('called_count', 0)}`",
        f"- attention_selected: `{result.get('attention_selected_count', 0)}/{result.get('attention_limit', 18)}`",
        f"- generated: `{result.get('ts', '')}`",
        "", "## Attention Plan", "", "| File / Key | Slot | Why |", "|---|---|---|",
    ]
    for row in result.get("attention_plan") or []:
        lines.append(f"| `{row.get('file')}` | {row.get('attention_slot')} | {_cell(row.get('why'))} |")
    lines.extend([
        "",
        "## Called Files / Keys",
        "",
        "| File / Key | Kind | Local Manifest | Why In Sim | Intent Keys |",
        "|---|---|---|---|---|",
    ])
    for row in result.get("called_files") or []:
        lines.append(
            f"| `{row.get('file')}` | {row.get('kind')} | `{row.get('local_manifest')}` | "
            f"{_cell(row.get('why'))} | {_cell(', '.join(row.get('intent_keys') or []), 180)} |"
        )
    lines.extend(["", "## File Comments", ""])
    for row in result.get("called_files") or []:
        if row.get("operator_comment") or row.get("coding_agent_note") or row.get("opus_note"):
            lines.extend([f"### {row.get('file')}", "", f"**Operator Note:** {row.get('operator_comment', '')}", "", f"**Coding Agent Note:** {row.get('coding_agent_note', '')}", "", f"**Opus Note:** {row.get('opus_note', '')}", ""])
    return "\n".join(lines) + "\n"
