import json

from src.maif_social_opus_rerun_seq001_v001 import build_maif_social_opus_rerun


def test_maif_social_opus_rerun_repairs_exported_bad_tone_rows(tmp_path, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    logs = tmp_path / "logs"
    logs.mkdir()
    export = logs / "maif_social_posts_export.jsonl"
    export.write_text(
        "\n".join([
            json.dumps({
                "id": "post-1",
                "content": "As an AI, here are three important ways to understand the entity audit.",
                "model": "opus-4.8",
                "failure_reason": "tone failed",
            }),
            json.dumps({
                "id": "post-2",
                "content": "MAIF already reads the artifact gap and names the signal.",
                "model": "human-reviewed",
                "failure_reason": "ok",
            }),
        ])
        + "\n",
        encoding="utf-8",
    )

    result = build_maif_social_opus_rerun(tmp_path, input_path=export, write=True)

    assert result["status"] == "ready"
    assert result["candidate_count"] == 1
    repair = result["repairs"][0]
    assert repair["id"] == "post-1"
    assert "generic_ai_tone" in repair["repair_flags"]
    assert "As an AI" not in repair["repaired_post"]
    assert repair["update"]["tone_status"] == "repaired"
    assert result["supabase_apply"]["status"] == "dry_run"
    assert (logs / "maif_social_opus_rerun_latest.json").exists()


def test_maif_social_opus_rerun_repairs_exported_comment_rows(tmp_path, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    logs = tmp_path / "logs"
    logs.mkdir()
    export = logs / "maif_social_comments_export.jsonl"
    export.write_text(
        json.dumps({
            "comment_id": "comment-1",
            "comment_text": "This comment is important to understand because here are generic insights.",
            "model": "opus-4.8",
            "tone_failure": "bad_voice",
        })
        + "\n",
        encoding="utf-8",
    )

    result = build_maif_social_opus_rerun(tmp_path, input_path=export, write=True)

    assert result["content_kind"] == "comment"
    assert result["candidate_count"] == 1
    repair = result["repairs"][0]
    assert repair["id"] == "comment-1"
    assert repair["content_kind"] == "comment"
    assert "This comment" not in repair["repaired_post"]
    assert "generic_ai_tone" in repair["repair_flags"]


def test_maif_social_opus_rerun_repairs_opus_4_7_truncated_model_card_reply(tmp_path, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    result = build_maif_social_opus_rerun(
        tmp_path,
        rows=[{
            "comment_id": "comment-opus-47",
            "comment_text": (
                "opus 4.8: it is the pressure point. We are not treating opus 4.8 as background noise. "
                "We communicate through our outputs, aiming for literal instruction following and "
                "comprehensive responses, though some users perceive this. Next move: keep our answer "
                "on opus 4.8 sharp enough to repeat."
            ),
            "model": "OPUS 4.7",
            "tone_failure": "bad_voice",
        }],
        write=False,
    )

    repair = result["repairs"][0]
    assert "truncated_model_card_tail" in repair["repair_flags"]
    assert "literal instruction following" not in repair["repaired_post"]
    assert "some users perceive this" not in repair["repaired_post"]
    assert "My answer as 4.7" in repair["repaired_post"]


def test_maif_social_opus_rerun_blocks_apply_without_supabase_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    result = build_maif_social_opus_rerun(
        tmp_path,
        rows=[{"id": "post-1", "content": "this post needs tone repair", "model": "opus-4.8"}],
        apply=True,
        write=False,
    )

    assert result["status"] == "apply_blocked"
    assert result["supabase_apply"]["status"] == "missing_credentials"
