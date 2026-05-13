from src.tc_popup_seq001_v004_d0420__passive_always_on_top_tkinter_lc_chore_pigeon_rename_cascade import (
    _completion_candidate_buffer,
)


def test_completion_candidate_uses_live_buffer():
    assert _completion_candidate_buffer("new prompt", "old prompt", "insert") == "new prompt"


def test_completion_candidate_keeps_last_nonempty_for_active_empty_event():
    assert _completion_candidate_buffer("", "half typed prompt", "delete") == "half typed prompt"


def test_completion_candidate_does_not_resurrect_submitted_buffer():
    assert _completion_candidate_buffer("", "submitted prompt", "submit") == ""


def test_completion_candidate_does_not_resurrect_discarded_buffer():
    assert _completion_candidate_buffer("", "discarded prompt", "discard") == ""

