import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _load_module(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


analyzer = _load_module(
    "chat_composition_analyzer_seq001_v001",
    "client/chat_composition_analyzer_seq001_v001.py",
)
health = _load_module("organism_health", "_build_organism_health.py")


def test_read_messages_keeps_paste_only_prompt(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    paste_text = "def run():\n    return {'ok': True}\n"
    events = [
        {
            "ts": 1000,
            "type": "paste",
            "key": "Ctrl+V",
            "context": "chat",
            "surface": "codex",
            "source": "os_hook",
            "pasted_text": paste_text,
            "paste_category": "code_context",
            "paste_chars": len(paste_text),
            "paste_lines": len(paste_text.splitlines()),
        },
        {
            "ts": 1200,
            "type": "submit",
            "key": "Enter",
            "context": "chat",
            "surface": "codex",
            "source": "os_hook",
        },
    ]
    path = log_dir / "os_keystrokes.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")

    messages = analyzer._read_messages(path)
    assert len(messages) == 1

    comp = analyzer.reconstruct_composition(messages[0])
    state = analyzer.classify_chat_state(comp)

    assert comp["final_text"] == paste_text
    assert comp["paste_count"] == 1
    assert comp["paste_chars_total"] == len(paste_text)
    assert comp["paste_categories"] == ["code_context"]
    assert state["state"] == "context_loading"


def test_health_reports_paste_pipeline_and_surface(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    paste_event = {
        "schema": "paste_event/v1",
        "ts": 1000,
        "ts_iso": "2026-04-30T00:00:00+00:00",
        "surface": "codex",
        "context": "chat",
        "category": "large_context",
        "chars": 1300,
        "lines": 20,
        "preview": "long pasted context",
    }
    journal_entry = {
        "ts": "2026-04-30T00:00:01+00:00",
        "msg": "use this context",
        "intent": "building",
        "cognitive_state": "context_loading",
        "signals": {
            "paste_count": 1,
            "paste_chars_total": 1300,
            "paste_ratio": 1.0,
            "deletion_ratio": 0.0,
        },
    }
    (log_dir / "paste_events.jsonl").write_text(json.dumps(paste_event) + "\n", encoding="utf-8")
    (log_dir / "prompt_journal.jsonl").write_text(json.dumps(journal_entry) + "\n", encoding="utf-8")

    doc = health.build_health(tmp_path)

    assert "paste_events" in doc
    assert "Paste Surface" in doc
    assert "large_context" in doc
    assert "context_loading" in doc
