import importlib.util
import json
from pathlib import Path


def _repo_root() -> Path:
    root = Path(__file__).resolve().parent
    while root != root.parent and not (root / "client").exists():
        root = root.parent
    return root


ROOT = _repo_root()


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


def test_health_uses_central_exclusions_and_labels_old_capture_historical(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "healthy.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "client").mkdir()
    (tmp_path / "client" / "protected_runtime.py").write_text(
        "\n".join("VALUE = 1" for _ in range(300)),
        encoding="utf-8",
    )
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "prompt_journal.jsonl").write_text(
        json.dumps({
            "ts": "2020-01-01T00:00:00+00:00",
            "session_n": 1,
            "intent": "testing",
            "signals": {},
        }) + "\n",
        encoding="utf-8",
    )

    doc = health.build_health(tmp_path)

    assert "1/1 compliant" in doc
    assert "0 over cap" in doc
    assert "📚" in doc
    assert "🔴" not in doc


def test_health_collision_scan_requires_a_pigeon_manifest(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for stem in ("safe_split", "unsafe_split"):
        (src / f"{stem}.py").write_text("VALUE = 1\n", encoding="utf-8")
        package = src / stem
        package.mkdir()
        (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (src / "safe_split" / "MANIFEST.md").write_text(
        "# Pigeon extracted package\n",
        encoding="utf-8",
    )

    scan = health._collision_scan(tmp_path)

    assert scan["source_shadows"] == ["src/safe_split.py"]
    assert scan["unsafe"] == ["src/unsafe_split.py"]
