from pigeon_compiler.organization_pass_seq001_v001 import build_organization_plan


def test_organization_plan_ranks_folder_independence_and_moves_root_src(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "MANIFEST.md").write_text("# src\n", encoding="utf-8")
    (src / "file_alpha_seq001_v001.py").write_text(
        "from src.manifest_beta_seq001_v001 import beta\n\n"
        "def alpha():\n"
        "    return beta()\n",
        encoding="utf-8",
    )
    (src / "manifest_beta_seq001_v001.py").write_text(
        "def beta():\n"
        "    return True\n",
        encoding="utf-8",
    )
    pkg = src / "thought_completer"
    pkg.mkdir()
    (pkg / "MANIFEST.md").write_text("# thought completer\n", encoding="utf-8")
    (pkg / "tc_local_seq001_v001.py").write_text(
        "def local():\n"
        "    return True\n",
        encoding="utf-8",
    )

    plan = build_organization_plan(tmp_path, write=True)

    assert plan["schema"] == "pigeon_codebase_organization_plan/v1"
    assert plan["mode"] == "plan_only_no_moves"
    assert plan["summary"]["files_scanned"] == 3
    assert plan["folder_rankings"]
    moves = {row["file"]: row for row in plan["move_plan"]}
    assert moves["src/file_alpha_seq001_v001.py"]["target_folder"] == "src/file_sim"
    assert moves["src/manifest_beta_seq001_v001.py"]["target_folder"] == "src/manifest_orchestration"
    assert moves["src/file_alpha_seq001_v001.py"]["apply_now"] is False
    folders = {row["folder"]: row for row in plan["folder_rankings"]}
    assert folders["src/thought_completer"]["recommended_mode"] == "self_managed"
    assert (tmp_path / "logs" / "pigeon_codebase_organization_plan_latest.json").exists()
