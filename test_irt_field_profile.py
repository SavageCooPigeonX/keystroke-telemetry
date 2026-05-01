import tempfile
from pathlib import Path

from src.irt_field_profile_seq001_v001 import (
    analyze_transcription_against_profile,
    apply_intent_resolutions,
    build_irt_profile,
    chunk_transcript,
    probe_artifact_for_intent_keys,
    process_speech_chunk,
    render_field_report,
    resolve_intent_keys_against_profile,
    select_entity_profiles,
    should_run_mfs,
)


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="irt_field_profile_"))
    (root / "logs").mkdir()
    (root / "logs" / "repo_fingerprint_maif_auditor.json").write_text(
        """
{
  "schema": "repo_fingerprint/v1",
  "label": "maif_auditor",
  "files": [
    {"identity": "maif_auditor_examples_compare_entities", "path_hash": "abc"},
    {"identity": "maif_auditor_templates_ai_model_audit", "path_hash": "def"}
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return root


def test_speech_chunking_is_deterministic():
    text = " ".join(f"word{i}" for i in range(1, 181))

    first = chunk_transcript(text, chunk_seconds=30, words_per_minute=120)
    second = chunk_transcript(text, chunk_seconds=30, words_per_minute=120)

    assert first == second
    assert len(first) == 3
    assert first[0]["chunk_id"] == "chunk-0001"
    assert first[0]["word_count"] == 60
    assert first[1]["start_seconds"] == 30


def test_repeated_entity_mentions_merge_into_one_entity_profile():
    root = _root()
    profile = build_irt_profile(root, "run-entity", {"label": "entity_test"})
    first = {"chunk_id": "chunk-0001", "index": 1, "text": "Elon Musk said Tesla is building AI systems."}
    second = {"chunk_id": "chunk-0002", "index": 2, "text": "Musk said Tesla must make the model reliable."}

    select_entity_profiles(profile, first)
    select_entity_profiles(profile, second)

    entity = profile["entities"]["elon_musk"]
    assert entity["canonical"] == "Elon Musk"
    assert "Musk" in entity["aliases"]
    assert entity["support_count"] == 2
    assert entity["confidence"] > 0.5


def test_topic_drift_triggers_hush_pulse():
    root = _root()
    profile = build_irt_profile(root, "run-drift", {"label": "drift_test"})

    process_speech_chunk(root, profile, {
        "chunk_id": "chunk-0001",
        "index": 1,
        "text": "Elon Musk explained Tesla AI models, compute, neural training, and vehicle autonomy.",
    })
    pulse = process_speech_chunk(root, profile, {
        "chunk_id": "chunk-0002",
        "index": 2,
        "text": "But instead the conversation switched to unrelated cooking recipes and kitchen flavor.",
    })

    assert pulse["listen_state"] == "hush"
    assert pulse["trigger"] in {"topic_shift", "low_confidence", "unknown_theme", "intent_key_probe"}
    assert pulse["withheld_context"] or pulse["reason"]


def test_missing_ambiguous_context_creates_void_probe():
    root = _root()
    profile = build_irt_profile(root, "run-probe", {"label": "probe_test"})

    pulse = process_speech_chunk(root, profile, {
        "chunk_id": "chunk-0001",
        "index": 1,
        "text": "He said it would change everything, but they never named the company.",
    })

    assert pulse["listen_state"] == "probe"
    assert profile["void_probes"]
    assert profile["void_probes"][0]["reason"] == "missing_entity_reference"


def test_stable_repeated_themes_accumulate_intent_nodes_and_metrics():
    root = _root()
    profile = build_irt_profile(root, "run-stable", {"label": "elon_musk_podcast"})
    chunks = [
        {
            "chunk_id": "chunk-0001",
            "index": 1,
            "text": "Elon Musk said Tesla uses AI models, compute, and vehicle autonomy.",
        },
        {
            "chunk_id": "chunk-0002",
            "index": 2,
            "text": "Musk returned to Tesla AI training, neural models, and autonomy safety.",
        },
        {
            "chunk_id": "chunk-0003",
            "index": 3,
            "text": "Tesla and Elon Musk kept discussing AI model reliability and vehicle autonomy.",
        },
    ]
    stability = []

    for chunk in chunks:
        process_speech_chunk(root, profile, chunk)
        stability.append(profile["metrics"]["graph_stability"])

    assert stability[-1] > stability[0]
    assert any(node["support_count"] >= 2 for node in profile["intent_nodes"].values())
    assert profile["metrics"]["unknown_rate"] == 0.0
    assert profile["metrics"]["context_churn"] < 0.75


def test_artifact_probe_emits_candidate_intent_keys_from_irt_evidence():
    root = _root()
    profile = build_irt_profile(root, "run-probe-keys", {"label": "probe_keys"})

    artifact = {
        "chunk_id": "chunk-0001",
        "index": 1,
        "text": "My husband set the standard and the movement should carry his legacy together.",
        "entities": [{"canonical": "Erika Kirk"}],
        "themes": [],
        "semantic": {},
    }
    probe = probe_artifact_for_intent_keys(root, profile, artifact)

    keys = {item["key"] for item in probe["candidate_intent_keys"]}
    assert "legacy_continuity" in keys
    assert "base_consolidation" in keys
    assert all(item["implied_trajectory"] for item in probe["candidate_intent_keys"])


def test_existing_profile_keys_are_reinforced_by_matching_artifact():
    root = _root()
    profile = build_irt_profile(root, "run-reinforce", {
        "label": "reinforce_test",
        "monthly_intent_prior": {"legacy_continuity": 0.72},
    })
    candidate = {
        "key": "legacy_continuity",
        "implied_trajectory": "legacy continuity",
        "evidence": ["legacy", "standard"],
        "confidence": 0.84,
        "entity": "Erika Kirk",
        "source_artifact_id": "artifact-a",
        "temporal_context": {},
    }

    resolved = resolve_intent_keys_against_profile(profile, [candidate])

    item = resolved["resolved_intent_keys"][0]
    assert item["resolution"] == "reinforce"
    applied = apply_intent_resolutions(profile, {
        "artifact": {"artifact_id": "artifact-a", "timestamp": "2026-05-01T00:00:00+00:00"},
        "candidate_intent_keys": [candidate],
        **resolved,
        "mfs": {"mfs_needed": False},
    })
    assert profile["artifact_probe_state"]["active_intent_keys"]["legacy_continuity"]["support_count"] == 1
    assert applied["artifact_bindings"][0]["resolution"] == "reinforce"


def test_compatible_new_keys_resolve_as_extend_not_drift():
    root = _root()
    profile = build_irt_profile(root, "run-extend", {"label": "extend_test"})
    profile["artifact_probe_state"]["active_intent_keys"]["ai_modeling"] = {
        "key": "ai_modeling",
        "confidence": 0.74,
        "support_count": 3,
    }
    candidate = {
        "key": "vehicle_autonomy",
        "implied_trajectory": "vehicle autonomy",
        "evidence": ["tesla", "autonomy"],
        "confidence": 0.74,
        "entity": "Tesla",
        "source_artifact_id": "artifact-b",
        "temporal_context": {},
    }

    resolved = resolve_intent_keys_against_profile(profile, [candidate])["resolved_intent_keys"][0]

    assert resolved["resolution"] == "extend"
    assert resolved["drift_score"] < 0.5


def test_contradictory_keys_resolve_as_contradict():
    root = _root()
    profile = build_irt_profile(root, "run-contradict", {"label": "contradict_test"})
    profile["artifact_probe_state"]["active_intent_keys"]["legacy_continuity"] = {
        "key": "legacy_continuity",
        "confidence": 0.82,
        "support_count": 4,
    }
    candidate = {
        "key": "operational_independence",
        "implied_trajectory": "operational independence",
        "evidence": ["independent", "operations"],
        "confidence": 0.84,
        "entity": "Erika Kirk",
        "source_artifact_id": "artifact-c",
        "temporal_context": {},
    }

    resolved = resolve_intent_keys_against_profile(profile, [candidate])["resolved_intent_keys"][0]

    assert resolved["resolution"] == "contradict"
    assert resolved["contradiction_delta"] >= 0.8


def test_high_confidence_high_drift_resolution_emits_mfs_score_trigger():
    root = _root()
    profile = build_irt_profile(root, "run-mfs", {"label": "mfs_test"})
    artifact = {"artifact_id": "artifact-d"}
    resolutions = [{
        "key": "risk_governance",
        "evidence_likelihood": 0.91,
        "drift_score": 0.82,
        "contradiction_delta": 0.1,
    }]

    mfs = should_run_mfs(profile, artifact, resolutions)

    assert mfs["mfs_needed"] is True
    assert mfs["model_favorability_score_delta"] > 0


def test_analyze_transcription_against_profile_runs_full_bayesian_replay():
    root = _root()
    profile = build_irt_profile(root, "run-analysis", {"label": "analysis_test"})
    transcript = (
        "Elon Musk discussed Tesla AI models and vehicle autonomy. "
        "Musk returned to Tesla compute and neural training. "
        "Tesla stayed on AI model reliability and autonomy safety."
    )

    result = analyze_transcription_against_profile(
        root,
        profile,
        transcript,
        chunk_seconds=15,
        words_per_minute=80,
    )

    assert result is profile
    assert profile["metrics"]["chunks_processed"] >= 2
    assert profile["artifact_probe_state"]["artifact_bindings"]
    assert profile["artifact_probe_state"]["latest_resolution"]["resolved_intent_keys"]


def test_synthetic_replay_acceptance_report_is_renderable():
    root = _root()
    text = (
        "Elon Musk discussed Tesla AI models and vehicle autonomy. "
        "Musk explained Tesla compute and neural training for autonomy. "
        "Tesla returned to AI model safety and vehicle reliability. "
        "SpaceX later discussed Starship and Mars, but the model kept entities separate. "
        "Elon Musk returned to Tesla AI and autonomy again."
    )
    profile = build_irt_profile(root, "run-acceptance", {"label": "synthetic_hour"})

    for chunk in chunk_transcript(text, chunk_seconds=15, words_per_minute=80):
        process_speech_chunk(root, profile, chunk)

    assert profile["metrics"]["graph_stability"] >= 0.25
    assert profile["metrics"]["unknown_rate"] < 0.5
    assert profile["entities"]["tesla"]["support_count"] >= 2
    report = render_field_report(profile)
    assert "IRT Field Profile Report" in report
    assert "Tesla" in report
