"""opus_micro_pulse_runtime_seq001_v001_compiled_seq015_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_micro_pulse_runtime_seq001_v001_compiled_seq016_v001 import _folder_for
from typing import Any
import re

def _append_pulse_folder_block(content: str, folder: str, result: dict[str, Any]) -> str:
    start = "<!-- manifest:opus-micro-pulse-state -->"
    end = "<!-- /manifest:opus-micro-pulse-state -->"
    content = re.sub(rf"\n?{re.escape(start)}.*?{re.escape(end)}\n?", "", content, flags=re.S).rstrip()
    cannon = result.get("cannon_job") or {}
    lines = [
        start,
        "## Opus Micro-Pulse State",
        "",
        f"- prompt_hash: `{result.get('prompt_hash')}`",
        f"- prompt_class: `{cannon.get('prompt_class')}`",
        f"- executor_session: `{cannon.get('executor_session')}`",
        f"- metric: `opus_prediction_vs_executor_diff`",
        "",
        "### Local Pulse Comments",
        "",
    ]
    for pulse in result.get("pulses") or []:
        for item in pulse.get("file_interrogations") or []:
            rel = str(item.get("file") or "")
            if _folder_for(rel) == folder:
                lines.append(f"- `{rel}` {item.get('file_comment')}")
                lines.append(f"  - coding_agent: {item.get('coding_agent_note')}")
    lines.extend(["", "### Pending Backward Pass", ""])
    pending = result.get("pending_backward_learning") or {}
    for rel in pending.get("predicted_files") or []:
        if _folder_for(str(rel)) == folder:
            lines.append(f"- `{rel}` waiting_for_codex_diff")
    lines.append(end)
    return content + "\n\n" + "\n".join(lines) + "\n"
