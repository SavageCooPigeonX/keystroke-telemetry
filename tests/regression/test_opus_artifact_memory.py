import json
import subprocess
import tempfile
from pathlib import Path

from src.opus_artifact_memory_seq001_v001 import build_opus_artifact_memory


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="opus_artifact_memory_"))
    (root / "src").mkdir()
    (root / "logs").mkdir()
    (root / "build" / "compressed").mkdir(parents=True)
    (root / "src" / "hot.py").write_text("def hot():\n    return 1\n", encoding="utf-8")
    (root / "src" / "silent.py").write_text("def silent():\n    return 2\n", encoding="utf-8")
    (root / "logs" / "prompt_telemetry_latest.json").write_text(json.dumps({
        "latest_prompt": {
            "ts": "2026-05-05T00:00:00+00:00",
            "preview": "find dead files",
            "files_open": ["src/hot.py"],
        },
        "deleted_words": ["old"],
    }), encoding="utf-8")
    (root / "logs" / "file_intelligence_graph_latest.json").write_text(json.dumps({
        "focus_files": ["src/hot.py", "src/silent.py"],
    }), encoding="utf-8")
    (root / "logs" / "file_self_knowledge_latest.json").write_text(json.dumps({
        "packets": [{
            "file": "src/hot.py",
            "file_quote": "hot file wants a test before mutation",
            "mutation_scope": {"readiness": "draft_ready"},
        }],
    }), encoding="utf-8")
    (root / "logs" / "training_pairs.jsonl").write_text(
        json.dumps({"ts": "2026-05-04T00:00:00+00:00"}) + "\n",
        encoding="utf-8",
    )
    (root / "logs" / "edit_pairs.jsonl").write_text(
        json.dumps({"file": "src/hot.py"}) + "\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.local"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=root, check=True, capture_output=True)
    return root


def test_opus_artifact_memory_reports_hot_dead_and_compiler_probe():
    root = _repo()

    result = build_opus_artifact_memory(root, "simulate compiler telemetry", write=True, commit_limit=5)

    assert result["schema"] == "opus_artifact_memory/v1"
    assert result["high_touch_files"][0]["file"] == "src/hot.py"
    assert any(row["file"] == "src/hot.py" for row in result["file_death_areas"])
    assert result["compiler_probe"]["status"] == "needs_wiring"
    assert "hot file wants a test" in result["file_dialogue"][0]["quote"]
    assert (root / "logs" / "opus_artifact_memory_latest.json").exists()
    assert "Opus Artifact Memory" in (root / "logs" / "opus_artifact_memory.md").read_text(encoding="utf-8")
