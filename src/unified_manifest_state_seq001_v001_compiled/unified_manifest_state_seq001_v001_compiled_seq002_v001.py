"""unified_manifest_state_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _bug_chat_rows
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _latest_protocol
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _syntax_rows
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import FOLDER_END
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import FOLDER_START
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import _belongs
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import _cell
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import _load_json
from pathlib import Path
import json
import re

def render_folder_unified_state(root: Path, folder: str, changed: list[str]) -> str:
    protocol = _latest_protocol(root)
    own = "MANIFEST.md" if folder in {"", "."} else f"{folder}/MANIFEST.md"
    touched = [rel for rel in changed if _belongs(rel, folder)]
    read_set = [row.get("manifest") for row in protocol.get("read_set", [])]
    external = [rel for rel in read_set if rel and rel != own][:12]
    syntax = _syntax_rows(root, folder)
    lines = [
        FOLDER_START,
        "## Folder Unified State",
        "",
        f"- state_doc: `{own}`",
        "- write_authority: `own_folder_manifest_only`",
        "- read_authority: `selected_manifest_read_only`",
        f"- changed_files_in_scope: `{len(touched)}`",
        "",
        "### Local Files Learning Here",
        "",
        "| File | Observations | Learned Trigger Sample |",
        "|---|---:|---|",
    ]
    for row in syntax[:10]:
        learned = ", ".join((row.get("learned_operator_tokens") or [])[:8]) or "none"
        lines.append(f"| `{row.get('file')}` | {row.get('observations', 0)} | {_cell(learned)} |")
    if not syntax:
        lines.append("| `none` | 0 | no syntax trigger state for this folder yet |")
    lines.extend(["", "### Cross-Folder Manifests Read In Sim", ""])
    for rel in external:
        lines.append(f"- `{rel}`")
    if not external:
        lines.append("- `none-selected`")
    local_chats = [row for row in _bug_chat_rows(root) if _belongs(str(row.get("owner") or ""), folder)]
    lines.extend(["", "### Local Bug Chat", ""])
    for row in local_chats[:8]:
        lines.append(f"- `{row.get('owner')}` {row.get('operator_comedy')}")
        if row.get("coding_agent_note"):
            lines.append(f"  - coding_agent: {row.get('coding_agent_note')}")
    if not local_chats:
        lines.append("- `none-local`")
    key_state = _load_json(root / "logs" / "root_sim_key_file_latest.json") or {}
    attention = {row.get("file"): row.get("attention_slot") for row in key_state.get("attention_plan") or []}
    receipts = [row for row in key_state.get("called_files") or [] if _belongs(str(row.get("file") or ""), folder)]
    lines.extend(["", "### Live Sim Call Receipts", ""])
    for row in receipts[:12]:
        lines.append(f"- `{row.get('file')}` kind={row.get('kind')} attention={attention.get(row.get('file'), 'not_selected')} :: {_cell(row.get('why'))}")
    if not receipts:
        lines.append("- `none-called`")
    lines.extend(["", "### Local Write Queue", ""])
    for rel in touched[:12]:
        lines.append(f"- `{rel}` -> `{own}`")
    if not touched:
        lines.append("- `no-local-file-touch-this-cycle`")
    lines.append(FOLDER_END)
    return "\n".join(lines)
