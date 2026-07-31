"""unified_manifest_state_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _bug_chat_rows
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _bug_rows
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _folder_rows
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _latest_protocol
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _replace_block
from .unified_manifest_state_seq001_v001_compiled_seq005_v001 import _state_files
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import MASTER_END
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import MASTER_START
from .unified_manifest_state_seq001_v001_compiled_seq006_v001 import _load_json
from pathlib import Path
import json
import re

def append_master_persistent_state(root: Path, content: str, changed: list[str]) -> str:
    content = _replace_block(content, MASTER_START, MASTER_END, "")
    protocol = _latest_protocol(root)
    prompt_packet = _load_json(root / "logs" / "prompt_context_packet_latest.json") or {}
    lines = [
        MASTER_START,
        "## Master Persistent State",
        "",
        "- state_doc: `MANIFEST.md`",
        "- role: `opus_master_manifest_project_structure_and_persistent_state`",
        "- folder_state_contract: `each folder writes one MANIFEST.md`",
        f"- latest_prompt_hash: `{prompt_packet.get('prompt_hash', '')}`",
        f"- manifest_gate: `{protocol.get('status', 'unknown')}`",
        "",
        "### Project Structure",
        "",
        "| Folder | Manifest | Changed In Scope |",
        "|---|---|---:|",
    ]
    for row in _folder_rows(root, changed)[:80]:
        lines.append(f"| `{row['folder']}` | `{row['manifest']}` | {row['changed_count']} |")
    lines.extend(["", "### Master Intent Keys", ""])
    for key in protocol.get("master_intent_keys", [])[:20]:
        lines.append(f"- `{key}`")
    if not protocol.get("master_intent_keys"):
        lines.append("- `none-current`")
    lines.extend(["", "### Surfaced Bug Queue", ""])
    for bug in _bug_rows(root)[:12]:
        lines.append(f"- `{bug.get('severity')}` `{bug.get('owner')}` {bug.get('title')} :: {bug.get('next_action')}")
    if not _bug_rows(root):
        lines.append("- `none-surfaced`")
    lines.extend(["", "### File Bug Chat", ""])
    for row in _bug_chat_rows(root)[:6]:
        lines.append(f"- `{row.get('owner')}` {row.get('operator_comedy')}")
    if not _bug_chat_rows(root):
        lines.append("- `none-generated`")
    key = _load_json(root / "logs" / "root_sim_key_file_latest.json") or {}
    lines.extend(["", "### Root Sim Key File", ""])
    lines.append(f"- `ROOT_SIM_KEYS.md` :: called={key.get('called_count', 0)}")
    pulse = _load_json(root / "logs" / "opus_micro_pulse_latest.json") or {}
    cannon = pulse.get("cannon_job") or {}
    lines.extend(["", "### Opus Micro-Pulse Runtime", ""])
    if pulse:
        lines.append(
            f"- `logs/opus_micro_pulse_latest.json` :: class={cannon.get('prompt_class')} "
            f"executor={cannon.get('executor_session')} predicted={len(cannon.get('predicted_files') or [])}"
        )
    else:
        lines.append("- `none-generated`")
    gate = _load_json(root / "logs" / "cannon_execution_gate_latest.json") or {}
    lines.extend(["", "### Cannon Execution Gate", ""])
    if gate:
        lines.append(
            f"- `logs/cannon_execution_gate_latest.json` :: status={gate.get('status')} "
            f"payload_ready={str(gate.get('payload_ready')).lower()} predicted={gate.get('predicted_file_count', 0)}"
        )
        if gate.get("blockers"):
            for blocker in gate.get("blockers", [])[:8]:
                lines.append(f"  - blocker: `{blocker}`")
    else:
        lines.append("- `blocked` :: cannon gate has not been configured")
    lines.extend(["", "### Persistent State Files", ""])
    for rel in _state_files():
        exists = (root / rel).exists()
        lines.append(f"- `{rel}` :: exists={str(exists).lower()}")
    lines.append(MASTER_END)
    return content.rstrip() + "\n\n" + "\n".join(lines) + "\n"
