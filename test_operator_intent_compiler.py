import json
import tempfile
from pathlib import Path

from src.operator_intent_compiler_seq001_v001 import compile_operator_intent


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="operator_intent_compile_"))
    logs = root / "logs"
    logs.mkdir()
    prompts = [
        "make repo self heal with intent graph and validation",
        "thought completer should catch pauses and unsaid intent",
        "file sims should organize jobs and 10q consensus",
        "email should be file memory not notification",
        "split repo if closed context leaks into this project",
    ]
    for idx, prompt in enumerate(prompts, 1):
        _append_jsonl(logs / "prompt_journal.jsonl", {
            "ts": f"2026-04-30T00:0{idx}:00+00:00",
            "msg": prompt,
            "intent": "unknown" if idx < 3 else "building",
            "cognitive_state": "focused",
            "signals": {"deletion_ratio": 0.1},
        })
        _append_jsonl(logs / "chat_compositions.jsonl", {
            "ts": f"2026-04-30T00:0{idx}:01+00:00",
            "final_text": prompt,
            "deletion_ratio": 0.1,
            "deleted_words": [],
            "intent_deleted_words": [],
        })
    (logs / "context_selection.json").write_text(json.dumps({
        "confidence": 0.05,
        "stale_blocks": ["operator-state"],
    }), encoding="utf-8")
    (logs / "intent_loop_latest.json").write_text(json.dumps({
        "status": "awaiting_operator_approval",
        "stage": "human_intent_compiled",
        "observed_edits": [],
        "observed_responses": [],
    }), encoding="utf-8")
    (logs / "batch_rewrite_sim_latest.json").write_text(json.dumps({
        "self_model": {"dirty_files": ["a.py"] * 12},
        "proposals": [{
            "ten_q_score": None,
            "ten_q_passed": None,
            "validation_plan": ["py -m pytest test_missing.py"],
        }],
    }), encoding="utf-8")
    (logs / "dead_stale_code_audit_latest.json").write_text(json.dumps({
        "findings_count": 300,
        "category_counts": {"stale_suspect": 40},
    }), encoding="utf-8")
    return root


def test_compile_operator_intent_reports_alive_blockers_and_writes_artifacts():
    root = _root()

    report = compile_operator_intent(root, prompt_limit=888, write=True)

    names = {item["name"] for item in report["missing_alive_loop"]}
    assert report["available_prompt_count"] == 5
    assert report["coverage_gap"] == 883
    assert "capture_retention_gap" in names
    assert "context_selection_too_weak" in names
    assert "loop_has_no_execution_muscle" in names
    assert "validation_plans_reference_missing_tests" in names
    assert report["bucket_hits"]["repo_self_healing"]["hits"] > 0
    assert (root / "logs" / "operator_intent_888.json").exists()
    md = (root / "logs" / "operator_intent_888.md").read_text(encoding="utf-8")
    assert "Why The Repo Is Not Alive Yet" in md
