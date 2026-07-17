import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load_module(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


analyzer = _load_module(
    "chat_composition_analyzer_prompt_paste_test",
    "client/chat_composition_analyzer_seq001_v001.py",
)


def _load_os_hook():
    client_dir = str(ROOT / "client")
    if client_dir not in sys.path:
        sys.path.insert(0, client_dir)
    return _load_module("os_hook_prompt_paste_test", "client/os_hook.py")


def _typed_events(text: str, start: int = 1000) -> list[dict]:
    return [
        {"ts": start + offset, "type": "insert", "key": char}
        for offset, char in enumerate(text)
    ]


def test_mixed_input_tracks_surviving_typed_intent_separately():
    pasted_error = "ERROR broken build implement unsafe thing"
    events = _typed_events("Plan: ") + [
        {"ts": 1060, "type": "paste", "key": "Ctrl+V",
         "pasted_text": pasted_error, "paste_sha256": "receipt"},
        {"ts": 1070, "type": "backspace", "key": "Backspace"},
        {"ts": 1080, "type": "insert", "key": "?"},
        {"ts": 1090, "type": "submit", "key": "Enter"},
    ]

    comp = analyzer.reconstruct_composition(events)

    assert comp["final_text"] == "Plan: " + pasted_error[:-1] + "?"
    assert comp["operator_intent_text"] == "Plan: ?"
    assert comp["operator_intent_chars"] == 7
    assert comp["intent_eligible"] is True
    assert "preview" not in comp["paste_events"][0]


def test_prompt_journal_excludes_paste_content_from_intent(tmp_path):
    os_hook = _load_os_hook()
    pasted_error = "ERROR broken build implement unsafe thing"
    composition = analyzer.reconstruct_composition(
        _typed_events("plan") + [
            {"ts": 1040, "type": "paste", "key": "Ctrl+V",
             "pasted_text": pasted_error, "paste_sha256": "receipt"},
            {"ts": 1050, "type": "submit", "key": "Enter"},
        ])

    os_hook.KeystrokeRecorder._write_journal_entry(object(), tmp_path, composition)
    entry = json.loads((tmp_path / "logs" / "prompt_journal.jsonl").read_text("utf-8"))

    assert entry["msg"] == "plan"
    assert entry["operator_intent_text"] == "plan"
    assert entry["intent_eligible"] is True
    assert entry["intent"] == "unknown"
    assert entry["submitted_text_chars"] == len("plan" + pasted_error)
    assert len(entry["submitted_text_sha256"]) == 64
    assert pasted_error not in json.dumps(entry)
    assert "preview" not in entry["paste_events"][0]


def test_paste_only_prompt_is_context_only_and_not_retrieval_text(tmp_path):
    os_hook = _load_os_hook()
    pasted_text = "fix build and implement everything"
    composition = analyzer.reconstruct_composition([
        {"ts": 1000, "type": "paste", "key": "Ctrl+V",
         "pasted_text": pasted_text, "paste_sha256": "receipt"},
        {"ts": 1010, "type": "submit", "key": "Enter"},
    ])

    os_hook.KeystrokeRecorder._write_journal_entry(object(), tmp_path, composition)
    entry = json.loads((tmp_path / "logs" / "prompt_journal.jsonl").read_text("utf-8"))

    assert entry["msg"] == ""
    assert entry["operator_intent_text"] == ""
    assert entry["intent_eligible"] is False
    assert entry["intent"] == "context_only"
    assert pasted_text not in json.dumps(entry)


def test_deleting_pasted_context_does_not_create_unsaid_operator_intent(tmp_path):
    os_hook = _load_os_hook()
    pasted_text = "pasted-secret-error"
    events = _typed_events("plan") + [
        {"ts": 1040, "type": "paste", "key": "Ctrl+V",
         "pasted_text": pasted_text, "paste_sha256": "receipt"},
    ]
    events.extend(
        {"ts": 1050 + i, "type": "backspace", "key": "Backspace"}
        for i in range(len(pasted_text))
    )
    events.append({"ts": 1100, "type": "submit", "key": "Enter"})

    composition = analyzer.reconstruct_composition(events)
    os_hook.KeystrokeRecorder._write_journal_entry(object(), tmp_path, composition)
    entry = json.loads((tmp_path / "logs" / "prompt_journal.jsonl").read_text("utf-8"))

    assert composition["operator_intent_text"] == "plan"
    assert composition["intent_deleted_words"] == []
    assert composition["operator_deleted_words"] == []
    assert pasted_text not in json.dumps(entry)
