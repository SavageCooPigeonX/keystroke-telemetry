import json

from src.opus_orchestrator_runtime_seq001_v001 import build_opus_orchestrator_runtime


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_opus_runtime_pairs_thought_completer_with_file_subagents(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    for idx, prompt in enumerate(["pair models", "opus orchestrates", "show last sims"], start=1):
        with (logs / "prompt_journal.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"session_n": idx, "msg": prompt, "intent": "testing", "cognitive_state": "unknown"}) + "\n")
    _write_json(logs / "dynamic_context_pack.json", {
        "context_selection": {"confidence": 0.7, "files": [{"name": "thought_completer", "score": 0.7}]},
        "prompt_brain": {"intent": {"intent_key": "src:route:opus_runtime:patch"}},
    })
    _write_json(logs / "file_self_knowledge_latest.json", {
        "packets": [{
            "file": "src/thought_completer.py",
            "file_quote": "thought_completer can host Opus.",
            "mutation_scope": {"readiness": "draft_ready"},
        }]
    })
    _write_json(logs / "file_deepseek_delegate_latest.json", {
        "jobs": [{"job_id": "fdd-123", "target_file": "src/thought_completer.py"}]
    })
    _write_json(logs / "file_self_sim_learning_latest.json", {
        "mode": "learning_only_no_overwrite",
        "backward_learning_pass": {"status": "armed_waiting_for_outcome"},
    })
    _write_json(logs / "manifest_state_write_latest.json", {
        "status": "manifest_state_written",
        "file_writes": [{"file": "src/thought_completer.py", "manifest": "src/MANIFEST.md", "changed": True}],
        "selected_manifests": [{"manifest": "src/MANIFEST.md", "source": "manifest_read_set"}],
    })

    runtime = build_opus_orchestrator_runtime(tmp_path, "can i talk to opus")

    assert runtime["chat_surface"] == "thought_completer"
    assert runtime["roles"]["orchestrator"] == "claude-opus"
    assert runtime["roles"]["context_selector"] == "gemini"
    assert runtime["file_subagents"][0]["deepseek_job"] == "fdd-123"
    assert runtime["artifact_memory"]["path"] == "logs/opus_artifact_memory_latest.json"
    assert runtime["coding_area_memory"]["path"] == "logs/opus_coding_area_memory_latest.json"
    assert runtime["training_pair_debug"]["path"] == "logs/opus_training_pair_debug_latest.json"
    assert runtime["session_macro_cycle"]["path"] == "logs/session_macro_cycle_latest.json"
    assert runtime["manifest_state_write_cycle"]["status"] == "manifest_state_written"
    assert "Claude Opus may write manifest" in runtime["manifest_write"]["markdown"]
    assert (logs / "opus_artifact_memory_latest.json").exists()
    assert (logs / "opus_coding_area_memory_latest.json").exists()
    assert (logs / "opus_training_pair_debug_latest.json").exists()
    assert (logs / "opus_orchestrator_runtime_latest.json").exists()
    assert (logs / "opus_orchestrator_manifest_note.md").exists()
    assert (logs / "session_macro_cycle_latest.json").exists()
