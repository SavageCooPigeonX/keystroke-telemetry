import json
import tempfile
from pathlib import Path

from src.pipeline_staleness_audit_seq001_v001 import run_pipeline_staleness_audit


def test_pipeline_staleness_audit_writes_major_file_opinions():
    root = Path(tempfile.mkdtemp(prefix="pipeline_staleness_"))
    (root / "logs").mkdir()
    (root / "src").mkdir()
    (root / "codex_compat.py").write_text("def log_prompt():\n    return True\n", encoding="utf-8")
    (root / "src" / "file_email_plugin_seq001_v001.py").write_text("def emit():\n    return True\n", encoding="utf-8")
    (root / "logs" / "prompt_journal.jsonl").write_text("{}\n", encoding="utf-8")
    (root / "logs" / "operator_intent_888.json").write_text(json.dumps({
        "prompt_coverage": {"available_prompt_count": 2, "requested_prompt_count": 888, "coverage_gap": 886},
        "cognitive_state_counts": {"unknown": 8, "frustrated": 1},
    }), encoding="utf-8")

    result = run_pipeline_staleness_audit(
        root,
        send_file_opinions=True,
        opinion_limit=2,
        delivery_mode="resend_dry_run",
    )

    assert result["cognitive_probe_health"]["status"] == "weak"
    assert result["stale"]
    assert result["email"]["count"] >= 1
    assert result["email"]["records"][0]["event_type"] == "file_opinion"
    assert result["email"]["records"][0]["resend"]["status"] == "dry_run"
    assert (root / "logs" / "pipeline_staleness_audit_latest.json").exists()
