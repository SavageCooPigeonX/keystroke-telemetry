from src.opus_branch_sim_seq001_v001 import grade_opus_branch_sim, simulate_opus_branch_job


def test_opus_branch_sim_builds_compression_rescue_contract(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    sim = simulate_opus_branch_job(tmp_path, "make compression fire for LLM-readable manifests")

    assert sim["orchestrator"] == "claude-opus"
    assert sim["branch_plan"]["mutates_git"] is False
    assert sim["branch_plan"]["branch"] == "codex/opus-sim-context-compression-rescue"
    assert sim["original_monitor"]["veto"].startswith("Claude Opus")
    assert "src/context_compressor_seq001_v001.py" in sim["gemini_context_select"]["focus_files"]
    assert any(job["target_file"] == "src/context_compressor_seq001_v001.py" for job in sim["deepseek_file_pairs"])
    assert "tests/interlink/test_context_compressor.py" in sim["complex_test"]["required_gates"][0]
    assert "manifest/byproduct" in sim["grader_manifest_write"]["markdown"]
    assert (tmp_path / "logs" / "opus_branch_sim_latest.json").exists()
    assert (tmp_path / "logs" / "opus_branch_sim.md").exists()


def test_opus_branch_grade_accepts_only_bounded_validated_branch():
    sim = simulate_opus_branch_job(".", "compression branch", write=False)
    gates = sim["complex_test"]["required_gates"]
    allowed = sim["deepseek_file_pairs"][0]["allowed_files"][:2]

    accepted = grade_opus_branch_sim(sim, {"passed_gates": gates, "changed_files": allowed})
    assert accepted["accepted"] is True
    assert accepted["decision"] == "merge_candidate"

    rejected = grade_opus_branch_sim(sim, {"passed_gates": gates[:-1], "changed_files": [*allowed, "src/random.py"]})
    assert rejected["accepted"] is False
    assert rejected["decision"] == "continue_branch_sim"
    assert rejected["missing_gates"] == ["git diff --check"]
    assert rejected["out_of_scope"] == ["src/random.py"]
