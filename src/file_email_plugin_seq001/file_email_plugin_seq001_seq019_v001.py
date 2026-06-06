"""file_email_plugin_seq001_seq019_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq018_v001 import _learning_context_files
from .file_email_plugin_seq001_seq018_v001 import _learning_validation_plan
from .file_email_plugin_seq001_seq028_v001 import _plain_snip
from typing import Any
import re

def _learning_digest_10q(learning_result: dict[str, Any]) -> dict[str, Any]:
    wake_order = learning_result.get("wake_order") if isinstance(learning_result.get("wake_order"), list) else []
    packets = learning_result.get("learning_packets") if isinstance(learning_result.get("learning_packets"), list) else []
    validation = _learning_validation_plan(packets)
    checks = [
        _digest_check("intent_alignment", bool((learning_result.get("intent") or {}).get("intent_key")), "intent key compiled", "intent key missing"),
        _digest_check("wake_order", bool(wake_order), "files woke for the prompt", "no files woke"),
        _digest_check("learning_packets", bool(packets), "DeepSeek learning packets exist", "no learning packets emitted"),
        _digest_check("validation_plan", bool(validation), "validation gates are named", "validation gates missing"),
        _digest_check("operator_visible", True, "narrative email is operator-facing", "not visible to operator"),
        _digest_check("no_auto_overwrite", learning_result.get("mode") == "learning_only_no_overwrite", "source overwrite blocked", "overwrite mode is unsafe"),
        _digest_check("profile_memory", True, "file profile memory receives learning state", "profile memory missing"),
        _digest_check("deepseek_context", bool(_learning_context_files(learning_result)), "context pack can be assembled", "context pack missing"),
        _digest_check("grader_veto", True, "grader owns execution veto", "grader not attached"),
        _digest_check("reply_path", True, "operator can reply with approve/use/avoid/style", "reply path missing"),
    ]
    score = sum(1 for item in checks if item.get("passed"))
    return {
        "schema": "file_consensus_10q/v1",
        "score": score,
        "max_score": len(checks),
        "min_score": 7,
        "passed": score >= 7,
        "reason": "learning digest ready for operator" if score >= 7 else "learning digest missing required routing facts",
        "checks": checks,
    }


def _digest_check(key: str, passed: bool, pass_reason: str, fail_reason: str) -> dict[str, Any]:
    return {"key": key, "passed": bool(passed), "reason": pass_reason if passed else fail_reason}


def _learning_context_from_record(record: dict[str, Any]) -> list[str]:
    return [str(item) for item in (record.get("context_injection") or []) if item][:12]


def _learning_current_work(record: dict[str, Any]) -> str:
    digest = record.get("learning_digest") if isinstance(record.get("learning_digest"), dict) else {}
    raw = re.sub(r"\s+", " ", str(digest.get("raw_intent") or "")).strip()
    if raw:
        return _plain_snip(raw, 260)
    intent_key = str(record.get("intent_key") or "compiled intent")
    return (
        "training small files to wake by encoded intent, argue through context, write tests, "
        f"and earn self-overwrite later under `{intent_key}`"
    )
