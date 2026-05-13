import json
from datetime import datetime, timedelta, timezone

from src.opus_training_pair_debug_seq001_v001 import debug_training_pairs


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_debug_training_pairs_explains_stale_upstream_edit_pairs(tmp_path):
    logs = tmp_path / "logs"
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=2)
    _write_jsonl(logs / "prompt_journal.jsonl", [{"ts": now.isoformat(), "session_n": 7}])
    _write_jsonl(logs / "edit_pairs.jsonl", [{"ts": old.isoformat(), "file": "src/old.py"}])
    _write_jsonl(logs / "training_pairs.jsonl", [{"ts": old.isoformat(), "session_n": 3}])
    (logs / "deepseek_prompt_latest.json").write_text(json.dumps({"ts": now.isoformat(), "job_id": "ds"}), encoding="utf-8")

    result = debug_training_pairs(tmp_path)

    assert result["status"] == "blocked_upstream_edit_pairs_stale"
    assert result["failed_steps"]
    assert "edit-pair" in result["recommended_fix"]
    assert (logs / "opus_training_pair_debug_latest.json").exists()
