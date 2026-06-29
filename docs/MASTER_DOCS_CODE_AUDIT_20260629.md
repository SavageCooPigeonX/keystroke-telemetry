# Master Docs Code Audit - 2026-06-29

Branch: `codex/root-docs-manifest-hygiene-20260629`
Base: `origin/master`

## Scope

- Root README and generated root `MANIFEST.md` notes.
- Root pytest-style files that were living beside source and runtime entrypoints.
- `tests/MANIFEST.md` plus new `tests/test_history/` mapping.
- Root manifest references in README.

## Code-To-Docs Checks

| Surface | Code evidence | Doc or manifest state | Result |
|---|---|---|---|
| Root smoke runner | `test_all.py` is documented as the public smoke runner and hook/trace target. | README keeps `test_all.py` at root and marks it intentional. | aligned |
| Root pytest-style files | `test_codex_compat_compiled.py`, `test_file_interview_mode.py`, and `test_intent_outcome_binder.py` were root-level pytest files. | Moved to `tests/test_history/` with non-collecting filenames and original-path headers. | aligned |
| Active pytest lanes | Maintained tests already live under `tests/`, `tests/regression/`, `tests/interlink/`, and `tests/generated/`. | README and `tests/MANIFEST.md` now name `tests/test_history/` as non-collected evidence. | aligned |
| Master/root manifest path | No tracked root `MASTER_MANIFEST.md` exists on `origin/master`; tracked root files are `MANIFEST.md` and `ROOT_SIM_KEYS.md`. | README tree and task example now reference actual tracked files. | aligned |
| Generated manifest safety | Root `MANIFEST.md` is generated from local telemetry/diagnostic state. | Added a manual audit note instead of regenerating from local operator data. | aligned |

## Root Test Moves

- `tests/test_history/codex_compat_compiled_root_legacy_seq001_v001.py`
- `tests/test_history/file_interview_mode_root_legacy_seq001_v001.py`
- `tests/test_history/intent_outcome_binder_root_legacy_seq001_v001.py`

## Follow-Up Contract

- Regenerate root `MANIFEST.md` only through the guarded producer when local operator data is safe to summarize.
- Keep `test_all.py` at repo root unless the README contract and hooks are updated together.
- Keep future historical tests in `tests/test_history/` with filenames that do not match `test_*.py`.