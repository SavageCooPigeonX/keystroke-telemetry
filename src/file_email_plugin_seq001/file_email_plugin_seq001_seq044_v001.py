"""file_email_plugin_seq001_seq044_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq023_v001 import _format_check_line
from .file_email_plugin_seq001_seq045_v001 import _guard_line
from .file_email_plugin_seq001_seq045_v001 import _ten_q_line
from typing import Any
import json
import re

def _render_context_request(request: dict[str, Any]) -> str:
    lines = [
        "# 10Q INT Context Request",
        "",
        f"- request_id: `{request.get('request_id')}`",
        f"- status: `{request.get('status')}`",
        f"- file: `{request.get('file')}`",
        f"- intent_key: `{request.get('intent_key')}`",
        f"- beef_with: `{request.get('beef_with')}`",
        f"- 10Q consensus: `{_ten_q_line(request)}`",
        f"- orchestrator_email_guard: `{_guard_line(request)}`",
        "",
        "## Questions",
        "",
    ]
    for item in request.get("questions", []):
        computed = item.get("computed") or {}
        suffix = ""
        if computed:
            suffix = f" `{ 'PASS' if computed.get('passed') else 'FAIL' }` {computed.get('reason')}"
        lines.append(f"{item.get('n')}. **{item.get('key')}** - {item.get('question')}{suffix}")
    lines.extend([
        "",
        "## Required Context",
        "",
    ])
    required = request.get("required_context") or []
    lines.extend(f"- `{item}`" for item in required[:12]) if required else lines.append("- none")
    lines.extend([
        "",
        "## Computed Checks",
        "",
    ])
    checks = request.get("computed_checks") or []
    if checks:
        for item in checks[:10]:
            mark = "PASS" if item.get("passed") else "FAIL"
            lines.append(f"- `{mark}` `{item.get('key')}` - {item.get('reason')}")
    else:
        lines.append("- no computed 10Q checks attached")
    failed = request.get("failed_checks") or [item for item in checks if not item.get("passed")]
    lines.extend([
        "",
        "## Failed Checks",
        "",
    ])
    if failed:
        for item in failed[:10]:
            lines.append(_format_check_line(item, "FAIL"))
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Fulfillment Storage",
        "",
        "- JSONL: `logs/context_request_fulfillments.jsonl`",
        "- Per-request markdown/json: `logs/context_requests/`",
        "",
    ])
    return "\n".join(lines)
