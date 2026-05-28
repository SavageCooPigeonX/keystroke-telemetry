from pigeon_compiler.git_plugin.w_gpmo_s019_v012_d0510_λTL_βoc import (
    _new_hook_dirty_paths,
)


def test_new_hook_dirty_paths_excludes_preexisting_dirty_files():
    before = {
        ".github/copilot-instructions.md",
        "data/query_monitoring/query_audit_results.json",
        "directory/unrelated_prior_work.py",
    }
    after = before | {
        "directory/new_pigeon_name.py",
        "directory/old_pigeon_name.py",
        "pigeon_registry.json",
    }

    assert _new_hook_dirty_paths(before, after) == [
        "directory/new_pigeon_name.py",
        "directory/old_pigeon_name.py",
        "pigeon_registry.json",
    ]


def test_new_hook_dirty_paths_returns_empty_when_only_prior_dirty_remains():
    before = {"frontend/src/app/wire/page.tsx"}
    after = {"frontend/src/app/wire/page.tsx"}

    assert _new_hook_dirty_paths(before, after) == []
