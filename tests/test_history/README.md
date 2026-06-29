# Test History

Historical tests live here when they are useful as repo intent evidence but should not be collected by pytest.

Rules:

- Files in this folder should not start with `test_`.
- Keep the original root path in each file header.
- `test_all.py` is intentionally still at repo root as the public smoke runner.
- Active pytest coverage belongs in `tests/`, `tests/regression/`, `tests/interlink/`, or `tests/generated/`.

Current entries:

- `codex_compat_compiled_root_legacy_seq001_v001.py` moved from `test_codex_compat_compiled.py` on 2026-06-29. Active coverage maps to `tests/regression/test_codex_compat.py` plus the maintained `codex_compat` package tests.
- `file_interview_mode_root_legacy_seq001_v001.py` moved from `test_file_interview_mode.py` on 2026-06-29. Active coverage maps to the file interview and prompt-manifest lanes under `tests/` and `tests/regression/`.
- `intent_outcome_binder_root_legacy_seq001_v001.py` moved from `test_intent_outcome_binder.py` on 2026-06-29. Active coverage maps to `tests/regression/test_codex_edit_outcome_binder.py` and intent outcome binding coverage in `src/`.