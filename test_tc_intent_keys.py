import json
import tempfile
from pathlib import Path

from src.tc_intent_keys_seq001_v001 import generate_intent_key


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="tc_intent_keys_"))
    (root / ".github").mkdir()
    (root / ".github" / "copilot-instructions.md").write_text("# Copilot\n", encoding="utf-8")
    (root / "task_queue.json").write_text('{"tasks": []}\n', encoding="utf-8")
    (root / "MANIFEST.md").write_text("# Root\nGeneral repo manifest.\n", encoding="utf-8")
    scope = root / "src" / "thought_completer"
    scope.mkdir(parents=True)
    (scope / "MANIFEST.md").write_text(
        "# Thought Completer\n"
        "Owns prompt composer, manifest matching, semantic intent key generation, "
        "and prompt box routing.\n",
        encoding="utf-8",
    )
    return root


def test_manifest_prompt_generates_scoped_intent_key_and_prompt_box_task():
    root = _root()

    result = generate_intent_key(
        root,
        "wire thought completer intent key generation to prompt box",
        deleted_words=["manifest"],
    )

    assert result["intent_key"].startswith("src/thought_completer:")
    assert result["void"] is False
    assert result["prompt_box"]["status"] == "queued"
    tasks = json.loads((root / "task_queue.json").read_text(encoding="utf-8"))["tasks"]
    assert tasks[-1]["intent_key"] == result["intent_key"]
    assert "codex:intent-key-context" in (root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert (root / "logs" / "intent_key_context.md").exists()


def test_intent_key_duplicate_does_not_spam_prompt_box():
    root = _root()

    first = generate_intent_key(root, "wire thought completer intent key generation to prompt box")
    second = generate_intent_key(root, "wire thought completer intent key generation to prompt box")

    tasks = json.loads((root / "task_queue.json").read_text(encoding="utf-8"))["tasks"]
    assert len(tasks) == 1
    assert second["prompt_box"]["status"] == "duplicate"
    assert second["prompt_box"]["task_id"] == first["prompt_box"]["task_id"]


def test_low_manifest_confidence_becomes_void_not_prompt_box_task():
    root = _root()

    result = generate_intent_key(root, "zzzz qqqq unseen phrase", emit_prompt_box=True)

    assert result["void"] is True
    assert result["prompt_box"]["status"] == "skipped"
    tasks = json.loads((root / "task_queue.json").read_text(encoding="utf-8"))["tasks"]
    assert tasks == []
