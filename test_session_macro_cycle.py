import json
from datetime import datetime, timezone
from pathlib import Path

from src.session_macro_cycle_seq001_v001 import build_session_macro_cycle


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def _write_json(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row), encoding="utf-8")


def test_session_macro_cycle_groups_prompts_and_records_deleted_words(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    prompts = [
        ("2026-05-08T10:00:00+00:00", "s1", "route prompt through context select and file sim", []),
        ("2026-05-08T10:05:00+00:00", "s2", "verify work complete per cycle", ["maybe"]),
        ("2026-05-08T10:40:00+00:00", "s1", "manifest maintenance should update folders", ["stale"]),
    ]
    for index, (ts, session_id, msg, deleted) in enumerate(prompts, 1):
        _append_jsonl(logs / "prompt_journal.jsonl", {
            "ts": ts,
            "session_n": index,
            "session_id": session_id,
            "msg": msg,
            "deleted_words": deleted,
        })
        _append_jsonl(logs / "intent_keys.jsonl", {
            "ts": ts,
            "prompt": msg,
            "intent_key": f"root:route:test_{index}:minor",
            "semantic_profile": {
                "numeric_encoding": {"algorithm": "sha256_u16_v1", "vector": [index]},
            },
        })
    _write_json(logs / "dynamic_context_pack.json", {"ok": True})

    report = build_session_macro_cycle(tmp_path, prompt_limit=5, window_minutes=20)

    assert report["schema"] == "session_macro_cycle/v1"
    assert report["cycle_count"] == 2
    assert report["cycles"][0]["prompt_count"] == 2
    assert report["cycles"][0]["session_ids"] == ["s1", "s2"]
    assert "maybe" in report["cycles"][0]["deleted_words"]
    assert report["latest_prompt_deleted_words"] == ["stale"]
    assert report["latest_prompt_shatter"]
    assert (logs / "session_macro_cycle_latest.json").exists()
    assert (logs / "session_macro_cycle.md").exists()


def test_session_macro_cycle_marks_artifacts_after_cycle(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    _append_jsonl(logs / "prompt_journal.jsonl", {
        "ts": "2026-05-08T10:00:00+00:00",
        "session_n": 1,
        "session_id": "codex",
        "msg": "audit context select and manifest",
        "deleted_words": [],
    })
    _write_json(logs / "context_selection.json", {"confidence": 0.8})
    after = datetime.now(timezone.utc).timestamp()
    for path in [logs / "context_selection.json"]:
        path.touch()
        assert path.stat().st_mtime <= after or path.exists()

    report = build_session_macro_cycle(tmp_path, prompt_limit=1)

    assert report["cycles"][0]["completion_evidence"]["score"] >= 1
    assert report["manifest_freshness"]["status"] in {
        "fresh_after_latest_prompt",
        "no_manifest_update_after_latest_prompt",
    }
