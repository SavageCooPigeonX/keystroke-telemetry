import json
import importlib.util
import sys
import tempfile
from pathlib import Path

import codex_compat


def _load_prompt_composer():
    module_path = Path(__file__).resolve().parent / "src" / "tc_prompt_composer_seq001_v001.py"
    spec = importlib.util.spec_from_file_location("tc_prompt_composer_seq001_v001", module_path)
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
    assert (root / "logs" / "pre_prompt_state.json").exists()
    assert (root / "logs" / "pre_prompt_state.md").exists()
    assert "<!-- codex:pre-prompt-state -->" in copilot.read_text(encoding="utf-8")
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
