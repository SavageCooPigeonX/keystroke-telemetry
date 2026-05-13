import json
from pathlib import Path

from src.file_email_plugin_seq001_v001 import emit_file_email, mail_quality_gate


def test_file_email_reads_like_text_chain_and_keeps_reply_handles(tmp_path: Path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "router.py").write_text("def route():\n    return True\n", encoding="utf-8")

    record = emit_file_email(
        tmp_path,
        {
            "trigger": "file_sim",
            "event_type": "compile",
            "file": "src/router.py",
            "intent_key": "src:patch:router",
            "target_state": "two_way_validation_gate",
            "decision": "safe_dry_run",
            "reason": "router needs validator context before DeepSeek writes",
            "file_comment": "validator should approve me first",
            "context_injection": ["src/router.py", "src/validator.py"],
            "validation_plan": ["py -m py_compile src/router.py"],
            "ten_q": {"passed": True, "score": 10, "max_score": 10},
            "orchestrator_email_guard": {"decision": "allow_email", "aligned": True},
        },
        config={"delivery_mode": "resend_dry_run", "triggers": ["file_sim", "compile"]},
    )

    latest = (tmp_path / "logs" / "file_email_latest.md").read_text(encoding="utf-8")
    assert record["subject"].startswith("group text:")
    assert "File room:" in latest
    assert "router: I heard the complaint" in latest
    assert "router.py: I have beef with `src/validator.py`" in latest
    assert "Opus: Backward pass solution" in latest
    assert "router: Approval -> approved by file checks" in latest
    assert "Grader: open" in latest
    assert "Text back like a message:" in latest
    assert "I need from you:" in latest
    assert "`remember: ...`, `use: ...`, `avoid: ...`, `style: ...`" in latest
    assert "Blank sheet:" in latest
    payload = json.loads((tmp_path / "logs" / "resend_payload_latest.json").read_text(encoding="utf-8"))
    assert "Text back like a message:" in payload["payload"]["text"]


def test_file_email_quality_gate_rejects_empty_status_noise():
    result = mail_quality_gate("From: file\nStatus: done\n")

    assert result["passed"] is False
    assert {"learned", "did", "next", "need"}.issubset(set(result["missing"]))
