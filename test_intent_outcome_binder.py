import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src import intent_outcome_binder_seq001_v002_d0510__closes_the_intent_outcome_loop_lc_feat_bind_keystroke_telemetry as binder


def _run_git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(root: Path) -> None:
    _run_git(root, "init")
    _run_git(root, "config", "user.email", "codex@example.test")
    _run_git(root, "config", "user.name", "Codex Test")


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_bind_commit_pairs_file_comments_to_actual_push_outcome(tmp_path):
    _init_repo(tmp_path)
    src_dir = tmp_path / "src"
    logs_dir = tmp_path / "logs"
    src_dir.mkdir()
    logs_dir.mkdir()
    target = src_dir / "example_seq001_v001.py"
    target.write_text("def value():\n    return 1\n", encoding="utf-8")
    _run_git(tmp_path, "add", ".")
    _run_git(tmp_path, "commit", "-m", "initial")

    prompt_ts = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    (logs_dir / "prompt_journal.jsonl").write_text(
        json.dumps(
            {
                "ts": prompt_ts,
                "msg": "fix example outcome binder from file comment",
                "intent": "outcome_binding",
                "module_refs": ["src/example_seq001_v001.py"],
                "files_open": ["src/example_seq001_v001.py"],
                "signals": {"state": "focused", "wpm": 42},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (logs_dir / "operator_response_policy_latest.json").write_text(
        json.dumps(
            {
                "file_comments": [
                    {
                        "path": "src/example_seq001_v001.py",
                        "file_says": "I think the fix is to bind my proposal to the push result.",
                        "file_fix_proposal": "Bind file comments to changed files after commit.",
                        "fix_grade": {"decision": "codex_can_act_after_review"},
                        "backward_pass_learning": {"pattern_tokens": ["outcome_binder", "file_comment"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (logs_dir / "file_solution_backward_pass.jsonl").write_text(
        json.dumps(
            {
                "path": "src/example_seq001_v001.py",
                "pattern_tokens": ["outcome_binder", "file_comment"],
                "note": "Strengthen exact path selection after rename or split.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    target.write_text("def value():\n    return 2\n", encoding="utf-8")
    _run_git(tmp_path, "add", "src/example_seq001_v001.py")
    _run_git(tmp_path, "commit", "-m", "update example binder")

    result = binder.bind_commit(tmp_path, "HEAD", run_rename_guard=False)

    assert result["bound"] == 1
    assert result["outcome_binding"]["outcomes"] == 1
    assert result["outcome_binding"]["strengthened"] == 1
    outcomes = _jsonl(logs_dir / "file_solution_outcomes.jsonl")
    assert outcomes[-1]["file"] == "src/example_seq001_v001.py"
    assert outcomes[-1]["proposed_fix"] == "Bind file comments to changed files after commit."
    memory = json.loads((logs_dir / "file_solution_memory.json").read_text(encoding="utf-8"))
    assert memory["paths"]["src/example_seq001_v001.py"]["strengthen"] == 1
    assert memory["tokens"]["outcome_binder"]["strengthen"] == 1


def test_rename_engine_guard_fires_without_executing_renames(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "guard_seq001_v001.py").write_text("VALUE = 1\n", encoding="utf-8")

    result = binder.run_rename_engine_guard(tmp_path, execute=False)

    assert result["fired"] is True
    assert result["execute"] is False
    assert "valid" in result["import_validation"]
    assert (tmp_path / "src" / "guard_seq001_v001.py").exists()
