# Changelog — keystroke-telemetry

---

## [unreleased] 2026-03-22 — Self-Compiling Loop

### feat: auto-compile oversized files at every commit

`git_plugin` now triggers `auto_compile_oversized()` after every commit. Any file flagged `over_hard_cap` by `self_fix_seq013` is automatically decomposed by `run_clean_split` (DeepSeek cut plan → AST bin-packing → import rewriting) without human intervention. The `[pigeon-auto]` commit that follows stages all output.

**Compiled this session:**

| Source | Lines | Output | Cost |
|---|---|---|---|
| `compliance_seq008` | 216 | 12 files | $0.0010 |
| `heal_seq009` | 264 | 6 files | $0.0008 |
| `manifest_builder_seq007` | 1024 | **32 files** | $0.0028 |
| `nametag_seq011` | 245 | 9 files | $0.0009 |

### fix: Windows MAX_PATH exceeded in auto-compile target names (`556f5b2`)

`target_name` was the full 90-char pigeon stem → output paths reached 289 chars, crashing `mkdir`. Fixed: `re.match(r'([\w]+_seq\d+)', stem)` extracts `compliance_seq008` style short name → 141 chars.

### fix: multi-line `from X import (...)` capture in `file_writer_seq003` (`4e3a7c4`)

`_collect_imports()` used `lines[node.lineno - 1]` — only the first line of multi-line imports, producing truncated `from X import (` with no closing paren. Generated files had `SyntaxError` on line 5.

**Fix:** `"\n".join(lines[node.lineno-1 : node.end_lineno])` — full span via AST `end_lineno`.

### fix: `_HC_FROM_IMPORT` regex missed indented imports (`d447b19`)

Pattern was `^(from\s+...)` — anchored at column 0. Imports inside `try:` blocks (like `pulse_watcher.py`'s hardcoded import) were never matched by the self-fix scanner.

**Fix:** `^([ \t]*from\s+...)` + tightened symbol group to `[\w,][^\n]*` to stop at newline.

### fix: `_scan_over_hard_cap` reading wrong registry key

`pigeon_registry.json` structure is `{generated, total, files: [...]}`. The scanner was calling `list(registry.values())` and getting `[timestamp, 96, [files_list]]` — the files list itself isn't a dict, so every entry was skipped and the over_hard_cap list was always empty.

**Fix:** `registry['files']` with `isinstance` guard.

### fix: over_hard_cap scanner re-flagging already-compiled monolith originals

Monolith source files (`compliance_seq008_v004_...py`) remained in the registry even after their compiled subdir existed. They kept appearing in the auto-compile queue (wasting API calls).

**Fix:** Check for `(abs_p.parent / seq_base / '__init__.py').exists()` — skip if compiled output already exists.

### fix: `run_clean_split` hardcoded versioned import (`556f5b2`)

`from pigeon_compiler.weakness_planner.deepseek_plan_prompt_seq004_v003_...` — breaks on the next pigeon rename.

**Fix:** Dynamic loader `_load_request_cut_plan()` using glob, same pattern as other hot-module loaders.

### feat: exclusion logic for auto-compile (`aaeb075`)

`pigeon_limits.py` `EXCLUDE_STEM_PATTERNS` extended to 10 patterns:
- Compiler orchestrators: `run_clean_split`, `run_pigeon_loop`, `run_heal_seq`
- Test harnesses: `stress_test`, `test_all`, `deep_test`, `test_public`
- Prompt templates: `streaming_layer_seq007` (intentional monolith)
- `EXCLUDE_DIR_PATTERNS` now includes `vscode-extension` and `client`

`_scan_over_hard_cap` wired to call `is_excluded(abs_p)` before flagging. 9/9 smoke tests pass.

### feat: `mark_done()` wired into post-commit hook (`d447b19`)

Commit messages containing `tq-NNN` now auto-close corresponding task queue items via `mark_done(root, task_id)`. `inject_task_queue()` re-injects the updated queue on the same commit.

### fix: `fix_report` scope bug in `git_plugin.run()` (`7768b84`)

Auto-compile block was placed in `_run_post_commit_extras()` which has no access to `fix_report` (created in `run()`). Moved inside `run()` under `if fix_mod:`.

---

## [unreleased] 2026-03-17

### feat: dynamic CoT injection fully wired (`d460a7d`, `f989307`, `1f60b21`)

The system now injects **11 live telemetry sections** into Copilot's chain-of-thought on every commit.
`dynamic_prompt_seq017` reads from 10 data sources and writes a self-updating `<!-- pigeon:task-context -->` block directly into `.github/copilot-instructions.md`.

**New injection sections (this session):**

| Section | Data Source | What it surfaces |
|---|---|---|
| Coaching Directives | `operator_coaching.md` | DeepSeek-synthesized behavioral rules per operator state |
| Fragile Contracts | `docs/push_narratives/*.md` | Module assumptions + regression watchlists from last 3 commits |
| Known Issues | `docs/self_fix/*.md` | CRITICAL/HIGH problems with file names from latest self-fix scan |
| Persistent Gaps | `query_memory.json` | Recurring queries asked 2+ times (bg-noise filtered) |

**Previously injected (prior session):**
- Task focus inferred from commit messages
- Cognitive state + per-state CoT directive (frustrated/hesitant/flow/restructuring/abandoned)
- Unsaid threads (deleted prompt words)
- Module hot zones (file_heat_map hesitation scores)
- AI rework surface (miss rate + worst queries)
- Recent commits (non-pigeon-auto only)
- Prompt evolution trajectory (mutation count, line growth, features added)

**Pipeline:**
```
git commit
  → git_plugin._run_post_commit_extras()
      → push_narrative, self_fix, prompt_recon
      → DeepSeek → operator_coaching.md
      → _refresh_operator_state() → <!-- pigeon:operator-state -->
      → dynamic_prompt.inject_task_context() → <!-- pigeon:task-context -->
      → auto-commit [pigeon-auto]
```

---

### fix: operator_stats DATA block never accumulating (`1f60b21`)

`OperatorStats._load_existing()` searched for `"<!-- DATA"` on a single line, but
`_render()` outputs the markers on separate lines:
```
<!--
DATA
{json}
DATA
-->
```
**Fix:** changed to `re.search(r'<!--\s*\n?DATA\s*\n(.*?)\nDATA\s*\n-->', ..., re.DOTALL)`.
Every instantiation had been starting with empty history — the profile was never accumulating
beyond 1 message despite 110+ extension flushes. Now accumulates correctly (verified: 5 → 6 entries on re-load).

---

### feat: copilot prompt mutation tracker + auto-recon pipeline (`fa132f9`, `fec3fe0`)

- `prompt_recon_seq016` reconstructs Copilot prompts from commit diffs and tracks how
  `copilot-instructions.md` has evolved across all commits.
- Snapshots stored in `logs/copilot_prompt_mutations.json`. Current state: **24 mutations, 186→434 lines**.
- Features added tracked per-snapshot: `auto_index`, `operator_state`, `prompt_journal`, `pulse_blocks`, `prompt_recon`.
- Wired into post-commit hook: runs on every push.

---

### fix: EXCLUDE_STEM_PATTERNS was silently excluding all src/ files (`8199ccb`)

`is_excluded()` matched files whose intent slug contained `"prompt"` — every `src/` file
at the time had `_lc_pulse_telemetry_prompt` in the name. Push narratives were never
generating for any src/ module changes. Fixed the pattern to require a full stem match.

---

### feat: composition analyzer wired into cognitive pipeline (`7dd8e7b`)

Deleted words from prompt compositions now feed into:
1. `unsaid_seq002` — query memory unsaid thread detection
2. `operator_coaching.md` — DeepSeek sees what the operator wanted to say but deleted
3. `dynamic_prompt_seq017` — injected as "Unsaid Threads" into every Copilot session

---

## Manifest rebuild — 2026-03-17 05:46 UTC

All 17 MANIFEST.md files rebuilt across the project:
`src/`, `src/cognitive/`, `src/cognitive/drift/`, `src/cognitive/unsaid/`,
`src/operator_stats/`, `streaming_layer/`, `pigeon_compiler/`,
`pigeon_compiler/bones/`, `pigeon_compiler/cut_executor/`,
`pigeon_compiler/integrations/`, `pigeon_compiler/rename_engine/`,
`pigeon_compiler/runners/`, `pigeon_compiler/runners/compiler_output/press_release_gen/`,
`pigeon_compiler/state_extractor/`, `pigeon_compiler/weakness_planner/`,
`client/`, `vscode-extension/`

`MASTER_MANIFEST.md` rebuilt from scratch (was blank).

---

## Known outstanding issues (from self-fix scanner)

| Severity | Type | Files |
|---|---|---|
| CRITICAL | hardcoded_import | `stress_test.py`, `test_all.py`, `vscode-extension/pulse_watcher.py` |
| HIGH | query_noise | 76 `(background)` queries in `query_memory.json` — filter in extension flush |
| LOW | dead_export | ~11 functions defined but never called across `src/` |

---

## Module versions as of this session

| Module | Version |
|---|---|
| `dynamic_prompt_seq017` | v003 |
| `operator_stats_seq008` | v004 |
| `push_narrative_seq012` | v005 |
| `prompt_recon_seq016` | v001 |
| `logger_seq003` | v003 |
| `context_budget_seq004` | v007 |
| `drift_watcher_seq005` | v003 |
| `resistance_bridge_seq006` | v003 |
| `rework_detector_seq009` | v004 |
| `query_memory_seq010` | v003 |
| `file_heat_map_seq011` | v004 |
| `self_fix_seq013` | v003 |
| `cognitive_reactor_seq014` | v002 |
| `pulse_harvest_seq015` | v002 |
