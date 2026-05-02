from pathlib import Path

from src import deepseek_daemon_seq001_v001 as daemon


def _patch_roots(monkeypatch, root: Path):
    logs = root / "logs"
    monkeypatch.setattr(daemon, "ROOT", root)
    monkeypatch.setattr(daemon, "LOGS", logs)
    monkeypatch.setattr(daemon, "PROMPT_RESULTS", logs / "deepseek_prompt_results.jsonl")
    monkeypatch.setattr(daemon, "ARTIFACT_LOG", logs / "deepseek_artifact_writes.jsonl")


def test_prompt_job_can_write_guarded_markdown_artifact(tmp_path, monkeypatch):
    _patch_roots(monkeypatch, tmp_path)
    monkeypatch.setattr(
        daemon,
        "_call_deepseek",
        lambda system, user, api_key, max_tokens=2000, model=None: "# Meta Analysis\n\nDeepSeek wrote the doc.",
    )
    work = {
        "key": "prompt:artifact-unit",
        "stem": "meta",
        "intent": "write a repo meta-analysis markdown artifact",
        "job": {
            "job_id": "artifact-unit",
            "prompt": "write a repo meta-analysis markdown artifact",
            "mode": "research_md_artifact",
            "write_artifact": True,
            "artifact_path": "logs/deepseek_artifacts/meta_analysis.md",
            "focus_files": [],
            "model": "unit-model",
        },
    }

    result = daemon._do_prompt_job(work, api_key="unit", dry_run=False)

    target = tmp_path / "logs" / "deepseek_artifacts" / "meta_analysis.md"
    assert result["success"] is True
    assert result["artifact_written"] is True
    assert result["artifact"]["artifact_path"] == "logs/deepseek_artifacts/meta_analysis.md"
    assert target.exists()
    assert "# Meta Analysis" in target.read_text(encoding="utf-8")


def test_prompt_artifact_blocks_paths_outside_allowed_dirs(tmp_path, monkeypatch):
    _patch_roots(monkeypatch, tmp_path)
    monkeypatch.setattr(
        daemon,
        "_call_deepseek",
        lambda system, user, api_key, max_tokens=2000, model=None: "# Should Not Write",
    )
    work = {
        "key": "prompt:artifact-blocked",
        "stem": "meta",
        "intent": "try writing outside artifact lane",
        "job": {
            "job_id": "artifact-blocked",
            "prompt": "try writing outside artifact lane",
            "mode": "research_md_artifact",
            "write_artifact": True,
            "artifact_path": "src/should_not_write.md",
            "focus_files": [],
            "model": "unit-model",
        },
    }

    result = daemon._do_prompt_job(work, api_key="unit", dry_run=False)

    assert result["success"] is True
    assert result["artifact_written"] is False
    assert result["artifact"]["status"] == "blocked"
    assert not (tmp_path / "src" / "should_not_write.md").exists()


def test_run_cycle_prioritizes_live_prompt_artifact_over_code_completion(monkeypatch):
    seen = []
    monkeypatch.setattr(
        daemon,
        "_prompt_job_work",
        lambda attempted: [{
            "type": "prompt_coding_context",
            "stem": "artifact_prompt",
            "intent": "live artifact job",
            "job": {"job_id": "prompt-artifact"},
            "key": "prompt:artifact",
            "priority": 0,
        }],
    )
    monkeypatch.setattr(
        daemon,
        "_code_completion_job_work",
        lambda attempted: [{
            "type": "prompt_coding_context",
            "stem": "old_code_completion",
            "intent": "older file sim completion",
            "job": {"job_id": "code-completion"},
            "key": "code:completion",
            "priority": 2,
        }],
    )
    monkeypatch.setattr(daemon, "_rejected_patch_work", lambda attempted: [])
    monkeypatch.setattr(daemon, "_pigeon_compliance_work", lambda attempted: [])
    monkeypatch.setattr(daemon, "_intent_work", lambda attempted: [])
    monkeypatch.setattr(daemon, "_log", lambda entry: None)

    def fake_do_prompt_job(work, api_key, dry_run):
        seen.append(work["stem"])
        return {"success": True, "reason": "unit"}

    monkeypatch.setattr(daemon, "_do_prompt_job", fake_do_prompt_job)

    processed = daemon.run_cycle(api_key="unit", dry_run=False, already_attempted=set())

    assert processed == 1
    assert seen == ["artifact_prompt"]


def test_reasoning_artifact_jobs_get_larger_token_budget():
    assert daemon._prompt_max_tokens({"mode": "research_md_artifact"}, "deepseek-v4-pro") == 8000
    assert daemon._prompt_max_tokens({"mode": "probe_push_cycle"}, "deepseek-v4-pro") == 6000
    assert daemon._prompt_max_tokens({"mode": "research_md_artifact", "max_tokens": 1234}, "deepseek-v4-pro") == 1234


def test_autonomous_write_uses_approved_file_overwriter_path(tmp_path, monkeypatch):
    _patch_roots(monkeypatch, tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    target = src / "target_module.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    calls = []

    class FakeOverwriter:
        @staticmethod
        def overwrite_file(*args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            return {"applied": True, "diff": "unit", "error": ""}

    monkeypatch.setattr(daemon, "_call_deepseek", lambda *args, **kwargs: "<<<SEARCH\nVALUE = 1\n===\nVALUE = 2\n>>>REPLACE")
    monkeypatch.setattr(daemon, "_load_glob_module", lambda folder, pattern: FakeOverwriter)

    result = daemon._do_prompt_job({
        "key": "prompt:approved-write",
        "stem": "target_module",
        "intent": "apply approved source repair",
        "job": {
            "job_id": "approved-write",
            "prompt": "apply approved source repair",
            "focus_files": ["src/target_module.py"],
            "autonomous_write": True,
        },
    }, api_key="unit", dry_run=False)

    assert result["success"] is True
    assert calls
    assert calls[0]["kwargs"]["approved"] is True
    assert calls[0]["kwargs"]["target_path"] == "src/target_module.py"
    assert calls[0]["kwargs"]["grade_result"]["approved"] is True
    assert calls[0]["kwargs"]["_patch_override"].startswith("<<<SEARCH")
