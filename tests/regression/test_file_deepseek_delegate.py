import json

from src.file_deepseek_delegate_seq001_v001 import (
    grade_file_delegate_result,
    queue_file_deepseek_delegates,
)


def _packet():
    return {
        "file": "src/example_seq001_v001.py",
        "owns": ["example routing", "file-local tests"],
        "required_context": ["src/example_seq001_v001.py", "test_example.py", "src/MANIFEST.md"],
        "validates_with": [
            "py -m py_compile src/example_seq001_v001.py",
            "py -m pytest test_example.py -q",
            "git diff --check",
        ],
        "mutation_scope": {"readiness": "draft_ready", "allowed_without_operator": False},
    }


def test_file_delegate_pairs_packet_with_patch_and_test_artifact(tmp_path):
    result = queue_file_deepseek_delegates(
        tmp_path,
        [_packet()],
        intent={"intent_key": "src:test:example_delegate:patch"},
        model_policy={
            "orchestrator_model": "claude-opus-orchestrator",
            "file_reasoning_model": "gemini-file-reasoner",
            "coding_model": "deepseek-v4-pro",
        },
    )

    job = result["jobs"][0]
    assert job["mode"] == "patch_and_test"
    assert job["autonomy_tier"] == 2
    assert job["autonomy_tier"] <= result["grader_contract"]["max_auto_tier_now"]
    assert job["expected_test_files"] == ["test_example.py"]
    assert job["allowed_files"][:2] == ["src/example_seq001_v001.py", "test_example.py"]
    assert job["model"] == "deepseek-v4-pro"
    assert job["file_reasoning_model"] == "gemini-file-reasoner"
    assert result["orchestrator_model"] == "claude-opus-orchestrator"
    assert result["pairing"]["orchestrator"].startswith("Claude Opus")
    assert result["grader_contract"]["direct_overwrite_allowed"] is False
    assert (tmp_path / job["artifact_path"]).exists()

    queued = [
        json.loads(line)
        for line in (tmp_path / "logs" / "deepseek_prompt_jobs.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert queued[-1]["job_id"] == job["job_id"]
    assert queued[-1]["autonomous_write"] is False
    assert queued[-1]["write_artifact"] is True


def test_delegate_grader_keeps_scope_leaks_as_artifacts(tmp_path):
    result = queue_file_deepseek_delegates(tmp_path, [_packet()], write=False)
    job = result["jobs"][0]

    grade = grade_file_delegate_result(
        job,
        changed_files=["src/example_seq001_v001.py", "src/unrelated.py"],
        tests_written=["test_example.py"],
        validations=[{"command": "py -m pytest test_example.py -q", "passed": True}],
    )

    assert grade["accepted"] is False
    assert grade["decision"] == "keep_as_artifact"
    assert grade["out_of_scope"] == ["src/unrelated.py"]


def test_delegate_grader_accepts_bounded_patch_with_test(tmp_path):
    result = queue_file_deepseek_delegates(tmp_path, [_packet()], write=False)
    job = result["jobs"][0]

    grade = grade_file_delegate_result(
        job,
        changed_files=["src/example_seq001_v001.py", "test_example.py"],
        tests_written=["test_example.py"],
        validations=[
            {"command": "py -m py_compile src/example_seq001_v001.py", "passed": True},
            {"command": "py -m pytest test_example.py -q", "passed": True},
        ],
    )

    assert grade["accepted"] is True
    assert grade["decision"] == "eligible_to_apply"
