import json

from src.file_blank_sheet_sim_seq001_v001 import build_file_blank_sheet_sim


def test_blank_sheet_sim_lets_files_choose_pressure_without_source_write(tmp_path):
    src = tmp_path / "src"
    logs = tmp_path / "logs"
    src.mkdir()
    logs.mkdir()
    (src / "router.py").write_text("def route():\n    return True\n", encoding="utf-8")
    (logs / "prompt_journal.jsonl").write_text(json.dumps({"msg": "router needs its own test pressure"}) + "\n", encoding="utf-8")
    (logs / "codex_edit_outcomes.jsonl").write_text(json.dumps({"files": ["src/router.py"]}) + "\n", encoding="utf-8")
    (logs / "file_self_sim_learning_latest.json").write_text(json.dumps({
        "wake_order": [{"file": "src/router.py", "wake_reason": "rename history says router owns intent"}],
    }), encoding="utf-8")

    result = build_file_blank_sheet_sim(tmp_path, write=True)

    job = result["file_pressure_jobs"][0]
    assert job["file"] == "src/router.py"
    assert job["approval_required"] == ["file_sim", "opus_grader", "validation"]
    assert result["approval_gate"]["direct_source_write"] is False
    assert (logs / "file_blank_sheet_sim_latest.json").exists()
