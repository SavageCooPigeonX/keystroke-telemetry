# Intent Map Context Routing Systems Doc

Generated: 2026-05-28

This document captures the sanitized architecture pivot for keystroke
telemetry. It intentionally contains no raw prompts, operator facts, live MAIF
records, private shard contents, API keys, or session logs.

The project should stop treating typing telemetry as only behavior capture and
start treating it as local intent evidence for code generation, context
selection, and Pigeon file identity.

The target system is:

1. A prompt is compiled into structured intent key profiles.
2. A domain router selects the correct project or private domain.
3. Intent keys expand, match, split, and route to files.
4. Files testify back through file comments and mutation history.
5. The intent profile remembers why code exists.
6. Generated code carries identity: why it was created, which domain owns it,
   which file owns it, and which tests prove it.

In short: keystroke telemetry becomes the private local substrate that lets
agent intent survive code generation without leaking the underlying MAIF data.

## MAIF Maintenance Role

Keystroke telemetry has crossed from a standalone thought-completer experiment
into a maintenance layer for MAIF-adjacent workflows. Its job is to convert
local operator signals into durable routing state for projects that share
maintenance pressure:

- Hush-style memory contributes shard/writeback and prompt-withholding
  patterns.
- IRT-style runtime contributes artifact probes, entity drift, and high-drift
  escalation.
- Pigeon contributes generated-code identity, rename/import safety, and
  auto-commit pairing.
- Keystroke telemetry contributes typing/deletion context, intent keys, domain
  manifests, learned file wakeups, and local privacy boundaries.

The maintenance rule is: typing speed, hesitation, deletions, prompt fragments,
and profile facts are private evidence for routing. They may select domains,
wake files, and update intent profiles; they must not be narrated or committed
as raw telemetry output.

## File Comments As Opinion Layer

File comments are testimony, not the intent itself. They should be paired to a
specific intent run so a later prompt cannot overwrite the current opinion
layer.

| Component | What it contributes | What it must not do |
| --- | --- | --- |
| File interview bridge | Collects bounded file testimony for a prompt run. | Store raw prompt history in committed docs. |
| Intent manifest builder | Builds durable intent-key profiles from file and session metadata. | Treat private shard names or raw operator text as public identifiers. |
| Domain manifest | Names project and private routing domains. | Wake personal/private domains without a privacy gate. |
| Prompt box policy | Turns intent profiles into compact action surfaces. | Duplicate memory instead of referencing the intent profile. |
| Intent lock | Binds the active run id and selected intent keys. | Drift from the prompt run that created it. |
| Outcome binder | Closes accepted file changes back to intent memory. | Write sensitive session data into source files. |

## Domain Model

The equivalent of memory shards for codebase work is a domain router. Projects
and knowledge surfaces are named, bounded, and scored.

| Domain id | Domain role | Default privacy |
| --- | --- | --- |
| `project.keystroke_telemetry` | intent-map telemetry substrate | local-first |
| `project.hush` | shard memory and writeback pattern | mixed personal/project |
| `project.irt` | artifact and field profile routing | project with private signals |
| `project.pigeon_code_compiler` | generated code identity and file lineage | project |
| `personal.operator_profile` | personal facts, style, routines, cognitive state | private |
| `cross_domain.audit` | audits, security, release, push state | project with sensitive logs |

The master manifest should own this domain table. It should decide which domain
wakes when prompt language, active files, typing speed, deletion ratio, recent
touches, or file comments point there.

## System Goal

The goal is an intent-addressable codebase:

- every generated or mutated file is paired with at least one intent key;
- every intent key belongs to one selected domain first;
- every domain has an intent key map;
- every intent key profile has file comments as testimony;
- every file can explain which intent it serves, what tests prove it, and what
  context would make it split;
- every context selection event leaves a receipt for why files were included or
  excluded.

The endpoint is not the file. The endpoint is the intent key profile. Files
comment into the profile after domain and intent matching.

## Core Objects

### Domain Manifest

The master domain manifest is the top-level router. It says what worlds exist
before a prompt is allowed to pick files.

```json
{
  "schema": "domain_manifest/v1",
  "domain_id": "project.keystroke_telemetry",
  "display_name": "Keystroke Telemetry",
  "root": "<repo-root>",
  "lexical_triggers": ["keystroke", "typing", "deleted words", "context select", "intent key"],
  "intent_profile_dir": "documentation/manifests/intent_profiles",
  "file_comment_sources": [
    "pigeon_registry.json",
    "logs/edit_pairs.jsonl",
    "logs/context_selection.json"
  ],
  "privacy_scope": "local-first",
  "default_writeback": "intent_profile"
}
```

### Intent Key Profile

An intent key profile is the durable endpoint. It is where file comments,
matched files, tests, learned triggers, and outcomes gather.

```json
{
  "schema": "intent_key_profile/v1",
  "intent_key": "project.keystroke_telemetry:route:context_select:major",
  "domain_id": "project.keystroke_telemetry",
  "status": "active",
  "definition": "route prompt and typing signals into selected codebase context",
  "lexical_triggers": ["context select", "intent key", "route files", "typing speed"],
  "files": [
    {
      "path": "src/example_selector.py",
      "role": "selector",
      "contribution": "scores source files from buffer, history, numeric surface, and local state",
      "confidence": 0.82,
      "missing": "must read domain manifest before file ranking"
    }
  ],
  "tests": [
    "tests/regression/test_tc_intent_keys.py"
  ],
  "file_comments": [],
  "signal_strength": {
    "lexical": 0.74,
    "typing": 0.48,
    "file_coupling": 0.66,
    "history": 0.71
  }
}
```

### File Intent Comment

A file intent comment is a vote. It is not the authority.

```json
{
  "schema": "file_intent_comment/v1",
  "run_id": "intent-run-example",
  "file": "src/tc_intent_keys_seq001_v001.py",
  "domain_id": "project.keystroke_telemetry",
  "candidate_intent_keys": [
    "project.keystroke_telemetry:route:intent_graph:major"
  ],
  "file_says": "Deterministically turns prompt fragments into scope:verb:target:scale intent keys.",
  "opinion": "This file should own graph generation, but not domain manifest authority.",
  "missing": [
    "generate_intent_graph",
    "profile writeback",
    "learned file wakeups"
  ],
  "confidence": 0.76
}
```

## Routing Pipeline

The routing path should be:

1. Capture prompt and composition telemetry locally.
2. Select a domain with privacy gates.
3. Compile structured intent.
4. Match intent nodes to files.
5. Run context clearing.
6. Ask files for bounded comments.
7. Write the intent profile endpoint.
8. Mutate code only after the profile gate.
9. Verify and bind the outcome.

## Signal Strength Model

Typing telemetry should change routing strength without exposing private text.

```text
intent_file_score =
  lexical_domain_score * 0.24
+ intent_key_text_score * 0.18
+ typing_signal_score * 0.12
+ active_file_score * 0.10
+ learned_file_memory_score * 0.14
+ manifest_syntax_score * 0.12
+ file_comment_support * 0.07
+ outcome_history_score * 0.06
- stale_context_penalty * 0.07
- privacy_or_domain_mismatch_penalty * 0.10
```

| Signal | Meaning for routing |
| --- | --- |
| Fast WPM with low deletion | known route; boost learned priors. |
| Fast WPM with high deletion | strong pressure with unstable wording; keep secondary keys. |
| Slow WPM with high hesitation | careful framing; boost manifests and file comments. |
| Repeated deleted terms | unsaid intent; include as weak context or probe. |
| Rewrite chain old to new | old term is rejected branch; new term is current route. |
| Post-response rework | previous context was weak; penalize repeated bad packets. |
| Active file edits | boost file domain but require profile match before mutation. |

## Intent Splitting Rule

If context exceeds intent key, split the key.

Split when any of these are true:

- selected files span more than one domain with no explicit coupling edge;
- a prompt contains multiple verbs, such as audit plus implement plus push;
- selected files exceed the token budget for one coherent context packet;
- file comments disagree on the same profile;
- numeric predictions produce high-scoring files outside the domain;
- tests required for the intent live in a different domain;
- deleted words indicate an abandoned branch.

Parent intent keeps narrative continuity. Children own file mutation and tests.

## Current Keystroke Status

Implemented surfaces now include:

- deterministic intent key generation;
- intent graph generation and prompt splitting;
- domain selection and domain manifests;
- learned intent-file memory;
- prompt brain intent graph context;
- probe push-cycle handoff paths;
- dry-run-safe email delivery behavior;
- operator response policy reward logging;
- deterministic compiler fallback when DeepSeek is unavailable;
- paired-path auto-commit safety tests.

Current verification on 2026-05-28:

- `py -m pytest -q` -> 193 passed, 1 skipped;
- `py test_all.py` -> all tests passed;
- `py -m compileall -q ...` -> passed;
- `git diff --check` -> passed, CRLF warnings only.

## Privacy Rules For Commits

- Do not commit raw prompt journals, raw keystroke logs, MAIF records, private
  shard contents, local `.env` files, or API keys.
- Committed docs may describe architecture, but examples must be schematic.
- Tests may include synthetic prompts only.
- Domain ids may name a class of system, but must not reveal live customer,
  entity, or private operator data.
- Runtime outputs under `logs/` stay local unless a test fixture explicitly
  creates synthetic data.
