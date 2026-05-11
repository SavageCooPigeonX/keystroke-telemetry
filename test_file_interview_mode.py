import json

from src.file_interview_mode_seq001_v001 import interview_files


def test_file_interview_writes_file_voice_and_latest_outputs(tmp_path):
    root = tmp_path
    src = root / "src"
    logs = root / "logs"
    src.mkdir()
    logs.mkdir()
    target = src / "sample_seq001_v001.py"
    target.write_text('"""Sample file voice."""\n\nVALUE = 1\n', encoding="utf-8")
    (logs / "operator_response_policy_latest.json").write_text(
        json.dumps(
            {
                "file_comments": [
                    {
                        "file": "src/sample_seq001_v001.py",
                        "file_says": "Sample says it can answer.",
                        "file_fix_proposal": "I think the fix is: keep my test narrow.",
                        "fix_grade": {"decision": "codex_can_act_after_review"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = interview_files(root, question="what do you know", files=["src/sample_seq001_v001.py"])

    assert report["files_interviewed"] == 1
    assert report["answers"][0]["file_says"] == "Sample file voice."
    assert report["answers"][0]["i_think_fix_is"] == "I think the fix is: keep my test narrow."
    assert (logs / "file_interview_latest.json").exists()
    assert (logs / "file_interview_latest.md").exists()


def test_file_interview_resolves_aliases(tmp_path):
    root = tmp_path
    current = root / "src" / "current_seq001_v002.py"
    current.parent.mkdir()
    current.write_text('"""Current identity."""\n', encoding="utf-8")
    logs = root / "logs"
    logs.mkdir()
    (logs / "file_identity_aliases.json").write_text(
        json.dumps(
            {
                "schema": "file_identity_aliases/v1",
                "aliases": {
                    "src/old_seq001_v001.py": {
                        "current_file": "src/current_seq001_v002.py",
                        "current_files": ["src/current_seq001_v002.py"],
                        "source_file": "src/old_seq001_v001.py",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    report = interview_files(root, question="where are you", files=["src/old_seq001_v001.py"], write=False)

    assert report["answers"][0]["file"] == "src/current_seq001_v002.py"
    assert report["answers"][0]["rename_identity"]["current_file"] == "src/current_seq001_v002.py"
