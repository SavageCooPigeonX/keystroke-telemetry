# Codex Compatibility

Codex uses explicit session events instead of ambient keyboard capture.
That keeps the loop browseable: every prompt, response, edit, training pair,
and entropy refresh lands in local files under `logs/`.

## Browse While Codex Works

- `logs/codex_state.md` - human-readable current loop state.
- `logs/codex_state.json` - same state for tools.
- `logs/codex_entropy_block.md` - latest entropy prompt block.
- `logs/prompt_journal.jsonl` - prompt history.
- `logs/ai_responses.jsonl` - response history.
- `logs/edit_pairs.jsonl` - prompt to file edit links.
- `logs/training_pairs.jsonl` - generated training pairs.
- `logs/dynamic_context_pack.json` - compact Codex/Copilot context bundle.
- `logs/dynamic_context_pack.md` - browseable version of the same bundle.
- `logs/prompt_telemetry_latest.json` - fresh replacement for the old stale
  `pigeon:prompt-telemetry` Copilot block.
- `logs/deepseek_prompt_jobs.jsonl` - prompt-triggered DeepSeek V4 coding jobs.
- `logs/deepseek_prompt_results.jsonl` - DeepSeek V4 prompt job outputs.

## Commands

```powershell
py codex_compat.py state
py codex_compat.py log-prompt --prompt "fix the parser"
py codex_compat.py log-prompt --prompt "fix the parser" --deleted-text "rewrite regex" --deleted-word regex
py codex_compat.py log-composition --final-text "fix the parser" --deleted-text "rewrite regex maybe"
py codex_compat.py pre-prompt --final-text "fix the parser" --deleted-text "rewrite regex maybe"
py codex_compat.py select-context --prompt "fix parser routing" --deleted-word regex
py codex_compat.py context-pack --prompt "fix parser routing" --deleted-word regex --surface codex
py codex_compat.py train-numeric --prompt "fix parser routing" --file src/parser.py
py codex_compat.py predict-numeric --prompt "fix parser routing"
py codex_compat.py log-response --prompt "fix the parser" --response "patched parser.py"
py codex_compat.py log-edit --file src/parser.py --why "fix parser edge case"
py codex_compat.py capture-pair
py codex_compat.py shed --module src/parser.py --confidence 0.78 --note "uncertain parsing edge"
py codex_compat.py import-jsonl path\to\codex-session.jsonl
py codex_compat.py push-intent-resolver
py codex_compat.py launch-observatory
py codex_compat.py launch-observatory --thought-completer
py codex_compat.py launch-deepseek
py src/thought_completer.py --compose
py src/deepseek_daemon_seq001_v001.py --once --dry-run
```

## What This Can And Cannot Do

Can:

- Preserve persistent local state for Codex coding loops.
- Generate the repo's existing training-pair format from explicit Codex events.
- Refresh entropy files after prompts, responses, edits, and shed records.
- Carry explicit deletion analytics through `chat_compositions`, `prompt_journal`,
  `unsaid_history`, and `unsaid_reconstructions`.
- Run a pre-submit pipeline that captures deletions, fires numeric context
  selection, optionally waits for the thought-completer sim, and injects a
  managed block into `.github/copilot-instructions.md`.
- Open `thought_completer` as a controlled prompt composer. Prompts written
  there have exact deletion/hesitation capture before the final text is copied
  for Copilot.
- Write `logs/dynamic_context_pack.json` and `.md`, then inject a managed
  `codex:dynamic-context-pack` block into `.github/copilot-instructions.md`.
  This pack combines prompt text, deleted words, hesitation, numeric file
  scores, dirty files, recent training pairs, unresolved intents, entropy, and
  surface activity.
- Replace the legacy `pigeon:prompt-telemetry` block from the same fresh context
  pack, so Copilot does not read a missing/stale `prompt_telemetry_latest.json`.
- Refresh `pigeon:current-query` and `pigeon:staleness-alert` from the same
  live pack, while still naming older legacy blocks that remain stale.
- Queue DeepSeek V4 jobs per prompt/context pack in
  `logs/deepseek_prompt_jobs.jsonl`. The daemon defaults to `deepseek-v4-pro`
  for coding and can use `deepseek-v4-flash` for fast lanes.
- Start the V4 daemon with `py codex_compat.py launch-deepseek`; it refuses to
  run real API calls until `DEEPSEEK_API_KEY` exists.
- In composer mode, pause fires are separate from submit. `Ctrl+Shift+R`
  rewards the last pause/sim result; `Ctrl+Shift+C` copies your exact words/code
  without treating that copy as a reward.
- Consume an already-captured OS/UIA composition via
  `run_pre_prompt_from_composition(...)`, so external watchers can feed the same
  context pack without duplicating a composition log.
- Expose `handoff_ready` in `logs/pre_prompt_state.json`; if the sim times out
  or errors, a controlled submitter can stop before the prompt reaches Copilot.
- Push deletion-heavy prompts into the intent resolver backlog.
- Fire numeric context selection per logged prompt/composition and append
  `logs/context_selection_history.jsonl`.
- Train `logs/intent_matrix.json` from every `log-edit`, then reuse it for
  later context selection.
- Launch the existing observatory/thought-completer entrypoints.
- Best-effort capture native Codex desktop typing when `client/os_hook.py` is
  running and the foreground window title contains `Codex`. That preserves
  composition logs and dynamic context for the next turn, but it does not
  guarantee the current Codex API request was blocked before send.
- Keep prompt-triggered DeepSeek writes gated by
  `DEEPSEEK_AUTONOMOUS_PROMPT_WRITES=1`; without that, prompt jobs produce
  coding context/results instead of arbitrary file patches.

Cannot:

- Reliably reconstruct deleted keystrokes unless the user explicitly logs them.
- Guarantee native Copilot chat reads the injected block unless the submit path
  is controlled by an extension/wrapper that runs `pre-prompt` and waits first.
- Capture edits made directly inside native Copilot chat before submit unless
  the prompt is written in the controlled composer or a VS Code keybinding
  wrapper owns the submit.
- Guarantee native Codex chat pre-send injection from inside this API session.
  For that guarantee, the prompt must be written in the composer or a separate
  prompt broker must own the Enter/submit action.
- Read Codex's private internal reasoning.
- Guarantee the old VS Code observatory tabs are meaningful without VS Code-specific logs.
- Make autonomous changes safe without a visible state file, tests, and git diffs.

## Current Integration State

| Surface | Composition fires? | Injection timing | Sharpest path |
| --- | --- | --- | --- |
| Thought-completer composer | Yes: text diffs, deletions, pauses, reward/copy | Before clipboard handoff | Best today |
| Copilot in VS Code | Yes when `os_hook`/UIA or extension wrapper runs | Guaranteed only if wrapper owns submit | Good with wrapper |
| Codex native chat | Best-effort with `os_hook` window match or explicit session logging | Not guaranteed before current request | Good for next turn/state |
| Screenshots | Not wired yet | N/A | Next layer: screenshot/OCR context shift events |

## DeepSeek V4 Coding Lane

Default model:

```powershell
DEEPSEEK_CODING_MODEL=deepseek-v4-pro
DEEPSEEK_FAST_MODEL=deepseek-v4-flash
```

Prompt flow:

1. `log-prompt`, composer submit/pause, or `context-pack` writes current state.
2. `codex_compat` appends a queued job to `logs/deepseek_prompt_jobs.jsonl`.
3. `deepseek_daemon` consumes prompt jobs first, then rejected patches,
   compliance work, and older simulated intents.
4. Results land in `logs/deepseek_prompt_results.jsonl` and the latest result
   in `logs/deepseek_prompt_latest_result.json`.

Autonomous prompt patching is intentionally gated. Existing daemon compliance
and intent jobs can still patch through the older controlled path; prompt jobs
only patch when `DEEPSEEK_AUTONOMOUS_PROMPT_WRITES=1`.

Long term, screenshot context should sit above UIA: UIA gives structured
`chat/editor/terminal/search` switches; screenshot/OCR can detect broader
semantic shifts such as "now looking at tests", "now reading docs", or "now in
Copilot result view".
