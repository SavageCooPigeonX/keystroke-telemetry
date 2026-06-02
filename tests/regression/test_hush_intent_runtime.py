import json
from pathlib import Path

from src.mira_runtime_seq001_v001 import build_mira_runtime, classify_active_repo


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _root(tmp_path: Path) -> Path:
    (tmp_path / "logs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "file_sim.py").write_text("def wake():\n    return True\n", encoding="utf-8")
    _write_json(
        tmp_path / "logs" / "repo_fingerprint_maif_auditor.json",
        {
            "schema": "repo_fingerprint/v1",
            "label": "maif_auditor",
            "privacy": "closed",
            "files_indexed": 3,
            "files": [
                {"identity": "maif_auditor_directory_route_entity"},
                {"identity": "maif_auditor_production_auditor_pipeline"},
                {"identity": "maif_auditor_hush_chat_core"},
            ],
        },
    )
    return tmp_path


def test_hush_routes_maif_hush_entity_prompt_to_linkrouter_room(tmp_path: Path):
    root = _root(tmp_path)

    result = classify_active_repo(root, "Hush should inspect MAIF entity directory audit routing")

    assert result["active_repo"] == "maif_auditor"
    assert result["mutation_fence"] == "open"
    assert result["repo_confidence"] >= 0.22


def test_hush_routes_keystroke_file_sim_prompt_to_local_repo(tmp_path: Path):
    root = _root(tmp_path)

    result = classify_active_repo(root, "keystroke telemetry file sim orchestrator prompt encoding")

    assert result["active_repo"] == "keystroke_telemetry"
    assert result["mutation_fence"] == "open"


def test_hush_blocks_ambiguous_context0_without_repo_lock(tmp_path: Path):
    root = _root(tmp_path)

    result = classify_active_repo(root, "context0")

    assert result["active_repo"] == "ambiguous"
    assert result["mutation_fence"] == "blocked"


def test_mira_runtime_splits_messy_prompt_and_writes_file_packets(tmp_path: Path):
    root = _root(tmp_path)
    prompt = (
        "MIRA needs persistent intent reconstruction, repo classification for LinkRouter MAIF files, "
        "emails with useful text, Inator file identity names, and future whisper IRT field intent."
    )
    with (root / "logs" / "prompt_journal.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"msg": prompt, "intent": "building", "deleted_words": ["jarvis"]}) + "\n")
    _write_json(
        root / "logs" / "file_self_sim_learning_latest.json",
        {
            "wake_order": [
                {
                    "file": "src/file_sim.py",
                    "wake_reason": "file sim substrate requested",
                    "tests": ["test_file_sim.py"],
                }
            ],
            "learning_packets": [
                {
                    "file": "src/file_sim.py",
                    "responsibility_profile": {"declared_role": "file substrate wake loop"},
                }
            ],
        },
    )

    runtime = build_mira_runtime(root, prompt)

    names = {move["name"] for move in runtime["intent_moves"]}
    assert {
        "mira_runtime",
        "repo_classification",
        "linkrouter_file_room_access",
        "file_mail_quality_gate",
        "file_identity_narrative",
        "field_whisper_irt_future_layer",
    }.issubset(names)
    assert runtime["file_packets"]
    packet = runtime["file_packets"][0]
    assert packet["file_identity"]
    assert packet["operator_display_name"]
    assert packet["current_responsibility"]
    assert packet["last_change_state"]
    assert packet["validation_gate"]
    assert runtime["name"] == "MIRA"
    assert runtime["full_name"] == "Memory Intent Reconstruction Agent"
    assert runtime["loop"] == ["Map", "Infer", "Reconstruct", "Align"]
    assert (root / "logs" / "mira_runtime_latest.json").exists()
    assert (root / "logs" / "hush_intent_runtime_latest.json").exists()


def test_mira_runtime_hands_maif_prompts_to_hush_entity_sim(tmp_path: Path):
    root = _root(tmp_path)

    runtime = build_mira_runtime(
        root,
        "Hush entity sim for Audit SavageCooPigeonX marked staged docs copy file",
    )

    assert runtime["role"] == "memory_intent_reconstruction_agent"
    assert runtime["interface_surface"] == "opus_codebase_runtime"
    assert runtime["runtime_authority"]["mode"] == "maif_information_interface"
    assert runtime["runtime_authority"]["source_mutation_allowed"] is False
    assert runtime["entity_sim"]
    assert runtime["frontend_cards"]
    assert runtime["hush_frontend_interface"]["frontend_intent"] == "entity_sim"
    assert runtime["hush_frontend_interface"]["assistant"] == "Hush"


def test_mira_blocks_creative_no_research_prompt_as_artifact_only(tmp_path: Path):
    root = _root(tmp_path)
    prompt = "write a max length unhinged comedy about proactive intent probes no research"

    runtime = build_mira_runtime(root, prompt)

    names = {move["name"] for move in runtime["intent_moves"]}
    assert "creative_artifact_only" in names
    authority = runtime["runtime_authority"]
    assert authority["mutation_fence"] == "blocked"
    assert authority["mode"] == "creative_artifact_only"
    assert authority["source_mutation_allowed"] is False
    assert runtime["intent_probe_capability"]["egress"] == "none"
