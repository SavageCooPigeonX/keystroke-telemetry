"""file_email_plugin_seq001_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq001_v001 import load_file_email_config
from .file_email_plugin_seq001_seq001_v001 import merge_file_email_config
from .file_email_plugin_seq001_seq016_v001 import render_learning_digest_email
from .file_email_plugin_seq001_seq017_v001 import _response_policy_snapshot
from .file_email_plugin_seq001_seq018_v001 import _learning_context_files
from .file_email_plugin_seq001_seq018_v001 import _learning_interlink_score
from .file_email_plugin_seq001_seq018_v001 import _learning_packet_summary
from .file_email_plugin_seq001_seq018_v001 import _learning_validation_plan
from .file_email_plugin_seq001_seq019_v001 import _learning_digest_10q
from .file_email_plugin_seq001_seq032_v001 import _write_context_request
from .file_email_plugin_seq001_seq034_v001 import _file_mail_memory_hint
from .file_email_plugin_seq001_seq035_v001 import _write_file_mail_memory
from .file_email_plugin_seq001_seq041_v001 import _operator_state_snapshot
from .file_email_plugin_seq001_seq047_v001 import _deliver_resend
from .file_email_plugin_seq001_seq049_v001 import _write_outbox
from .file_email_plugin_seq001_seq051_v001 import _enabled
from .file_email_plugin_seq001_seq052_v001 import SCHEMA
from .file_email_plugin_seq001_seq052_v001 import _append_jsonl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import re

def emit_learning_digest_email(
    root: Path,
    learning_result: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit one narrative operator email from the file self-learning run."""
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    if not _enabled(config, "learning_digest"):
        return {"status": "skipped", "reason": "disabled", "count": 0}
    now = datetime.now(timezone.utc)
    intent = learning_result.get("intent") if isinstance(learning_result.get("intent"), dict) else {}
    wake_order = learning_result.get("wake_order") if isinstance(learning_result.get("wake_order"), list) else []
    packets = learning_result.get("learning_packets") if isinstance(learning_result.get("learning_packets"), list) else []
    top_file = str((wake_order[0] or {}).get("file") if wake_order else "orchestrator/file_self_learning")
    digest = hashlib.sha256(
        json.dumps(
            {
                "intent": intent.get("intent_key"),
                "top_file": top_file,
                "packets": [packet.get("packet_id") for packet in packets[:10] if isinstance(packet, dict)],
                "ts": learning_result.get("ts"),
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()[:16]
    record = {
        "schema": SCHEMA,
        "ts": now.isoformat(),
        "id": f"file-email:{digest}",
        "trigger": "learning_digest",
        "event_type": "learning_digest",
        "file": "orchestrator/file_self_learning",
        "from": f"file.self.learning@{config.get('sender_domain', 'files.local')}",
        "to": config.get("recipient", "operator@local"),
        "subject": "the files held a rewrite meeting and the grader stole the gavel",
        "beef_with": "grader/master_plan",
        "intent_key": intent.get("intent_key", ""),
        "target_state": learning_result.get("target_state", "interlinked_source_state"),
        "decision": learning_result.get("mode", "learning_only_no_overwrite"),
        "interlink_score": _learning_interlink_score(learning_result),
        "reason": "narrative learning digest for file self-sim orchestration",
        "deepseek_completion_job_id": _learning_packet_summary(packets),
        "context_injection": _learning_context_files(learning_result),
        "validation_plan": _learning_validation_plan(packets),
        "ten_q": _learning_digest_10q(learning_result),
        "orchestrator_email_guard": {
            "schema": "orchestrator_email_guard/v1",
            "aligned": True,
            "decision": "allow_email",
            "policy": "learning_digest_operator_visible",
            "reason": "learning digest is operator-facing control-plane mail",
        },
        "learning_digest": {
            "raw_intent": intent.get("raw", ""),
            "wake_order": wake_order[:12],
            "packets": packets[:12],
            "paths": learning_result.get("paths", {}),
            "backward_learning_pass": learning_result.get("backward_learning_pass", {}),
            "interlink_plan": learning_result.get("interlink_plan", {}),
        },
    }
    record["operator_state"] = _operator_state_snapshot(root, record)
    record["operator_response_policy"] = _response_policy_snapshot(root, record, surface="file_mail_learning_digest")
    record["mail_memory"] = _file_mail_memory_hint(root, config, record)
    record["context_request"] = _write_context_request(root, config, record, record)
    body = render_learning_digest_email(record)
    paths = _write_outbox(root, config, record, body, now)
    (root / "logs" / "file_self_sim_learning_email.md").write_text(body, encoding="utf-8")
    record["paths"] = paths | {"learning_digest": "logs/file_self_sim_learning_email.md"}
    record["mail_memory"] = _write_file_mail_memory(root, config, record, body, paths)
    record["resend"] = _deliver_resend(root, config, record, body)
    _append_jsonl(root / "logs" / "file_email_outbox.jsonl", record)
    return {"status": "ok", "count": 1, "record": record}
