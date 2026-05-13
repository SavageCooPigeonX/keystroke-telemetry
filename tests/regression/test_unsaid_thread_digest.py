import json
import tempfile
from pathlib import Path

from src.unsaid_thread_digest_seq001_v001 import build_unsaid_thread_digest, render_unsaid_thread_digest


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def test_unsaid_thread_digest_writes_pasteable_copilot_context():
    root = Path(tempfile.mkdtemp(prefix="unsaid_digest_"))
    logs = root / "logs"
    logs.mkdir()

    _append_jsonl(logs / "unsaid_history.jsonl", {
        "ts": "2026-04-29T01:00:00Z",
        "completed_intent": "thought completer should stop being popup-first and close unsaid hooks into Copilot",
        "deleted_words": ["popup", "interferes"],
    })
    _append_jsonl(logs / "thought_composer_pauses.jsonl", {
        "ts": "2026-04-29T01:01:00Z",
        "pre_prompt": {
            "composition": {
                "final_text": "file sim should micro-sim ten file compositions before rewrite",
                "deleted_words": ["ten", "file", "compos"],
                "hesitation_count": 3,
            },
            "prompt_brain": {
                "intent_key": {"intent_key": "src/thought:simulate:file_context_pack:patch"},
                "context_selection": {
                    "files": [{"path": "src/tc_sim_engine_seq001_v004.py"}],
                },
            },
            "sim_latest": {
                "files": ["src/tc_context_agent_seq001_v004.py"],
                "completion": "wake file sim, load numeric context, produce a bounded validation plan",
            },
        },
    })
    _append_jsonl(logs / "tc_sim_results.jsonl", {
        "ts": "2026-04-29T01:02:00Z",
        "intent": "hook architecture should reconstruct deleted intent and inject future prompt history",
        "files": ["src/engagement_hooks_seq001_v001.py"],
        "completion": "write an unsaid digest file for Copilot to close",
        "score": 0.88,
    })
    _append_jsonl(logs / "prompt_brain_history.jsonl", {
        "ts": "2026-04-29T01:03:00Z",
        "prompt": "numeric encoding should select context for thought completer",
        "intent_key": "src/thought:route:numeric_context:patch",
        "context_selection": {"files": [{"path": "src/intent_numeric_seq001.py"}]},
    })

    result = build_unsaid_thread_digest(
        root,
        "hook architecture thought completer file sim copilot context injection",
        limit=5,
        write=True,
    )

    assert result["schema"] == "unsaid_thread_digest/v1"
    assert result["mode"] == "file_first_low_friction"
    assert result["threads"]
    assert result["threads"][0]["source"] in {"composer_pause", "tc_sim", "unsaid_history", "prompt_brain"}
    assert "Unsaid Threads To Close" in result["paste_block"]
    assert "close with Copilot/Codex" in result["paste_block"]
    assert "src/" in result["paste_block"]
    assert "Thought Completer owns pause/deletion reconstruction" in result["architecture_read"]

    assert (logs / "unsaid_thread_digest_latest.json").exists()
    assert (logs / "unsaid_thread_digest.jsonl").exists()
    assert (logs / "unsaid_thread_digest.md").exists()
    assert (logs / "copilot_unsaid_context.md").exists()
    assert "file sim should micro-sim" in (logs / "copilot_unsaid_context.md").read_text(encoding="utf-8")

    rendered = render_unsaid_thread_digest(result)
    assert "Architecture Read" in rendered
    assert "Paste Block" in rendered
