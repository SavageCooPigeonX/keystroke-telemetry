# MANIFEST - tests/test_history

> Non-collected historical test evidence.

## Policy

- This folder is for root test history, not active pytest collection.
- Filenames intentionally avoid the `test_*.py` pytest collection pattern.
- Each file names its original path and the active lane that now owns coverage.

## Entries

| Historical file | Original path | Active/map coverage | Reason |
|---|---|---|---|
| `codex_compat_compiled_root_legacy_seq001_v001.py` | `test_codex_compat_compiled.py` | `tests/regression/test_codex_compat.py`; maintained `codex_compat/` package tests | Root hygiene and non-collected history mapping. |
| `file_interview_mode_root_legacy_seq001_v001.py` | `test_file_interview_mode.py` | `tests/test_prompt_manifest_compiler.py`; `tests/regression/test_operator_response_policy.py` | Root hygiene and non-collected history mapping. |
| `intent_outcome_binder_root_legacy_seq001_v001.py` | `test_intent_outcome_binder.py` | `tests/regression/test_codex_edit_outcome_binder.py`; outcome binder source tests | Root hygiene and non-collected history mapping. |