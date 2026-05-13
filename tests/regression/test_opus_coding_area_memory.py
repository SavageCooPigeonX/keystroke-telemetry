from src.opus_coding_area_memory_seq001_v001 import build_opus_coding_area_memory


def test_coding_area_memory_searches_keywords_and_proposes_jobs(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "router.py").write_text(
        "def route_training_pair(prompt):\n    return 'training pair binder'\n",
        encoding="utf-8",
    )
    (src / "other.py").write_text("def noop():\n    return None\n", encoding="utf-8")

    memory = build_opus_coding_area_memory(tmp_path, "debug training pair binder", write=True)

    assert memory["blocks"][0]["file"] == "src/router.py"
    assert memory["file_jobs"][0]["target_file"] == "src/router.py"
    assert memory["orchestration_contract"]["direct_opus_code_execution"] is False
    assert (tmp_path / "logs" / "opus_coding_area_memory_latest.json").exists()
