import json
import tempfile
from pathlib import Path

from src.actual_job_runner_seq001_v001 import run_actual_jobs


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="actual_jobs_"))
    (root / "logs").mkdir()
    (root / "src").mkdir()
    (root / "src" / "target.py").write_text("def ok():\n    return True\n", encoding="utf-8")
    (root / "test_target.py").write_text(
        "from src.target import ok\n\n"
        "def test_ok():\n"
        "    assert ok() is True\n",
        encoding="utf-8",
    )
    (root / "logs" / "file_self_knowledge_latest.json").write_text(json.dumps({
        "packets": [
            {
                "packet_id": "fsk-target",
                "file": "src/target.py",
                "mutation_scope": {"readiness": "draft_ready"},
                "known_failures": ["prior_learning_outcome:actual_job_fail", "prior_learning_outcome:actual_job_pass"],
                "validates_with": [
                    "py -m py_compile src/target.py",
                    "py -m pytest test_target.py -q",
                    "py -m pytest missing_test.py -q",
                ],
                "relationships": [{"file": "test_target.py"}],
                "source_evidence": {"identity_growth_events": 2},
                "owns": ["validation target"],
            }
        ]
    }), encoding="utf-8")
    (root / "logs" / "batch_rewrite_sim_latest.json").write_text(json.dumps({
        "proposals": [
            {
                "path": "src/target.py",
                "confidence": 0.8,
                "reward": 0.7,
                "decision": "safe_dry_run",
                "proposed_fix": "tiny deterministic fix",
                "validation_plan": ["py -m py_compile src/target.py"],
            }
        ]
    }), encoding="utf-8")
    return root


def test_actual_job_runner_executes_real_validation_and_records_outcomes():
    root = _repo()

    result = run_actual_jobs(root, write=True, timeout_s=30)

    assert result["schema"] == "actual_job_runner/v1"
    assert result["selected_count"] == 1
    assert result["passed_count"] == 1
    assert result["failed_count"] == 0
    assert result["high_confidence_fixes"][0]["file"] == "src/target.py"
    job = result["jobs"][0]
    assert "missing_test.py" not in " ".join(job["commands"])
    assert job["blocking_failures"] == []
    assert job["status"] == "passed"
    assert job["outcome_reward"] > job["confidence"]
    assert (root / "logs" / "actual_job_runner_latest.json").exists()
    outcomes = (root / "logs" / "file_self_sim_learning_outcomes.jsonl").read_text(encoding="utf-8")
    assert "actual_job_pass" in outcomes
