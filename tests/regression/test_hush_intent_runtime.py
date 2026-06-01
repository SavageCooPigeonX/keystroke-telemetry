import json
from pathlib import Path

from src.hush_intent_runtime_seq001_v001 import build_hush_intent_runtime, classify_active_repo


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


def test_hush_routes_maif_social_sb_opus_rerun_without_live_logs(tmp_path: Path):
    (tmp_path / "logs").mkdir()

    result = classify_active_repo(
        tmp_path,
        "fix data in sb and rerun Opus 4.8 so MAIF social posts answer in the proper tone",
    )

    assert result["active_repo"] == "maif_auditor"
    assert result["mutation_fence"] == "open"
    assert result["repo_confidence"] >= 0.22


def test_hush_runtime_splits_messy_prompt_and_writes_file_packets(tmp_path: Path):
    root = _root(tmp_path)
    prompt = (
        "Hush needs persistent intent reconstruction, repo classification for LinkRouter MAIF files, "
        "MAIF social post reruns in Supabase, emails with useful text, Inator file identity names, "
        "and future whisper IRT field intent."
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

    runtime = build_hush_intent_runtime(root, prompt)

    names = {move["name"] for move in runtime["intent_moves"]}
    assert {
        "hush_intent_runtime",
        "repo_classification",
        "linkrouter_file_room_access",
        "maif_social_post_rerun",
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
    assert (root / "logs" / "hush_intent_runtime_latest.json").exists()
