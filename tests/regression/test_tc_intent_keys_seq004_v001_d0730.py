import json
import tempfile
from pathlib import Path

from src.opus_prompt_box_seq001_v001 import refine_opus_prompt_box
from src.tc_intent_file_memory_seq001_v001 import match_intent_file_memory
from src.tc_intent_keys_seq001_v001 import generate_intent_graph, generate_intent_key, seed_intent_graphs_from_history


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
        "operator profile routing, intent graph generation, file matching, "
        "and prompt box routing.\n",
        encoding="utf-8",
    )
    files = {
        "src/thought_completer.py": "# completes paused thoughts with analysis\n",
        "src/tc_prompt_composer_seq001_v001.py": "# prompt composer\n",
        "src/tc_semantic_profile_seq001_v001.py": "# operator profile semantic profile\n",
        "src/tc_intent_keys_seq001_v001.py": "# intent graph structured intent key generation\n",
        "src/intent_numeric_seq001_v004.py": "# numeric encoding file matching matrix\n",
        "src/tc_context_agent_seq001_v004.py": "# context select files intent matching\n",
        "hush_runtime/hush_v38/pipeline/hush_router.py": "# hush shard memory writeback recall route\n",
        "src/irt_field_profile_seq001_v001.py": "# irt artifact probe pulse entity field profile\n",
        "pigeon_compiler/compile_lineage.py": "# pigeon compiler compile rename registry import lineage\n",
        "docs/push_narratives/old_generated_state.md": "# old generated state should be stale context\n",
    }
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
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
    assert result["prompt_box"]["status"] == "candidate"
    box = refine_opus_prompt_box(root, "wire thought completer intent key generation to prompt box")
    tasks = json.loads((root / "task_queue.json").read_text(encoding="utf-8"))["tasks"]
    assert any(t.get("intent_key") == result["intent_key"] for t in tasks)
    assert box["writer"] == "claude-opus"
    assert "codex:intent-key-context" in (root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert (root / "logs" / "intent_key_context.md").exists()


def test_intent_key_duplicate_does_not_spam_prompt_box():
    root = _root()

    first = generate_intent_key(root, "wire thought completer intent key generation to prompt box")
    second = generate_intent_key(root, "wire thought completer intent key generation to prompt box")

    assert first["prompt_box"]["status"] == "candidate"
    assert second["prompt_box"]["status"] == "candidate"
    box = refine_opus_prompt_box(root, "wire thought completer intent key generation to prompt box")
    open_keys = [row.get("intent_key") for row in box.get("open_problems") or []]
    assert open_keys.count(first["intent_key"]) == 1


def test_low_manifest_confidence_becomes_void_not_prompt_box_task():
    root = _root()

    result = generate_intent_key(root, "zzzz qqqq unseen phrase", emit_prompt_box=True)

    assert result["void"] is True
    assert result["prompt_box"]["status"] == "skipped"
    tasks = json.loads((root / "task_queue.json").read_text(encoding="utf-8"))["tasks"]
    assert tasks == []


def test_intent_graph_splits_operator_prompt_into_file_matched_moves():
    root = _root()

    graph = generate_intent_graph(
        root,
        "thought completer should build an operator profile, complete paused thoughts with analysis, "
        "get intent graphs from files, match intent keys to files, and use numeric encoding",
        numeric_files=[
            {"name": "src/intent_numeric_seq001_v004.py", "score": 0.8},
            {"name": "missing_maif_noise", "score": 0.7},
        ],
    )

    assert graph["schema"] == "intent_graph/v1"
    assert graph["intent_count"] == 5
    keys = [item["intent_key"] for item in graph["intents"]]
    assert any("operator_profile" in key for key in keys)
    assert any("intent_graph" in key or "structured_intent" in key for key in keys)
    assert any("numeric" in key or "file_matching" in key for key in keys)
    assert all(item["files"] for item in graph["intents"])
    clearing = graph["context_clearing_pass"]
    assert clearing["schema"] == "self_clearing_context/v1"
    assert clearing["context_window_files"]
    assert any(item["file"] == "missing_maif_noise" for item in clearing["deranked_files"])
    assert graph["intent_nodes"]["node_count"] >= 1
    assert graph["intent_profiles_updated"]
    assert (root / "logs" / "intent_graph_context.md").exists()
    assert (root / "logs" / "intent_nodes.json").exists()
    assert (root / "logs" / "intent_map_manifest.md").exists()

    second = generate_intent_graph(
        root,
        "operator profile and numeric file matching should wake the same intent node again",
        numeric_files=[{"name": "src/intent_numeric_seq001_v004.py", "score": 0.8}],
    )

    assert second["intent_node_matches"]
    assert any(match["dominant_files"] for match in second["intent_node_matches"])


def test_intent_graph_learns_which_intent_keys_wake_files_naturally():
    root = _root()
    learned_file = root / "src" / "natural_router_seq001_v001.py"
    learned_file.write_text("# natural router intent file routing memory\n", encoding="utf-8")

    first = generate_intent_graph(
        root,
        "natural intent file routing memory should learn the selected file",
        numeric_files=[{"name": "src/natural_router_seq001_v001.py", "score": 0.95}],
    )

    assert (root / "logs" / "intent_file_memory.json").exists()
    learned = match_intent_file_memory(
        root,
        "natural intent file routing memory",
        intent_key=first["intents"][0]["intent_key"],
    )
    assert learned
    assert learned[0]["file"] == "src/natural_router_seq001_v001.py"

    second = generate_intent_graph(
        root,
        "operator profile and natural intent file routing memory should wake from history",
        numeric_files=[],
    )

    all_files = [file for intent in second["intents"] for file in intent["files"]]
    assert "src/natural_router_seq001_v001.py" in all_files
    assert second["intent_node_matches"]
    assert any(match["dominant_files"] for match in second["intent_node_matches"])


def test_seed_prompts_update_profiles_and_manifest_per_prompt():
    root = _root()
    summary = seed_intent_graphs_from_history(
        root,
        prompts=[
            "context select should route typing speed and deletion pressure into files",
            "pigeon compiler should pair generated code identity with tests and manifests",
        ],
        limit=2,
    )

    assert summary["schema"] == "intent_graph_seed_run/v1"
    assert summary["processed"] == 2
    assert summary["file_reactions"]
    assert summary["intent_profiles_updated"]
    assert (root / "logs" / "intent_graph_seed_latest.json").exists()
    assert (root / "logs" / "intent_map_manifest.json").exists()
    manifest = json.loads((root / "logs" / "intent_map_manifest.json").read_text(encoding="utf-8"))
    assert manifest["file_pairings"]
    assert manifest["files_by_domain"]
    profiles = list((root / "logs" / "intent_profiles").glob("*.json"))
    assert profiles
