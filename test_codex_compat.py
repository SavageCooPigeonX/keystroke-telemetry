import json
import importlib.util
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import codex_compat


def _load_prompt_composer():
    module_path = Path(__file__).resolve().parent / "src" / "tc_prompt_composer_seq001_v001.py"
    spec = importlib.util.spec_from_file_location("tc_prompt_composer_seq001_v001", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_chat_composition_analyzer():
    module_path = Path(__file__).resolve().parent / "client" / "chat_composition_analyzer_seq001_v001.py"
    spec = importlib.util.spec_from_file_location("chat_composition_analyzer_seq001_v001", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_codex_explicit_logs_can_capture_training_pair():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_"))
    codex_compat.log_prompt(root, "fix the parser edge case")
    codex_compat.log_response(root, "fix the parser edge case", "Patched parser.py and verified parsing.")
    codex_compat.log_edit(root, file="src/parser.py", why="fix parser edge case")

    pair = codex_compat.capture_pair(root)

    assert pair is not None
    assert pair["user_intent"]["raw_prompt"] == "fix the parser edge case"
    assert pair["completion"]["response_summary"]
    assert pair["copilot_intent"]["file"] == "src/parser.py"
    assert (root / "logs" / "training_pairs.jsonl").exists()


def test_import_jsonl_maps_common_codex_events():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_import_"))
    source = root / "session.jsonl"
    source.write_text(
        "\n".join(
            [
                json.dumps({"role": "user", "content": "add codex logger"}),
                json.dumps({"role": "assistant", "content": "Added the logger."}),
                json.dumps({"type": "file_edit", "file": "codex_compat.py", "summary": "add adapter"}),
            ]
        ),
        encoding="utf-8",
    )

    counts = codex_compat.import_jsonl(root, source)

    assert counts == {"prompts": 1, "responses": 1, "edits": 1, "pairs": 1}
    assert (root / "logs" / "prompt_journal.jsonl").exists()
    assert (root / "logs" / "ai_responses.jsonl").exists()
    assert (root / "logs" / "edit_pairs.jsonl").exists()


def test_orchestrator_prompt_compiles_and_fires_file_email():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_orchestrator_"))

    entry = codex_compat.log_prompt(
        root,
        "only code through orchestrator monitor email comedy alerts 10q sims",
        deleted_words=["direct", "bypass"],
        source="test",
    )

    assert entry["intent"] == "orchestration"
    assert entry["semantic_profile"]["semantic_intent"] == "code_orchestration"
    assert entry["file_sim"]["status"] == "fired"
    assert entry["file_sim"]["file_email"]["count"] >= 1


def test_codex_prompt_logging_fires_operator_email_receipt():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_prompt_email_"))

    entry = codex_compat.log_prompt(
        root,
        "email every codex prompt to the operator control plane",
        source="codex_explicit",
    )

    receipt = entry["codex_prompt_email"]
    assert receipt["trigger"] == "codex_prompt"
    assert receipt["event_type"] == "codex_prompt"
    assert receipt["resend"]["status"] == "dry_run"
    assert receipt["resend"]["would_send"] is True
    assert receipt["orchestrator_email_guard"]["policy"] == "codex_prompt_operator_receipt"
    rows = [
        json.loads(line)
        for line in (root / "logs" / "file_email_outbox.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rows[-1]["event_type"] == "codex_prompt"
    assert (root / "logs" / "file_email_config.json").exists()
    assert "codex_prompt" in json.loads((root / "logs" / "file_email_config.json").read_text(encoding="utf-8"))["triggers"]


def test_every_codex_prompt_forces_file_sim_and_slow_self_fix_email():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_every_prompt_"))
    (root / "src").mkdir()
    (root / "codex_compat.py").write_text("def adapter():\n    return True\n", encoding="utf-8")
    (root / "src" / "batch_rewrite_sim_seq001_v001.py").write_text("def sim():\n    return True\n", encoding="utf-8")
    (root / "src" / "file_self_sim_learning_seq001_v001.py").write_text("def learn():\n    return True\n", encoding="utf-8")
    (root / "src" / "file_email_plugin_seq001_v001.py").write_text("def mail():\n    return True\n", encoding="utf-8")

    entry = codex_compat.log_prompt(root, "yo", source="codex_explicit")

    assert entry["file_sim"]["status"] == "fired"
    assert entry["file_sim"]["file_email"]["count"] >= 1
    assert entry["file_sim"]["file_email"]["records"][0]["resend"]["would_send"] is True
    slow = entry["file_sim"]["file_self_learning"]
    assert slow["schema"] == "file_self_sim_learning/v1"
    assert slow["wake_order"]
    assert slow["learning_digest_email"]["record"]["event_type"] == "learning_digest"
    assert slow["learning_digest_email"]["record"]["resend"]["would_send"] is True
    rows = [
        json.loads(line)
        for line in (root / "logs" / "file_email_outbox.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert {"codex_prompt", "learning_digest"} <= {row["event_type"] for row in rows}


def test_codex_composition_logs_deletion_analytics():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_deletions_"))

    comp = codex_compat.log_composition(
        root,
        final_text="make deletion analytics work here",
        deleted_text="raw key hooks global capture",
        deleted_words=["keystroke", "telemetry"],
        hesitation_count=3,
        duration_ms=12000,
    )

    journal = (root / "logs" / "prompt_journal.jsonl").read_text(encoding="utf-8")
    latest_prompt = json.loads(journal.strip().splitlines()[-1])

    assert comp["deletion_ratio"] > 0
    assert "keystroke" in latest_prompt["deleted_words"]
    assert latest_prompt["signals"]["deletion_ratio"] == comp["deletion_ratio"]
    assert latest_prompt["cognitive_state"] in {"hesitant", "frustrated", "neutral"}
    assert (root / "logs" / "chat_compositions.jsonl").exists()
    assert (root / "logs" / "unsaid_reconstructions.jsonl").exists()


def test_push_intent_resolver_uses_deleted_words():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_intent_"))
    codex_compat.log_composition(
        root,
        final_text="make coding loops visible",
        deleted_text="intent resolver forgotten deletion analytics",
    )

    result = codex_compat.push_intent_resolver(root)

    assert result["status"] == "ok"
    assert result["unresolved_count"] >= 1
    assert (root / "logs" / "codex_intent_resolver.json").exists()


def test_prompt_logging_fires_context_selection_per_query():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_context_"))

    codex_compat.log_prompt(root, "route this to numeric context selection", deleted_words=["surface"])
    codex_compat.log_prompt(root, "route this to file intent graph context", deleted_words=["graph"])

    history_path = root / "logs" / "context_selection_history.jsonl"
    rows = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines()]

    assert len(rows) == 2
    assert rows[-1]["status"] in {"ok", "missing_context_select_agent", "error"}
    assert "graph" in rows[-1]["intent_keys"]
    assert (root / "logs" / "context_selection.json").exists()


def test_prompt_logging_queues_deepseek_v4_job():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_deepseek_"))

    codex_compat.log_prompt(root, "switch coding lane to deepseek v4", deleted_words=["coder"])

    jobs_path = root / "logs" / "deepseek_prompt_jobs.jsonl"
    rows = [json.loads(line) for line in jobs_path.read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["status"] == "queued"
    assert rows[-1]["model"] == "deepseek-v4-pro"
    assert rows[-1]["prompt"] == "switch coding lane to deepseek v4"
    assert rows[-1]["deleted_words"] == ["coder"]


def test_edit_logging_trains_numeric_surface_for_later_context_selection():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_numeric_"))

    prompt = "numeric prompt encoding should route to file intent graphs"
    codex_compat.log_prompt(root, prompt)
    codex_compat.log_edit(root, file="src/file_intent_graph.py", why="seed graph routing", prompt=prompt)
    selected = codex_compat.select_context(root, prompt)

    assert (root / "logs" / "intent_matrix.json").exists()
    assert (root / "logs" / "numeric_training_history.jsonl").exists()
    assert selected["files"]
    assert selected["files"][0]["name"] == "file_intent_graph"


def test_pre_prompt_pipeline_writes_state_and_injects_block():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_pre_prompt_"))
    (root / ".github").mkdir()
    copilot = root / ".github" / "copilot-instructions.md"
    copilot.write_text("# Instructions\n", encoding="utf-8")

    state = codex_compat.run_pre_prompt_pipeline(
        root,
        "fix parser before submit",
        deleted_text="regex rewrite",
        deleted_words=["regex"],
        hesitation_count=2,
        run_sim=False,
    )

    assert state["injected"] is True
    assert state["handoff_ready"] is True
    assert state["sim"]["status"] == "skipped"
    assert state["file_sim"]["status"] == "fired"
    assert state["file_sim"]["target_state"] == "interlinked_source_state"
    assert (root / "logs" / "file_sim_config.json").exists()
    assert (root / "logs" / "file_sim_fire_history.jsonl").exists()
    assert (root / "logs" / "pre_prompt_state.json").exists()
    assert (root / "logs" / "pre_prompt_state.md").exists()
    copilot_text = copilot.read_text(encoding="utf-8")
    assert "<!-- codex:pre-prompt-state -->" in copilot_text
    assert "FILE_SIM_STATUS" in copilot_text
    assert state["composition"]["deleted_words"]

    updated = codex_compat.run_pre_prompt_pipeline(
        root,
        r"open C:\Users\Nikita\repo before submit",
        deleted_text=r"C:\temp\wrong path",
        deleted_words=["path"],
        run_sim=False,
    )

    assert updated["injected"] is True
    assert updated["handoff_ready"] is True
    assert r"C:\Users\Nikita\repo" in copilot.read_text(encoding="utf-8")


def test_dynamic_context_pack_writes_browseable_bundle_and_injects():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_context_pack_"))
    (root / ".github").mkdir()
    copilot = root / ".github" / "copilot-instructions.md"
    copilot.write_text("# Instructions\n", encoding="utf-8")

    codex_compat.log_composition(
        root,
        final_text="route sharp context into copilot",
        deleted_text="wrong stale tab",
        hesitation_count=2,
    )
    pack = codex_compat.build_dynamic_context_pack(
        root,
        prompt="route sharp context into copilot",
        deleted_words=["stale", "tab"],
        surface="codex",
    )

    assert pack["injected"] is True
    assert pack["signals"]["deleted_words"]
    assert "capture_boundaries" in pack
    assert (root / "logs" / "dynamic_context_pack.json").exists()
    assert (root / "logs" / "dynamic_context_pack.md").exists()
    telemetry = json.loads((root / "logs" / "prompt_telemetry_latest.json").read_text(encoding="utf-8"))
    assert telemetry["schema"] == "prompt_telemetry/latest/v2"
    assert telemetry["deepseek"]["model"] == "deepseek-v4-pro"
    assert "stale" in telemetry["deleted_words"]
    copilot_text = copilot.read_text(encoding="utf-8")
    assert "<!-- codex:dynamic-context-pack -->" in copilot_text
    assert "prompt_telemetry/latest/v2" in copilot_text
    assert "Codex live context refreshed" in copilot_text
    assert "LIVE_REPLACEMENTS" in copilot_text


def test_dynamic_context_pack_trims_truncated_line_whitespace():
    pack = {
        "ts": "now",
        "surface": "codex",
        "prompt": "fix trailing whitespace",
        "signals": {},
        "file_self_knowledge": {
            "operator_read": ("context " * 80),
            "packets": [{"file": "src/thought_completer.py", "mutation_scope": {"readiness": "draft_ready"}}],
        },
    }

    rendered = codex_compat._render_dynamic_context_pack(pack, managed=True)

    assert all(line == line.rstrip() for line in rendered.splitlines())


def test_pre_prompt_from_existing_composition_preserves_deletion_signal():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_from_composition_"))
    (root / ".github").mkdir()
    copilot = root / ".github" / "copilot-instructions.md"
    copilot.write_text("# Instructions\n", encoding="utf-8")
    composition = {
        "final_text": "make codex compositions feed dynamic context",
        "deleted_words": [{"word": "native"}, {"word": "blocked"}],
        "intent_deleted_words": ["pre-submit"],
        "rewrites": [],
        "hesitation_windows": [{"duration_ms": 2400}],
        "deletion_ratio": 0.31,
        "intent_deletion_ratio": 0.2,
        "duration_ms": 6400,
    }

    state = codex_compat.run_pre_prompt_from_composition(root, composition, run_sim=False)

    assert state["handoff_ready"] is True
    assert state["injected"] is True
    assert state["composition"]["final_text"] == composition["final_text"]
    assert "native" in json.loads((root / "logs" / "dynamic_context_pack.json").read_text(encoding="utf-8"))["signals"]["deleted_words"]
    assert "<!-- codex:pre-prompt-state -->" in copilot.read_text(encoding="utf-8")


def test_prompt_composer_tracker_captures_deletion_and_hesitation():
    composer = _load_prompt_composer()
    tracker = composer.CompositionTracker()

    tracker.apply_text("write the awkward prompt", now_ms=1000)
    tracker.apply_text("write the prompt", now_ms=3600)
    state = tracker.state()

    assert state["deletion_ratio"] > 0
    assert state["hesitation_count"] == 1
    assert "awkward" in state["deleted_words"]
    assert state["source"] == "thought_completer_composer"


def test_chat_composition_reconstructs_slow_backspaced_deleted_word():
    analyzer = _load_chat_composition_analyzer()
    # User typed banana, then backspaced it right-to-left. The final b can be
    # deleted just over 500ms later, which used to split into "anana".
    chars = [
        {"char": "a", "ts": 1000, "pos": 5},
        {"char": "n", "ts": 1247, "pos": 4},
        {"char": "a", "ts": 1421, "pos": 3},
        {"char": "n", "ts": 1563, "pos": 2},
        {"char": "a", "ts": 1721, "pos": 1},
        {"char": "b", "ts": 2277, "pos": 0},
    ]

    words = analyzer._extract_deleted_words(chars)

    assert words[0]["word"] == "banana"


def test_prompt_composer_pause_gate_cooldown_and_duplicate_guard():
    composer = _load_prompt_composer()
    gate = composer.PauseGate(cooldown_s=2.0, min_chars=4)

    ready, reason, _wait = gate.check("route prompt", now_s=10.0)
    assert ready is True
    assert reason == "ready"

    gate.mark_fire("route prompt", now_s=10.0)
    gate.mark_done()
    ready, reason, _wait = gate.check("route prompt", now_s=13.0)
    assert ready is False
    assert reason == "duplicate"

    ready, reason, wait = gate.check("route prompt again", now_s=11.0)
    assert ready is False
    assert reason == "cooldown"
    assert wait > 0


def test_stale_date_audit_flags_old_file_sim_and_hidden_words():
    root = Path(tempfile.mkdtemp(prefix="codex_compat_stale_"))
    now = datetime.now(timezone.utc)
    (root / "logs").mkdir()
    (root / "logs" / "prompt_journal.jsonl").write_text(json.dumps({
        "ts": now.isoformat(),
        "msg": "audit stale date hidden word",
    }) + "\n", encoding="utf-8")
    (root / "logs" / "chat_compositions.jsonl").write_text(json.dumps({
        "ts": now.isoformat(),
        "final_text": "audit stale date",
        "deleted_words": [{"word": "juice"}],
    }) + "\n", encoding="utf-8")
    (root / "logs" / "batch_rewrite_sim_latest.json").write_text(json.dumps({
        "ts": (now - timedelta(hours=2)).isoformat(),
        "status": "fired",
    }), encoding="utf-8")
    (root / "logs" / "file_sim_config.json").write_text(json.dumps({
        "fire_on": ["pre_prompt", "os_hook_auto"],
    }), encoding="utf-8")
    (root / "logs" / "pre_prompt_state.json").write_text(json.dumps({
        "ts": now.isoformat(),
        "trigger": "os_hook_auto",
    }), encoding="utf-8")

    audit = codex_compat.audit_stale_dates(root, max_lag_minutes=30)

    assert "batch_rewrite_sim" in audit["stale"]
    assert "juice" in audit["hidden_words_latest"]
    assert audit["trigger_audit"]["trigger_allowed"] is True
    assert (root / "logs" / "stale_date_audit_latest.md").exists()
