from src.file_interlinked_naming_sim_seq001_v001 import run_interlinked_naming_sim
from src.file_interlinked_naming_policy_seq001_v001 import proposed_name, semantic_name_identity


def test_interlinked_naming_sim_forces_file_queries_and_sends_grader_email(tmp_path):
    src = tmp_path / "src"
    logs = tmp_path / "logs"
    src.mkdir()
    logs.mkdir()
    (src / "router_seq999_v123_long_name.py").write_text("def route():\n    return True\n", encoding="utf-8")
    (src / "router.py").write_text("def facade():\n    return True\n", encoding="utf-8")
    symbolic = "对p_tp_s027_v003_d0402_缩分话_λVR_βoc.py"
    (src / symbolic).write_text("def glyph_state():\n    return True\n", encoding="utf-8")
    (logs / "file_blank_sheet_sim_latest.json").write_text(
        '{"file_pressure_jobs":[{"file":"src/' + symbolic + '"},{"file":"src/router_seq999_v123_long_name.py"}]}',
        encoding="utf-8",
    )

    result = run_interlinked_naming_sim(tmp_path, write=True, limit=2, email=True)

    assert result["schema"] == "file_interlinked_naming_sim/v1"
    assert result["grader_gate"]["rename_allowed_now"] is False
    assert result["interlinked_queries"] == [
        "what_do_i_own",
        "what_number_key_am_i",
        "what_name_is_misleading",
        "who_could_break_if_i_rename",
        "what_standard_do_i_vote_for",
        "what_last_change_should_i_show",
        "what_proof_do_i_need",
    ]
    assert result["correction"]["downgrade"] == "prior_flatten_symbolic_names"
    assert "Chinese/symbolic" in result["standard_vote"]["convention"]
    assert "F#####" in result["standard_vote"]["convention"]
    assert "last_change" in result["standard_vote"]["convention"]
    assert result["participants"]
    assert result["participants"][0]["approval"] == "approve_plan_not_rename"
    symbolic_row = result["participants"][0]
    assert symbolic_row["number_key"].startswith("F")
    assert symbolic_row["answers"]["what_number_key_am_i"] == symbolic_row["number_key"]
    assert symbolic_row["operator_display_name"].startswith("The-Glyph-Preserving")
    assert symbolic_row["operator_display_name"].endswith("-Inator")
    assert "last-change" in symbolic_row["mutation_name"]
    assert symbolic_row["identity"]["symbolic_identity"] == symbolic
    assert symbolic_row["declared_kind"] == "symbolic_pigeon_name"
    assert symbolic_row["proposed_name"] == symbolic
    assert "intentional identity" in symbolic_row["discrepancy"]
    assert symbolic_row["downgrade"] == "prior_flatten_symbolic_names"
    assert "glyph identity" in symbolic_row["last_change_state"]
    assert result["email"]["event_type"] == "compile"
    latest = (logs / "file_email_latest.md").read_text(encoding="utf-8")
    assert "File room:" in latest
    assert "interlinked naming queries" in latest
    assert "F keys" in latest

    versioned = next(row for row in result["participants"] if row["file"].endswith("router_seq999_v123_long_name.py"))
    assert versioned["proposed_name"].startswith("router_seq999_v124__lc_")
    assert versioned["last_change_state"]


def test_semantic_name_policy_preserves_existing_sequence_and_versions_last_change():
    proposed = proposed_name(
        "src/router_seq020_v003_old_name.py",
        "versioned_module",
        sibling_files=["router_seq020_v003_old_name.py", "other_seq021_v001.py"],
        last_change="route prompt telemetry into manifest receipts",
    )

    assert proposed == "router_seq020_v004__lc_route_prompt_telemetry_manifest_receipts.py"


def test_semantic_name_policy_allocates_sequence_from_siblings_for_new_family():
    identity = semantic_name_identity(
        "new_router",
        sibling_files=["old_seq001_v001.py", "other_seq014_v002.py"],
    )

    assert identity["seq"] == 15
    assert identity["next_version"] == 1
    assert identity["source"] == "allocated_from_siblings"
