import json
from datetime import datetime, timezone
from pathlib import Path

from src.codex_edit_outcome_binder_seq001_v001 import bind_codex_edit_outcome


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_bind_codex_edit_outcome_writes_edit_pairs_without_fake_pulse(tmp_path):
    logs = tmp_path / "logs"
    src = tmp_path / "src"
    src.mkdir()
    (src / "target.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    _write_jsonl(logs / "prompt_journal.jsonl", [{
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_n": 9,
        "msg": "fix target",
        "cognitive_state": "unknown",
    }])

    result = bind_codex_edit_outcome(
        tmp_path,
        ["src/target.py", "missing.py"],
        reason="unit accepted edit",
        capture_training=False,
    )

    assert result["edit_pairs_written"] == 1
    assert result["files"] == ["src/target.py"]
    row = json.loads((logs / "edit_pairs.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert row["source"] == "codex_runtime"
    assert row["session_n"] == 9
    assert row["file_email"]["trigger"] == "codex_edit_outcome"


def test_bind_codex_edit_outcome_can_capture_training_pair(tmp_path):
    logs = tmp_path / "logs"
    src = tmp_path / "src"
    src.mkdir()
    (src / "target.py").write_text("def f():\n    return 2\n", encoding="utf-8")
    _write_jsonl(logs / "prompt_journal.jsonl", [{
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_n": 10,
        "msg": "train target",
        "intent": "debugging",
        "signals": {"deletion_ratio": 0.0, "hesitation_count": 0},
    }])

    result = bind_codex_edit_outcome(tmp_path, ["src/target.py"], reason="training capture test")

    assert result["training_pairs_captured"] == 1
    pair = json.loads((logs / "training_pairs.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert pair["session_n"] == 10
    assert pair["copilot_intent"]["file"] == "src/target.py"
