import json
import time

from src.tc_buffer_watcher_seq001_v001 import BufferWatcher


def _write_event(path, event):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def test_buffer_watcher_hydrates_active_prompt_on_launch(tmp_path):
    log_path = tmp_path / "logs" / "os_keystrokes.jsonl"
    live_buffer = "yeah its still not firing on completions pause and it cuts off my prompt"
    _write_event(
        log_path,
        {
            "type": "key",
            "ts": int(time.time() * 1000),
            "context": "codex",
            "buffer": live_buffer,
        },
    )

    watcher = BufferWatcher(log_path)

    assert watcher.buffer == live_buffer
    assert watcher.context == "codex"
    assert watcher.last_event_type == "key"
    assert watcher.hydrated_from_tail is True


def test_buffer_watcher_does_not_hydrate_after_submit(tmp_path):
    log_path = tmp_path / "logs" / "os_keystrokes.jsonl"
    _write_event(
        log_path,
        {
            "type": "submit",
            "ts": int(time.time() * 1000),
            "context": "codex",
            "buffer": "already submitted prompt",
        },
    )

    watcher = BufferWatcher(log_path)

    assert watcher.buffer == ""
    assert watcher.last_event_type == "submit"
    assert watcher.hydrated_from_tail is False


def test_buffer_watcher_submit_poll_clears_live_buffer(tmp_path):
    log_path = tmp_path / "logs" / "os_keystrokes.jsonl"
    _write_event(
        log_path,
        {
            "type": "insert",
            "ts": int(time.time() * 1000),
            "context": "codex",
            "buffer": "prompt that will be submitted",
        },
    )
    watcher = BufferWatcher(log_path)
    assert watcher.buffer == "prompt that will be submitted"

    _write_event(
        log_path,
        {
            "type": "submit",
            "ts": int(time.time() * 1000),
            "context": "codex",
            "buffer": "prompt that will be submitted",
        },
    )

    assert watcher.poll() is True
    assert watcher.buffer == ""
    assert watcher.last_event_type == "submit"


def test_buffer_watcher_ignores_stale_tail_on_launch(tmp_path):
    log_path = tmp_path / "logs" / "os_keystrokes.jsonl"
    stale_ms = int((time.time() - 20 * 60) * 1000)
    _write_event(
        log_path,
        {
            "type": "key",
            "ts": stale_ms,
            "context": "codex",
            "buffer": "old prompt should not wake popup",
        },
    )

    watcher = BufferWatcher(log_path)

    assert watcher.buffer == ""
    assert watcher.hydrated_from_tail is False
