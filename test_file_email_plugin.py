import json
import tempfile
from pathlib import Path

from src.batch_rewrite_sim_seq001_v001 import simulate_batch_rewrites
from src.file_email_plugin_seq001_v001 import (
    email_delivery_status,
    emit_codex_prompt_email,
    emit_file_email,
    emit_file_sim_emails,
    emit_prompt_lifecycle_email,
    emit_touch_email,
    ingest_file_mail_reply,
    load_file_email_config,
)


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="file_email_plugin_"))
    (root / "logs").mkdir()
    (root / "src").mkdir()
    (root / "src" / "router.py").write_text("def route():\n    return True\n", encoding="utf-8")
    (root / "src" / "validator.py").write_text("def validate():\n    return True\n", encoding="utf-8")
    (root / "logs" / "context_selection.json").write_text(json.dumps({
        "files": [{"name": "router", "score": 0.9}],
        "confidence": 0.9,
        "status": "ok",
    }), encoding="utf-8")
    pair = {
        "event_type": "patch",
        "new_path": "src/router.py",
        "intent_key": "src:patch:router:patch",
        "subject": "fix: route intent through validator",
    }
    (root / "logs" / "dead_token_collective_pairs.jsonl").write_text(json.dumps(pair) + "\n", encoding="utf-8")
    return root


def test_touch_email_writes_local_outbox():
    root = _root()
    (root / "logs" / "semantic_profile.json").write_text(json.dumps({
        "schema": "semantic_profile/v1",
        "facts": {"name": {"value": "Nikita"}},
        "intents": {},
    }), encoding="utf-8")
    (root / "logs" / "semantic_profile_latest.json").write_text(json.dumps({
        "semantic_intent": "operator_state_modeling",
        "semantic_intents": ["operator_state_modeling", "telemetry_email", "file_voice_design"],
        "text": "files keep saying theyre not the problem but emails should feel like getting mail from an old friend centered around operatorstate",
    }), encoding="utf-8")

    record = emit_touch_email(
        root,
        "src/router.py",
        why="wire routing",
        prompt="intent context test",
        config={"delivery_mode": "resend_dry_run"},
    )

    assert record["event_type"] == "touch"
    assert record["to"] == "context@myaifingerprint.com"
    assert record["resend"]["status"] == "dry_run"
    assert record["context_request"]["request_id"].startswith("ctx-")
    assert record["operator_response_policy"]["active_arm"]
    assert record["paths"]["eml"].endswith(".eml")
    assert (root / "logs" / "file_email_outbox.jsonl").exists()
    latest = (root / "logs" / "file_email_latest.md").read_text(encoding="utf-8")
    assert "Response policy:" in latest
    assert "I learned:" in latest
    assert "I did:" in latest
    assert "Next I am planning:" in latest
    assert "operator intent: `operator_state_modeling`" in latest
    assert "Reply `avoid: generic status memo`" in latest
    assert "not the problem" not in latest
    assert "10Q INT Context Request" not in latest
    assert "Memory thread:" in latest
    assert record["mail_memory"]["message_count"] == 1
    assert (root / record["mail_memory"]["path"]).exists()
    memory = json.loads((root / record["mail_memory"]["path"]).read_text(encoding="utf-8"))
    assert memory["messages"][0]["direction"] == "outbound"
    assert memory["knowledge"]["last_current_work"]
    payload = json.loads((root / "logs" / "resend_payload_latest.json").read_text(encoding="utf-8"))
    assert payload["payload"]["from"] == "File Comedy <contact@myaifingerprint.com>"
    assert payload["payload"]["to"] == ["context@myaifingerprint.com"]
    assert payload["orchestrator_guard"]["decision"] == "local_only"
    assert (root / "logs" / "context_requests.jsonl").exists()


def test_file_sim_emits_comedy_file_emails():
    root = _root()
    config = {
        "enabled": True,
        "per_fire_limit": 2,
        "triggers": ["file_sim", "touch", "compile"],
        "delivery_mode": "resend_dry_run",
    }

    result = simulate_batch_rewrites(root, "compile intent router validation", limit=2, write=True, config=config)

    assert result["file_email"]["status"] == "ok"
    assert result["file_email"]["count"] >= 1
    assert result["deepseek_code_completion"]["count"] >= 1
    proposal = result["proposals"][0]
    assert proposal["ten_q"]["passed"] is True
    assert proposal["orchestrator_email_guard"]["decision"] == "allow_email"
    assert (root / "logs" / "deepseek_code_completion_jobs.jsonl").exists()
    assert (root / "logs" / "orchestrator_dev_oath.md").exists()
    assert (root / "logs" / "file_push_narrative_fragment.md").exists()
    assert (root / "logs" / "context_requests.jsonl").exists()
    assert load_file_email_config(root)["enabled"] is True
    rows = (root / "logs" / "file_email_outbox.jsonl").read_text(encoding="utf-8").splitlines()
    assert rows
    last = json.loads(rows[-1])
    assert "beef_with" in last
    assert last["ten_q"]["passed"] is True
    assert last["context_request"]["computed_checks"]


def test_file_email_config_migrates_learning_digest_trigger():
    root = _root()
    (root / "logs" / "file_email_config.json").write_text(json.dumps({
        "enabled": True,
        "triggers": ["file_sim", "touch", "compile"],
    }), encoding="utf-8")

    config = load_file_email_config(root)

    assert "learning_digest" in config["triggers"]
    assert "codex_prompt" in config["triggers"]
    saved = json.loads((root / "logs" / "file_email_config.json").read_text(encoding="utf-8"))
    assert "learning_digest" in saved["triggers"]
    assert "codex_prompt" in saved["triggers"]


def test_codex_prompt_email_is_operator_control_plane_mail():
    root = _root()

    record = emit_codex_prompt_email(
        root,
        {
            "msg": "this is a Codex prompt, not a web chat message",
            "source": "codex_explicit",
            "session_n": 7,
            "context_selection": {"confidence": 0.8, "files": [{"name": "src/router.py"}]},
        },
        loop={
            "loop_id": "loop-codex-test",
            "intent_key": "codex:prompt:receipt",
            "human_position": "on_loop",
            "auto_write_allowed": False,
            "focus_files": ["src/router.py"],
        },
        config={"delivery_mode": "resend_dry_run"},
    )

    assert record["event_type"] == "codex_prompt"
    assert record["ten_q"]["passed"] is True
    assert record["resend"]["would_send"] is True
    assert record["orchestrator_email_guard"]["policy"] == "codex_prompt_operator_receipt"
    assert "src/router.py" in record["context_injection"]


def test_resend_real_send_blocks_failed_consensus():
    root = _root()

    record = emit_file_email(
        root,
        {
            "trigger": "file_sim",
            "event_type": "compile",
            "file": "src/router.py",
            "intent_key": "src:patch:router:patch",
            "target_state": "interlinked_source_state",
            "decision": "needs_review",
            "interlink_score": 0.1,
            "reason": "test failed consensus",
            "context_injection": ["src/router.py"],
            "validation_plan": ["py -m py_compile src/router.py"],
            "ten_q": {"passed": False, "score": 3, "max_score": 10, "reason": "score 3/7", "checks": []},
            "orchestrator_email_guard": {
                "aligned": False,
                "decision": "local_only",
                "reason": "10Q consensus failed: score 3/7",
            },
        },
        config={"delivery_mode": "resend"},
    )

    assert record["resend"]["status"] == "blocked_by_orchestrator"
    assert record["resend"]["orchestrator_guard"]["aligned"] is False


def test_file_sim_email_fires_monitor_when_no_proposals():
    root = _root()

    result = emit_file_sim_emails(
        root,
        {
            "trigger": "log_prompt",
            "target_state": "interlinked_source_state",
            "intent": {"intent_key": "src:route:no_candidates:patch"},
            "distributed_intent_encoding": {"file_votes": []},
            "proposals": [],
        },
        config={"delivery_mode": "resend_dry_run"},
    )

    assert result["status"] == "ok"
    assert result["count"] == 1
    record = result["records"][0]
    assert record["file"] == "orchestrator/prompt_monitor"
    assert record["ten_q"]["passed"] is False
    assert record["resend"]["would_send"] is True


def test_prompt_lifecycle_emails_fire_on_submission_and_completion():
    root = _root()
    loop = {
        "loop_id": "loop-test",
        "status": "awaiting_operator_approval",
        "intent_key": "src:route:lifecycle_email:patch",
        "target_state": "interlinked_source_state",
        "prompt": "submission and completion should email",
        "human_position": "on_loop",
        "approval_required": True,
        "auto_write_allowed": False,
        "focus_files": ["src/router.py"],
        "proposals": [],
        "observed_edits": [],
    }

    submission = emit_prompt_lifecycle_email(root, loop, "submission", config={"delivery_mode": "resend_dry_run"})
    loop["status"] = "verified"
    loop["completion_note"] = "stress test passed"
    loop["observed_edits"] = [{"file": "src/router.py"}]
    completion = emit_prompt_lifecycle_email(root, loop, "completion", config={"delivery_mode": "resend_dry_run"})

    assert submission["event_type"] == "submission"
    assert completion["event_type"] == "completion"
    assert submission["resend"]["would_send"] is True
    assert completion["resend"]["would_send"] is True
    rows = [json.loads(line) for line in (root / "logs" / "file_email_outbox.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [row["event_type"] for row in rows[-2:]] == ["submission", "completion"]


def test_prompt_lifecycle_completion_email_lists_failed_checks():
    root = _root()
    loop = {
        "loop_id": "loop-failed-checks",
        "status": "verified",
        "intent_key": "src:validate:missing_bound_edit:patch",
        "target_state": "interlinked_source_state",
        "prompt": "completion should list failed checks",
        "human_position": "on_loop",
        "approval_required": True,
        "auto_write_allowed": False,
        "focus_files": ["src/router.py"],
        "proposals": [],
        "observed_edits": [],
    }

    completion = emit_prompt_lifecycle_email(root, loop, "completion", config={"delivery_mode": "resend_dry_run"})

    assert completion["event_type"] == "completion"
    assert completion["ten_q"]["passed"] is False
    assert completion["resend"]["would_send"] is False
    latest = (root / "logs" / "file_email_latest.md").read_text(encoding="utf-8")
    assert "- failed: `" in latest
    assert "completion_bound" in latest
    assert "training_candidate" in latest
    context_request = json.loads((root / "logs" / "context_request_latest.json").read_text(encoding="utf-8"))
    assert any(item["key"] == "completion_bound" for item in context_request["failed_checks"])


def test_file_mail_reply_updates_long_term_memory():
    root = _root()
    emit_touch_email(
        root,
        "src/router.py",
        why="start memory thread",
        prompt="manage files through email memory",
        config={"delivery_mode": "resend_dry_run"},
    )

    reply = ingest_file_mail_reply(
        root,
        "src/router.py",
        "\n".join([
            "remember: router owns tiny intent dispatch",
            "use: src/validator.py, logs/context_selection.json",
            "avoid: giant schema lecture in visible mail",
            "style: old friend, adaptive to operator rhythm",
            "this thread is the file's long term memory",
        ]),
    )

    assert reply["memory"]["message_count"] == 2
    memory = json.loads((root / reply["memory"]["path"]).read_text(encoding="utf-8"))
    knowledge = memory["knowledge"]
    assert "router owns tiny intent dispatch" in knowledge["operator_notes"]
    assert "src/validator.py" in knowledge["preferred_context"]
    assert "giant schema lecture in visible mail" in knowledge["avoid_rules"]
    assert any("old friend" in item for item in knowledge["style_notes"])
    assert (root / "logs" / "file_memory_index.json").exists()


def test_email_delivery_status_explains_why_resend_does_not_send(monkeypatch):
    root = _root()
    monkeypatch.delenv("FILE_EMAIL_DELIVERY", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM", raising=False)

    status = email_delivery_status(root, config={"delivery_mode": "resend_dry_run"})

    assert status["can_send"] is False
    assert "delivery_mode_is_not_resend" in status["blockers"]
    assert "missing_RESEND_API_KEY" in status["blockers"]
    assert (root / "logs" / "file_email_delivery_status.json").exists()


def test_email_delivery_status_loads_local_env_without_exposing_key(monkeypatch):
    root = _root()
    monkeypatch.delenv("FILE_EMAIL_DELIVERY", raising=False)
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM", raising=False)
    (root / ".env").write_text(
        "FILE_EMAIL_DELIVERY=resend\n"
        "RESEND_API_KEY=re_test_secret\n"
        "RESEND_FROM=File Comedy <contact@myaifingerprint.com>\n",
        encoding="utf-8",
    )

    status = email_delivery_status(root)

    assert status["mode"] == "resend"
    assert status["api_key_present"] is True
    assert status["can_send"] is True
    assert "re_test_secret" not in json.dumps(status)
