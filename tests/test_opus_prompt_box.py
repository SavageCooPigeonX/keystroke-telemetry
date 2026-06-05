import json
import tempfile
from pathlib import Path

from src.opus_prompt_box_seq001_v001 import MAX_OPEN_PROBLEMS, refine_opus_prompt_box
from src.opus_orchestrator_runtime_seq001_v001 import build_opus_orchestrator_runtime
from src.tc_intent_keys_seq001_v001 import generate_intent_key


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="opus_prompt_box_"))
    (root / ".github").mkdir()
    (root / ".github" / "copilot-instructions.md").write_text("# Copilot\n", encoding="utf-8")
    (root / "task_queue.json").write_text('{"tasks": []}\n', encoding="utf-8")
    (root / "MANIFEST.md").write_text("# Root\n", encoding="utf-8")
    scope = root / "src" / "thought_completer"
    scope.mkdir(parents=True)
    (scope / "MANIFEST.md").write_text(
        "# Thought Completer\nOwns prompt composer, intent key generation, and prompt box routing.\n",
        encoding="utf-8",
    )
    (root / "src" / "thought_completer.py").write_text("# thought completer\n", encoding="utf-8")
    (root / "src" / "tc_intent_keys_seq001_v001.py").write_text("# intent keys\n", encoding="utf-8")
    return root


def test_intent_key_queues_candidate_and_opus_writes_prompt_box():
    root = _root()
    result = generate_intent_key(
        root,
        "wire thought completer intent key generation to prompt box",
        emit_prompt_box=True,
    )
    assert result["prompt_box"]["status"] == "candidate"

    box = refine_opus_prompt_box(root, "wire thought completer intent key generation to prompt box")
    assert box["writer"] == "claude-opus"
    assert box["open_count"] >= 1
    assert (root / "logs" / "copilot_prompt_box_latest.md").exists()
    tasks = json.loads((root / "task_queue.json").read_text(encoding="utf-8"))
    assert tasks["writer"] == "claude-opus"
    assert any(t.get("source") == "opus_orchestrator" for t in tasks["tasks"])


def test_prompt_box_caps_at_twenty_with_tax_dropoff():
    root = _root()
    (root / "task_queue.json").write_text(
        json.dumps({
            "tasks": [
                {
                    "id": f"ik-{idx:03d}",
                    "status": "pending",
                    "title": f"legacy task {idx}",
                    "intent_key": f"root:patch:task_{idx}:minor",
                    "priority": "low",
                    "confidence": 0.1 + idx * 0.001,
                    "created_ts": "2020-01-01T00:00:00+00:00",
                }
                for idx in range(25)
            ]
        }),
        encoding="utf-8",
    )
    box = refine_opus_prompt_box(root, "", max_open=MAX_OPEN_PROBLEMS)
    assert box["open_count"] == MAX_OPEN_PROBLEMS
    assert box["dropped_count"] == 5
    open_ids = {row["id"] for row in box["open_problems"]}
    assert len(open_ids) == MAX_OPEN_PROBLEMS


def test_opus_runtime_refines_prompt_box_each_build():
    root = _root()
    logs = root / "logs"
    logs.mkdir()
    (logs / "prompt_journal.jsonl").write_text(
        json.dumps({"msg": "opus routes intent keys across project", "session_n": 1}) + "\n",
        encoding="utf-8",
    )
    (logs / "dynamic_context_pack.json").write_text("{}", encoding="utf-8")
    (logs / "file_self_knowledge_latest.json").write_text('{"packets": []}', encoding="utf-8")
    (logs / "file_deepseek_delegate_latest.json").write_text('{"jobs": []}', encoding="utf-8")
    (logs / "file_self_sim_learning_latest.json").write_text("{}", encoding="utf-8")

    runtime = build_opus_orchestrator_runtime(root, "opus routes intent keys across project")
    assert runtime["opus_prompt_box"]["writer"] == "claude-opus"
    assert (logs / "opus_prompt_box_latest.json").exists()
