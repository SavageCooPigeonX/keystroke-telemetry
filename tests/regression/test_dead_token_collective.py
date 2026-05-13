import json
import subprocess
import tempfile
from pathlib import Path

from src.dead_token_collective_seq001_v001 import collect_dead_token_history


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _commit(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-m", message)


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="dead_token_repo_"))
    _git(root, "init")
    _git(root, "config", "user.email", "collector@example.test")
    _git(root, "config", "user.name", "Collector Test")
    (root / "src").mkdir()
    (root / "docs" / "push_narratives").mkdir(parents=True)
    (root / "docs" / "self_fix").mkdir(parents=True)
    (root / "docs" / "push_narratives" / "2026-04-28_abc1234.md").write_text("push narrative", encoding="utf-8")
    (root / "docs" / "self_fix" / "2026-04-28_abc1234_self_fix.md").write_text("self fix", encoding="utf-8")
    (root / "src" / "intent_numeric.py").write_text("def predict_files():\n    return []\n", encoding="utf-8")
    _commit(root, "feat: add numeric intent surface")
    (root / "src" / "intent_numeric.py").rename(
        root / "src" / "intent_numeric_seq001_v001__word_number_file_mapping.py"
    )
    _commit(root, "chore: rename intent numeric into file identity")
    (root / "src" / "intent_numeric_seq001_v001__word_number_file_mapping.py").write_text(
        "def predict_files(prompt=''):\n    return [prompt]\n",
        encoding="utf-8",
    )
    _commit(root, "fix: patch numeric prompt prediction")
    return root


def test_collect_dead_token_history_writes_pairs_and_narrative():
    root = _repo()

    summary = collect_dead_token_history(root, write=True)

    assert summary["stats"]["commits_seen"] == 3
    assert summary["stats"]["rename_events"] == 1
    assert summary["stats"]["push_narratives"] == 1
    pairs = (root / "logs" / "dead_token_collective_pairs.jsonl").read_text(encoding="utf-8").splitlines()
    rename_pair = next(json.loads(line) for line in pairs if '"event_type": "rename"' in line)
    assert rename_pair["old_identity"] == "intent_numeric"
    assert rename_pair["new_identity"].startswith("intent_numeric_seq001")
    assert rename_pair["intent_key"].startswith("src:rename:")
    narrative = (root / "logs" / "dead_token_collective.md").read_text(encoding="utf-8")
    assert "Dead Token Collective" in narrative
    assert "Q1" in narrative
