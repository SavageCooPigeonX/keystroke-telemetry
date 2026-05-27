import json
import subprocess
import tempfile
from pathlib import Path

from src.autonomous_mutation_audit_seq001_v001 import audit_autonomous_mutations


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="mutation_audit_"))
    _git(root, "init")
    _git(root, "config", "user.email", "audit@example.test")
    _git(root, "config", "user.name", "Mutation Audit")
    (root / "logs").mkdir()
    (root / "docs" / "self_fix").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "src" / "router.py").write_text("def route():\n    return True\n", encoding="utf-8")
    (root / "test_router.py").write_text("def test_router():\n    assert True\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "feat: deepseek self-heal improved router validation")

    prompt = "audit deepseek self fixes and file mutation memory"
    (root / "logs" / "prompt_journal.jsonl").write_text(json.dumps({
        "ts": "2026-04-30T00:00:00+00:00",
        "session_n": 9,
        "msg": prompt,
        "source": "os_hook_auto",
    }) + "\n", encoding="utf-8")
    (root / "logs" / "intent_key_latest.json").write_text(json.dumps({
        "prompt": prompt,
        "intent_key": "src:patch:deepseek_self_fix:read",
    }), encoding="utf-8")
    (root / "logs" / "intent_keys.jsonl").write_text(json.dumps({
        "prompt": prompt,
        "intent_key": "src:patch:deepseek_self_fix:read",
    }) + "\n", encoding="utf-8")
    (root / "logs" / "intent_loop_latest.json").write_text(json.dumps({
        "prompt": prompt,
        "intent_key": "src:patch:deepseek_self_fix:major",
        "focus_files": ["src/router.py"],
        "proposals": [{"file": "src/router.py"}],
    }), encoding="utf-8")
    (root / "logs" / "context_selection.json").write_text(json.dumps({
        "intent_keys": prompt,
        "files": [{"name": "src/router.py", "score": 0.8}],
        "confidence": 0.8,
    }), encoding="utf-8")
    (root / "logs" / "batch_rewrite_sim_latest.json").write_text(json.dumps({
        "intent": {"raw": prompt, "intent_key": "src:patch:deepseek_self_fix:major"},
        "proposals": [{"path": "src/router.py"}],
    }), encoding="utf-8")
    (root / "logs" / "dynamic_context_pack.json").write_text(json.dumps({
        "prompt": prompt,
        "focus_files": [{"name": "src/router.py", "reason": "numeric_context"}],
    }), encoding="utf-8")
    (root / "logs" / "file_self_knowledge_latest.json").write_text(json.dumps({
        "packets": [
            {
                "file": "src/router.py",
                "packet_id": "fsk-router",
                "validates_with": ["py -m py_compile src/router.py", "py -m pytest test_router.py -q"],
            }
        ]
    }), encoding="utf-8")
    (root / "logs" / "file_email_delivery_status.json").write_text(json.dumps({
        "mode": "resend",
        "can_send": True,
        "api_key_present": True,
        "blockers": [],
    }), encoding="utf-8")
    (root / "logs" / "file_email_outbox.jsonl").write_text(json.dumps({
        "reason": f"Codex prompt receipt: {prompt}",
        "intent_key": "src:patch:deepseek_self_fix:major",
        "file": "orchestrator/codex_prompt",
        "context_injection": ["src/router.py"],
        "resend": {"status": "sent", "response": {"id": "email-1"}},
    }) + "\n", encoding="utf-8")
    (root / "logs" / "deepseek_code_completion_jobs.jsonl").write_text(json.dumps({
        "status": "queued_for_orchestrator_approval",
        "file": "src/router.py",
    }) + "\n", encoding="utf-8")
    (root / "logs" / "deepseek_prompt_jobs.jsonl").write_text(json.dumps({
        "status": "queued",
        "prompt": prompt,
    }) + "\n", encoding="utf-8")
    (root / "logs" / "deepseek_prompt_results.jsonl").write_text(json.dumps({
        "success": True,
        "dry_run": True,
    }) + "\n", encoding="utf-8")
    (root / "logs" / "dead_token_collective_pairs.jsonl").write_text(json.dumps({
        "event_type": "rename",
        "old_path": "src/router_v001_chore.py",
        "new_path": "src/router.py",
        "dead_tokens": ["v001", "chore"],
    }) + "\n", encoding="utf-8")
    (root / "logs" / "file_identity_growth.jsonl").write_text(json.dumps({
        "file": "src/router.py",
        "growth_tags": ["deepseek", "self", "fix"],
    }) + "\n", encoding="utf-8")
    (root / "docs" / "self_fix" / "one_self_fix.md").write_text("self fix report", encoding="utf-8")
    return root


def test_audit_counts_intent_keys_and_mutation_signals():
    root = _repo()

    result = audit_autonomous_mutations(root, write=True)

    last = result["last_prompt_forensics"]
    assert last["distinct_intent_key_count"] == 2
    assert "src/router.py" in last["files_logged_by_source"]["file_email_receipt"]
    assert result["email_delivery"]["can_send"] is True
    assert result["email_delivery"]["latest_sent_id"] == "email-1"
    assert result["deepseek_actuals"]["code_completion_jobs"] == 1
    assert result["deepseek_actuals"]["dry_run_results"] == 1
    assert result["self_fix_history"]["self_fix_docs"] == 1
    assert result["file_reactions"]["files"][0]["file"] == "src/router.py"
    assert result["file_reactions"]["files"][0]["context_action"] in {
        "derank_dead_tokens_before_context",
        "clear_context_unless_intent_matches_then_allow_bounded_draft",
    }
    assert (root / "logs" / "autonomous_mutation_audit_latest.json").exists()
    assert (root / "logs" / "file_context_clearing_rules.json").exists()
