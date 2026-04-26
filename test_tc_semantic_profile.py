import json
import tempfile
from pathlib import Path

import codex_compat
from src.tc_intent_keys_seq001_v001 import generate_intent_key
from src.tc_semantic_profile_seq001_v001 import log_semantic_profile_event


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="tc_semantic_profile_"))
    (root / ".github").mkdir()
    (root / ".github" / "copilot-instructions.md").write_text("# Copilot\n", encoding="utf-8")
    (root / "task_queue.json").write_text('{"tasks": []}\n', encoding="utf-8")
    (root / "MANIFEST.md").write_text(
        "# Profile Intent\n"
        "Semantic profile numeric encoding intent key matching thought completer prompts.\n",
        encoding="utf-8",
    )
    return root


def test_greeting_logs_introduction_event():
    root = _root()

    event = log_semantic_profile_event(root, "hi", source="test")

    assert event["semantic_intent"] == "introduction"
    assert event["completion_hint"] == "intent:introduction"
    assert event["numeric_encoding"]["vector"]
    assert (root / "logs" / "semantic_profile_events.jsonl").exists()


def test_share_information_updates_profile_name_fact():
    root = _root()

    event = log_semantic_profile_event(root, "my name is nikita", source="test")
    profile = json.loads((root / "logs" / "semantic_profile.json").read_text(encoding="utf-8"))

    assert event["semantic_intent"] == "share_information"
    assert event["completion_hint"] == "remember:name=Nikita"
    assert profile["facts"]["name"]["value"] == "Nikita"
    assert profile["facts"]["name"]["numeric_encoding"]["hex"]


def test_later_name_reference_attaches_numeric_profile_match_to_intent_key():
    root = _root()
    log_semantic_profile_event(root, "my name is nikita", source="test")

    result = generate_intent_key(root, "nikita needs numeric encoding intent key matching")
    semantic = result["semantic_profile"]

    assert "profile_reference" in semantic["semantic_intents"]
    assert semantic["profile_matches"][0]["fact_type"] == "name"
    assert semantic["profile_matches"][0]["numeric_encoding"]["vector"]
    assert "PROFILE_MATCHES" in (root / "logs" / "intent_key_context.md").read_text(encoding="utf-8")


def test_codex_prompt_logger_runs_semantic_profile_per_prompt():
    root = _root()

    entry = codex_compat.log_prompt(root, "my name is nikita")

    assert entry["semantic_profile"]["semantic_intent"] == "share_information"
    assert (root / "logs" / "semantic_profile_latest.json").exists()
