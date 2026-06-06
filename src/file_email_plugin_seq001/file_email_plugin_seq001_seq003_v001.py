"""file_email_plugin_seq001_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _proposal_file_comment(proposal: dict[str, Any]) -> str:
    for key in ("file_comment", "file_quote", "comment", "proposed_fix", "reason"):
        value = proposal.get(key)
        if value:
            return str(value)
    ten_q = proposal.get("ten_q") if isinstance(proposal.get("ten_q"), dict) else {}
    if ten_q.get("reason"):
        return str(ten_q.get("reason"))
    return ""
