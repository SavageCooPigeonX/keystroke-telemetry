# Operator Data Storage Contract

Date: 2026-06-28
Scope: keystroke-telemetry local runtime, prompt journals, operator profile state, and pre-push safety.

## Rule

Operator-private runtime data must not be stored in git.

Git may store code, tests, schemas, synthetic fixtures, and documentation. Git must not store raw prompts, keystrokes, deleted words, operator profiles, query memory, rework memory, task queues, local coaching, or per-file operator heat maps.

## Storage Boundary

| Data class | Destination |
| --- | --- |
| raw operator prompts, query memory, rework log, task queue | MAIF storage or ignored local spool |
| keystroke/deletion/composition telemetry | MAIF storage or ignored local spool |
| operator profile/coaching/heat maps | MAIF storage or ignored local spool |
| code, tests, schema contracts, synthetic fixtures | git |
| generated docs/manifests without raw operator data | git only when intentionally reviewed |

Allowed local spools are `.maif/` and `maif_operator_data/`. They are ignored by git and are only staging areas before MAIF persistence.

## Mandatory Check

Before push, run:

```powershell
py scripts\operator_data_guard_seq001_v001__block_operator_data_git_storage_lc_data_storage_operator_happens.py --pre-push
```

Install the local hook:

```powershell
py scripts\install_operator_data_guard_hook_seq001_v001__install_pre_push_operator_data_guard_lc_data_storage_operator_happens.py
```

The hook blocks if operator-data-shaped files are staged, tracked, visibly untracked, or if `.gitignore` is missing the required MAIF/local-spool ignore patterns.
