import json
import tempfile
from pathlib import Path

from src.tc_prompt_brain_seq001_v001 import assemble_prompt_brain, latest_prompt_brain_block


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="tc_prompt_brain_"))
    (root / ".github").mkdir()
    (root / ".github" / "copilot-instructions.md").write_text("# Copilot\n", encoding="utf-8")
    (root / "task_queue.json").write_text('{"tasks": []}\n', encoding="utf-8")
    (root / "MANIFEST.md").write_text("# Root\nPrompt brain manifest.\n", encoding="utf-8")
    scope = root / "src" / "thought_completer"
    scope.mkdir(parents=True)
    (scope / "MANIFEST.md").write_text(
        "# Thought Completer\n"
        "Prompt brain watcher semantic profile numeric file encoding context selection.\n",
        encoding="utf-8",
    )
    (root / "codex_compat.py").write_text(
        "def select_context(root, prompt, deleted_words=None, rewrites=None):\n"
        "    return {'status':'ok','confidence':0.88,'files':[{'name':'tc_prompt_brain','score':0.88}]}\n"
        "def predict_numeric_files(root, prompt, top_n=6):\n"
        "    return [{'name':'tc_prompt_brain','score':0.77}]\n",
        encoding="utf-8",
    )
    return root


def test_prompt_brain_assembles_full_watcher_context_and_injects():
    root = _root()

    brain = assemble_prompt_brain(
        root,
        "my name is nikita and thought completer needs numeric file encoding",
        source="test",
        trigger="pause",
        emit_prompt_box=True,
        inject=True,
    )

    assert brain["intent_key"].startswith("src/thought_completer:")
    assert brain["semantic_profile"]["semantic_intent"] == "share_information"
    assert brain["operator_profile"]["facts"]["name"]["value"] == "Nikita"
    assert brain["intent_graph"]["intent_count"] >= 1
    assert brain["context_selection"]["status"] == "ok"
    assert brain["numeric_file_encoding"][0]["name"] == "tc_prompt_brain"
    assert brain["prompt_box"]["open_count"] == 1
    assert (root / "logs" / "prompt_brain_latest.json").exists()
    assert "codex:prompt-brain" in (root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")


def test_latest_prompt_brain_block_is_readable_for_thought_completer():
    root = _root()
    assemble_prompt_brain(root, "thought completer context selection", inject=False)

    block = latest_prompt_brain_block(root)

    assert "Prompt Brain" in block
    assert "INTENT_KEY" in block
    assert "INTENT_FILE_MEMORY" in block
    assert "INTENT_GRAPH_MOVES" in block
    assert "FORWARD_CONTEXT_WINDOW" in block
