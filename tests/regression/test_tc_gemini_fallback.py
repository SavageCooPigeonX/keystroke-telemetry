from src.tc_gemini_seq001_v004_d0421__gemini_api_call_system_prompt_lc_live_copilot_layer import (
    _fallback_context_files,
    _load_api_key_details,
    _local_no_key_completion,
)


def test_completion_fallback_wakes_pause_popup_gemini_and_buffer_files():
    files = _fallback_context_files(
        "thought completer popup pause is not getting data from gemining and cuts off my prompt"
    )
    names = [f["name"] for f in files]

    assert "thought_completer" in names
    assert "tc_popup" in names
    assert "tc_gemini" in names
    assert "tc_buffer_watcher" in names


def test_local_no_key_completion_reports_selected_files_not_blank():
    completion = _local_no_key_completion(
        "pause completion should fire",
        [{"name": "tc_popup"}, {"name": "tc_gemini"}],
    )

    assert "missing GEMINI_API_KEY" in completion
    assert "tc_popup" in completion
    assert "tc_gemini" in completion


def test_explicit_gemini_env_path_is_supported(tmp_path, monkeypatch):
    env_path = tmp_path / "shared_gemini.env"
    env_path.write_text("GOOGLE_API_KEY=test-gemini-key\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_ENV_PATH", str(env_path))

    key, source = _load_api_key_details()

    assert key == "test-gemini-key"
    assert source == str(env_path)
