# AI Fingerprint Repo Plugin

External repos can now be plugged into keystroke telemetry as prompt/file
training surfaces.

## Command

```powershell
py src\thought_completer.py --fingerprint-repo "C:\Users\Nikita\OneDrive\Documents\GitHub\LinkRouter.ai\maif-auditor" --fingerprint-label maif_auditor --fingerprint-limit 80
```

Default privacy is `closed`. Use `--fingerprint-privacy open` only for repos
where readable repo terms in logs are acceptable.

For maximum privacy while probing a very sensitive repo, add
`--fingerprint-no-train`. That writes hashed repo fingerprints without adding
repo vocabulary to the shared numeric matrix.

## Outputs

- `logs/repo_fingerprint_maif_auditor.json` - MAIF file identities, hashed term summaries, numeric signatures.
- `logs/repo_fingerprint_history.jsonl` - repo import history.
- `logs/ai_fingerprint.json` - operator semantic profile plus prompt-term numeric signature.
- `logs/ai_fingerprint_history.jsonl` - fingerprint snapshots over time.
- `logs/intent_matrix.json` - existing numeric prompt-to-file matrix, trained with MAIF file identities.
- `logs/private_numeric_training.jsonl` - closed-mode training receipts with prompt hashes only.

## Behavior

Each indexed repo file becomes prompt-like training text in memory from its path,
headings, function/class names, and leading content. In `closed` mode, that text
is used to train the local numeric matrix but is not written to touch logs.
Stored repo summaries use hashes for terms and paths. Stable file identities such
as `maif_auditor_maif_auditor_engine` remain readable because they are the routing
addresses used by context selection.

Closed mode does not write raw repo file text or raw repo prompt previews.
The current shared numeric engine still stores readable token vocabulary in
`logs/intent_vocab.json` because its predictor matches future prompts by token ID.
That file is local and gitignored, but `--fingerprint-no-train` is the stricter
choice when even local readable vocabulary is too much.

Normal `codex_compat.log_prompt(...)` calls now refresh `logs/ai_fingerprint.json`.
Prompt Brain reads that fingerprint and includes its signature in the watcher
context block.

## Current Prompt-To-File Encoding

The active path is:

1. `codex_compat.select_context(...)` tries the context-select agent first.
2. If it has no files, `predict_numeric_files(...)` calls the numeric engine.
3. The numeric engine normalizes prompt text, assigns tokens stable word IDs,
   builds a sparse TF vector, and scores files from `logs/intent_matrix.json`.
4. Training uses `record_touch(prompt, files)` for open data, or the private
   training path for closed repos.
5. Prediction score is a dot product between prompt vector and file vector,
   dampened by file touch count, then boosted by explicit lexical overlap with
   file identity terms.

Intent keys are separate but connected. `tc_intent_keys_seq001_v001.py` generates:

```text
scope:verb:target:scale
```

`scope` comes from manifest matching, `verb` from intent categorization, `target`
from phrase/file extraction, and `scale` from risk words. Prompt Brain carries
both the intent key and numeric file shortlist.

## Long-Horizon Easy-Fix Loop

For MAID/MAIF-scale closed repos, the safe loop should be:

1. Index closed repo locally with `--fingerprint-privacy closed`.
2. Run a scanner that only emits low-risk tasks: syntax errors, missing imports,
   stale manifests, trivial test failures, format drift, file budget warnings.
3. Convert each task into an intent key with scope locked to one folder/file.
4. Put only easy, local, reversible work into Prompt Box.
5. Apply patches on a branch with a per-iteration cap.
6. Run the smallest relevant verification.
7. Retire the intent key only when verification passes.

No closed repo source should be sent into a model by default. Handoff context
should contain file identities, hashes, manifest labels, test names, and patch
summaries unless you explicitly open a file for model-visible editing.
