import json

from src.hourly_deepseek_autonomy_seq001_v001 import run_hourly_deepseek_autonomy
from test_file_self_sim_learning import _repo


def test_hourly_deepseek_autonomy_compiles_intent_queues_job_and_emails():
    root = _repo()
    (root / "logs" / "prompt_journal.jsonl").write_text(
        json.dumps({
            "msg": "deepseek should run hourly autonomous tasks and email me from compiled intent",
            "intent": "building",
        }) + "\n",
        encoding="utf-8",
    )
    (root / "logs" / "chat_compositions.jsonl").write_text(
        json.dumps({"final_text": "compile intent into hourly repo action"}) + "\n",
        encoding="utf-8",
    )

    result = run_hourly_deepseek_autonomy(
        root,
        prompt_limit=8,
        write=True,
        run_validation=False,
        run_deepseek=False,
    )

    assert result["schema"] == "hourly_deepseek_autonomy/v1"
    assert result["intent_compile"]["available_prompt_count"] == 1
    assert result["deepseek_job"]["queued"] is True
    assert result["deepseek_job"]["source"] == "hourly_deepseek_autonomy/v1"
    assert result["deepseek_result"]["status"] == "skipped"
    assert result["email"]["event_type"] == "hourly_autonomy"
    assert result["email"]["resend"]["status"] == "dry_run"
    assert result["email"]["resend"]["would_send"] is True
    assert (root / "logs" / "deepseek_prompt_jobs.jsonl").exists()
    assert (root / "logs" / "hourly_deepseek_autonomy_latest.json").exists()
    latest = json.loads((root / "logs" / "hourly_deepseek_autonomy_latest.json").read_text(encoding="utf-8"))
    assert latest["email"]["event_type"] == "hourly_autonomy"

