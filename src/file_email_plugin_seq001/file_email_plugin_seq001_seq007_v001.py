"""file_email_plugin_seq001_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq001_v001 import load_file_email_config
from .file_email_plugin_seq001_seq001_v001 import merge_file_email_config
from .file_email_plugin_seq001_seq008_v001 import _codex_prompt_focus_files
from .file_email_plugin_seq001_seq008_v001 import _codex_prompt_job_id
from .file_email_plugin_seq001_seq008_v001 import _codex_prompt_reason
from .file_email_plugin_seq001_seq009_v001 import _codex_prompt_guard
from .file_email_plugin_seq001_seq009_v001 import _codex_prompt_ten_q
from .file_email_plugin_seq001_seq014_v001 import emit_file_email
from .file_email_plugin_seq001_seq051_v001 import _enabled
from pathlib import Path
from typing import Any
import json
import re

def emit_codex_prompt_email(
    root: Path,
    prompt_entry: dict[str, Any],
    loop: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit the one-per-Codex-prompt operator receipt.

    This is intentionally local/dev-control-plane mail, not Hush/web-chat mail.
    """
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    if not _enabled(config, "codex_prompt"):
        return {"status": "skipped", "reason": "disabled", "phase": "codex_prompt"}
    loop = loop if isinstance(loop, dict) else {}
    prompt = str(prompt_entry.get("msg") or prompt_entry.get("prompt") or "").strip()
    context = prompt_entry.get("context_selection") if isinstance(prompt_entry.get("context_selection"), dict) else {}
    file_sim = prompt_entry.get("file_sim") if isinstance(prompt_entry.get("file_sim"), dict) else {}
    focus_files = _codex_prompt_focus_files(context, file_sim, loop)
    source = str(prompt_entry.get("source") or loop.get("source") or "codex")
    intent_key = str(loop.get("intent_key") or ((file_sim.get("intent") or {}).get("intent_key") if isinstance(file_sim.get("intent"), dict) else "") or prompt_entry.get("intent") or "codex:prompt:receipt")
    event = {
        "trigger": "codex_prompt",
        "event_type": "codex_prompt",
        "file": "orchestrator/codex_prompt",
        "intent_key": intent_key,
        "target_state": "codex_prompt_operator_receipt",
        "decision": "prompt_received",
        "interlink_score": context.get("confidence", 0),
        "beef_with": loop.get("loop_id") or "missing_codex_prompt_receipt",
        "reason": _codex_prompt_reason(prompt_entry, prompt, source, loop),
        "deepseek_completion_job_id": _codex_prompt_job_id(file_sim),
        "context_injection": focus_files[:10] or ["logs/prompt_journal.jsonl", "logs/intent_loop_latest.json"],
        "validation_plan": [
            "prompt receipt recorded",
            "operator-visible Codex email emitted",
            "intent loop remains approval gated",
        ],
        "ten_q": _codex_prompt_ten_q(prompt, source, loop),
        "orchestrator_email_guard": _codex_prompt_guard(),
    }
    return emit_file_email(root, event=event, config=config)
