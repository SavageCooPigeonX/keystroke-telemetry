import json
import subprocess
import tempfile
from pathlib import Path

from src.batch_rewrite_sim_seq001_v001 import (
    load_file_sim_config,
    should_fire_file_sim,
    simulate_batch_rewrites,
)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="batch_rewrite_sim_"))
    _git(root, "init")
    _git(root, "config", "user.email", "sim@example.test")
    _git(root, "config", "user.name", "Batch Sim Test")
    (root / "logs").mkdir()
    (root / "src" / "thought").mkdir(parents=True)
    (root / "src" / "thought" / "MANIFEST.md").write_text("# Thought\nintent routing\n", encoding="utf-8")
    (root / "src" / "thought" / "router.py").write_text("def route_intent(x):\n    return x\n", encoding="utf-8")
    (root / "test_router.py").write_text("from src.thought.router import route_intent\n", encoding="utf-8")
    (root / "logs" / "intent_key_latest.json").write_text(json.dumps({
        "prompt": "compile intent propose fixes orchestrator validation",
        "intent_key": "src/thought:build:intent_rewrite_sim:major",
        "scope": "src/thought",
        "target": "intent_rewrite_sim",
        "confidence": 0.42,
        "manifest_path": "src/thought/MANIFEST.md",
    }), encoding="utf-8")
    (root / "logs" / "context_selection.json").write_text(json.dumps({
        "files": [{"name": "router", "score": 0.7}]
    }), encoding="utf-8")
    pair = {
        "event_type": "patch",
        "new_path": "src/thought/router.py",
        "intent_key": "src/thought:patch:route_intent:patch",
        "subject": "fix: route intent through validator",
    }
    (root / "logs" / "dead_token_collective_pairs.jsonl").write_text(json.dumps(pair) + "\n", encoding="utf-8")
    (root / "logs" / "dead_token_collective_history.json").write_text(json.dumps({
        "top_churn_files": [{"path": "src/thought/router.py", "churn": 10}]
    }), encoding="utf-8")
    (root / "logs" / "self_fix_accuracy.json").write_text(json.dumps({
        "avg_fix_rate": 0.25,
        "persistent_top_10": [{"module": "router", "status": "chronic"}],
    }), encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "seed repo")
    return root


def test_batch_rewrite_sim_is_proposal_only_and_writes_outputs():
    root = _repo()

    result = simulate_batch_rewrites(root, "compile intent propose fixes", limit=3, write=True)

    assert result["mode"] == "source_rewrite_orchestration"
    assert result["target_state"] == "interlinked_source_state"
    assert result["orchestrator"]["orchestrator_only"] is True
    assert result["orchestrator"]["email_per_prompt"] is True
    assert result["orchestrator"]["auto_write_allowed"] is False
    assert result["proposals"]
    top = result["proposals"][0]
    assert top["path"] == "src/thought/router.py"
    assert top["rewrite_target_type"] == "source"
    assert top["target_state"] == "interlinked_source_state"
    assert top["interlink_score"] > 0
    assert top["approval_gate"] == "operator_required"
    assert "src/thought/router.py" in top["context_injection"]
    assert any("py_compile" in step for step in top["validation_plan"])
    assert top["ten_q"]["passed"] is True
    assert top["ten_q"]["score"] >= 7
    assert top["orchestrator_email_guard"]["decision"] == "allow_email"
    assert top["deepseek_completion_job_id"].startswith("dsc-")
    assert result["orchestrator_oath"]["schema"] == "orchestrator_dev_oath/v1"
    assert result["deepseek_code_completion"]["status"] == "queued"
    council = result["file_job_council"]
    assert council["schema"] == "file_job_council/v1"
    assert council["jobs"]
    assert council["context_packs"]
    assert council["total_estimated_tokens"] > 0
    assert council["jobs"][0]["total_estimated_tokens"] > 0
    assert "friendships" in council["comedy_summary"]
    assert (root / "logs" / "batch_rewrite_sim_latest.json").exists()
    assert (root / "logs" / "batch_rewrite_sim.md").exists()
    assert (root / "logs" / "file_job_council_latest.json").exists()
    assert "File Job Council" in (root / "logs" / "batch_rewrite_sim.md").read_text(encoding="utf-8")


def test_file_sim_config_controls_fire_policy():
    root = Path(tempfile.mkdtemp(prefix="file_sim_config_"))

    config = load_file_sim_config(root)

    assert config["enabled"] is True
    assert "pre_prompt" in config["fire_on"]
    assert config["orchestrator_policy"]["orchestrator_only"] is True
    assert should_fire_file_sim(config, "pre_prompt", "compile intent") is True
    assert should_fire_file_sim(config, "os_hook_auto", "compile intent") is True
    assert should_fire_file_sim({"enabled": True, "fire_on": ["pre_prompt"], "min_chars": 1}, "os_hook_auto", "compile intent") is True

    config["enabled"] = False
    assert should_fire_file_sim(config, "pre_prompt", "compile intent") is False
