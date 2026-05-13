import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import codex_compat
from src.intent_loop_closer_seq001_v001 import (
    bind_edit_to_latest_loop,
    bind_response_to_latest_loop,
    close_intent_loop,
    record_intent_loop,
)
from src.intent_outcome_binder_seq001_v001 import match_journal_to_files


def _file_sim() -> dict:
    return {
        "status": "fired",
        "target_state": "interlinked_source_state",
        "intent": {"intent_key": "src/thought:build:intent_loop:patch"},
        "orchestrator": {
            "approval_required": True,
            "auto_write_allowed": False,
        },
        "proposals": [
            {
                "path": "src/thought/router.py",
                "decision": "source_rewrite_candidate",
                "proposed_fix": "bind edit receipts to the active loop",
                "interlink_score": 0.91,
                "approval_gate": "operator_required",
                "deepseek_completion_job_id": "dsc-test",
                "validation_plan": ["py -m py_compile src/thought/router.py"],
                "ten_q": {"score": 10, "passed": True},
                "orchestrator_email_guard": {"decision": "allow_email"},
            }
        ],
    }


def test_intent_loop_opens_binds_edits_and_closes():
    root = Path(tempfile.mkdtemp(prefix="intent_loop_"))

    loop = record_intent_loop(
        root,
        "compile intent and let copilot execute bounded fixes",
        context_selection={"confidence": 0.8, "files": [{"name": "src/thought/router.py"}]},
        file_sim=_file_sim(),
        source="test",
        deleted_words=["rewrite"],
    )

    assert loop["status"] == "awaiting_operator_approval"
    assert loop["human_position"] == "on_loop"
    assert loop["proposals"][0]["ten_q_score"] == 10
    assert loop["submission_email"]["event_type"] == "submission"
    queue = json.loads((root / "task_queue.json").read_text(encoding="utf-8"))
    assert queue["tasks"][0]["intent_loop_id"] == loop["loop_id"]
    assert queue["tasks"][0]["status"] == "pending"

    response_binding = bind_response_to_latest_loop(root, {
        "prompt": loop["prompt"],
        "response": "I will patch router.py and validate it.",
        "response_id": "codex:test",
    })
    assert response_binding["kind"] == "response"

    edit_binding = bind_edit_to_latest_loop(root, {
        "file": "src/thought/router.py",
        "edit_why": "bind receipt to router",
        "source": "copilot",
    })
    assert edit_binding["kind"] == "edit"
    assert edit_binding["alignment"]["score"] == 1.0
    assert (root / "logs" / "intent_loop_training_candidates.jsonl").exists()

    closed = close_intent_loop(root, status="verified", note="tests passed")
    assert closed["status"] == "verified"
    assert closed["completion_email"]["event_type"] == "completion"
    queue = json.loads((root / "task_queue.json").read_text(encoding="utf-8"))
    assert queue["tasks"][0]["status"] == "done"


def test_codex_pre_prompt_writes_intent_loop_into_dynamic_context():
    root = Path(tempfile.mkdtemp(prefix="intent_loop_codex_"))
    (root / ".github").mkdir()
    (root / ".github" / "copilot-instructions.md").write_text("# Copilot\n", encoding="utf-8")

    state = codex_compat.run_pre_prompt_pipeline(
        root,
        "close the human to copilot to repo plugin intent loop",
        deleted_words=["autonomous"],
        run_sim=False,
    )

    assert state["intent_loop"]["loop_id"].startswith("loop-")
    pack = json.loads((root / "logs" / "dynamic_context_pack.json").read_text(encoding="utf-8"))
    assert pack["intent_loop"]["loop_id"] == state["intent_loop"]["loop_id"]
    assert "INTENT_LOOP" in (root / "logs" / "dynamic_context_pack.md").read_text(encoding="utf-8")


def test_intent_outcome_binder_uses_root_when_binding_files():
    root = Path(tempfile.mkdtemp(prefix="intent_binder_root_"))
    now = datetime.now(timezone.utc)
    journal = [{
        "ts": (now - timedelta(minutes=2)).isoformat(),
        "msg": "fix parser file",
        "intent": "debugging",
        "signals": {},
    }]
    stats = [{"file": "src/parser.py", "added": 2, "removed": 1, "before_lines": 3, "after_lines": 4}]

    bindings = match_journal_to_files(root, journal, stats, now)

    assert bindings[0]["file"] == "src/parser.py"
    assert bindings[0]["prompt_intent"] == "debugging"
