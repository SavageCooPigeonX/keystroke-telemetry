import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import codex_compat
from src.engagement_hooks_seq001_v001 import generate_hook_records
from src.operator_response_policy_seq001_v001 import (
    POLICY_END,
    POLICY_SCHEMA,
    POLICY_START,
    build_operator_response_policy,
    load_operator_response_policy,
    load_response_style_model,
    record_response_reward,
    select_response_arm,
)


def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="operator_response_policy_"))
    (root / ".github").mkdir(parents=True)
    (root / "logs").mkdir()
    (root / "src").mkdir()
    (root / ".github" / "copilot-instructions.md").write_text("# Instructions\n", encoding="utf-8")
    (root / "MANIFEST.md").write_text(
        "# Operator Response Policy\n\n"
        "Owns reward loop, response style, intent graph, file mail memory, and self clearing context.",
        encoding="utf-8",
    )
    (root / "src" / "router.py").write_text("def route():\n    return True\n", encoding="utf-8")
    (root / "src" / "policy.py").write_text("def policy():\n    return 'ok'\n", encoding="utf-8")
    (root / "logs" / "context_selection.json").write_text(json.dumps({
        "files": [{"name": "src/policy.py", "path": "src/policy.py", "score": 0.9}],
        "confidence": 0.9,
        "status": "ok",
    }), encoding="utf-8")
    return root


def test_response_policy_renders_and_injects_managed_block():
    root = _root()

    policy = build_operator_response_policy(
        root,
        "make responses actionable with reward loop and intent graph",
        inject=True,
    )

    assert policy["schema"] == POLICY_SCHEMA
    assert policy["active_arm"] == "probe_council"
    assert (root / "logs" / "operator_response_policy.json").exists()
    assert (root / "logs" / "operator_response_policy.md").exists()
    text = (root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert POLICY_START in text
    assert POLICY_END in text
    assert "REQUIRED_RESPONSE_SHAPE" in text
    assert "Operator read" in text


def test_explicit_reward_commands_update_style_model():
    root = _root()

    event = record_response_reward(root, {
        "response_id": "resp-explicit",
        "style_arm": "probe_council",
        "prompt": "make the response layer more actionable",
        "response": "Operator read: action. Intent moves: root:route:policy:patch. Probe files: src/policy.py. Next mutation: run tests.",
        "feedback_text": "reward:+2\nstyle: old friend but actionable\navoid: generic status memo\nmore actionable",
    })
    model = load_response_style_model(root)

    assert event["score"] > 0.5
    assert model["arms"]["probe_council"]["count"] == 1
    assert any("old friend" in item for item in model["style_notes"])
    assert any("generic status memo" in item for item in model["avoid_rules"])


def test_passive_reward_scores_response_without_explicit_feedback():
    root = _root()

    event = record_response_reward(root, {
        "response_id": "resp-passive",
        "style_arm": "surgical_engineer",
        "prompt": "patch response policy and verify",
        "response": (
            "Operator read: patch the policy. Intent moves: root:patch:response_policy:patch. "
            "Probe files: src/policy.py. Next mutation: run pytest. File quote: policy.py brought receipts."
        ),
        "context_window_files": ["src/policy.py"],
        "intent_nodes": ["root:patch:response_policy:patch"],
    })

    assert event["passive_reward"]["weighted_score"] > 0.4
    assert event["score"] > 0.4
    assert (root / "logs" / "response_reward_events.jsonl").exists()


def test_engagement_hooks_get_stable_ids_for_later_reward():
    root = _root()
    (root / "logs" / "unsaid_latest.json").write_text(json.dumps({
        "completion": "wire hooks into the operator response policy",
    }), encoding="utf-8")

    first = generate_hook_records(root, history=[{"state": "focused", "del_ratio": 0.1}], max_hooks=1)
    second = generate_hook_records(root, history=[{"state": "focused", "del_ratio": 0.1}], max_hooks=1)

    assert first
    assert first[0]["hook_id"] == second[0]["hook_id"]
    assert first[0]["hook_type"] == "reveal"
    assert first[0]["expected_operator_action"]
    latest = json.loads((root / "logs" / "engagement_hooks_latest.json").read_text(encoding="utf-8"))
    assert latest["hooks"][0]["hook_id"] == first[0]["hook_id"]


def test_prompt_to_policy_to_logged_response_to_reward_update():
    root = _root()

    pack = codex_compat.build_dynamic_context_pack(
        root,
        "intent graph should wake policy file for reward loop",
        surface="test",
        inject=True,
    )
    entry = codex_compat.log_response(
        root,
        "intent graph should wake policy file for reward loop",
        (
            "Operator read: close the loop. Intent moves: root:route:reward_loop:patch. "
            "Probe files: src/policy.py. Next mutation: run pytest. File quote: policy.py is holding the receipt."
        ),
        style_arm=pack["operator_response_policy"]["active_arm"],
    )

    assert pack["operator_response_policy"]["active_arm"]
    assert entry["response_policy"]["style_arm"]
    assert entry["reward_event"]["score"] > 0
    model = load_response_style_model(root)
    assert model["arms"][entry["response_policy"]["style_arm"]]["count"] >= 1


def test_chaos_comedy_cannot_dominate_when_thinking_momentum_is_low():
    root = _root()
    model = load_response_style_model(root)
    model["arms"]["chaos_comedy"] = {
        "count": 4,
        "reward_total": 4.0,
        "score": 1.0,
        "dimension_scores": {
            "thinking_momentum": 0.2,
            "intent_extraction_accuracy": 0.8,
            "code_mutation_readiness": 0.8,
            "comedy_style_resonance": 1.0,
        },
        "last_reward_ts": datetime.now(timezone.utc).isoformat(),
    }
    (root / "logs" / "response_style_model.json").write_text(json.dumps(model, indent=2), encoding="utf-8")

    selected = select_response_arm(root, "crank entropy comedy but keep it useful")

    assert selected["selected_arm"] != "chaos_comedy"
    assert "guard" in selected["reason"]


def test_stale_policy_is_marked_instead_of_silently_reused():
    root = _root()
    old = {
        "schema": POLICY_SCHEMA,
        "ts": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
        "active_arm": "probe_council",
    }
    (root / "logs" / "operator_response_policy.json").write_text(json.dumps(old), encoding="utf-8")

    loaded = load_operator_response_policy(root, max_age_minutes=30)

    assert loaded["stale"] is True
    assert loaded["stale_reason"] == "missing_or_old_policy_ts"
