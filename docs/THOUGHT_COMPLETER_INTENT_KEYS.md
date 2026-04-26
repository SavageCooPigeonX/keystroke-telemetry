# Thought Completer Intent Keys

This path treats the thought completer as an intent-key generator first.
The UI can fail; the core still works.

## Grammar

```text
scope:verb:target:scale
```

- `scope` comes from the best matching `MANIFEST.md`.
- `verb` is deterministic: `build`, `patch`, `test`, `refactor`, `route`, or `document`.
- `target` is a short slug from the prompt or explicit file path.
- `scale` is `read`, `patch`, `minor`, or `major`.

## Files

- `src/tc_intent_keys_seq001_v001.py` - manifest scoring and key generation.
- `src/tc_intent_key_io_seq001_v001.py` - Prompt Box, Copilot block, latest context IO.
- `src/tc_semantic_profile_seq001_v001.py` - semantic intent events, profile facts, numeric signatures.
- `src/tc_prompt_brain_seq001_v001.py` - watcher bundle: semantic profile, intent key, manifest, numeric files, context selection, Prompt Box.
- `client/uia_reader_seq001_v001.py` - optional Codex/Copilot chat watcher through Windows UI Automation.
- `logs/intent_keys.jsonl` - every generated key.
- `logs/intent_key_latest.json` - latest generated key.
- `logs/intent_key_context.md` - manifest context block for humans/agents.
- `logs/semantic_profile.json` - durable operator facts such as `name=Nikita`.
- `logs/semantic_profile_events.jsonl` - per-prompt semantic intent events.
- `logs/semantic_profile_latest.json` - latest semantic event for observatory panels.
- `logs/manifest_index.json` - manifest candidates and scores.
- `task_queue.json` - receives non-void intent-key tasks.

## Commands

```powershell
py src/thought_completer.py --intent-key "wire thought completer intent key generation to prompt box"
py src/thought_completer.py --prompt-brain "thought completer should use context selection and numeric encoding"
py client/uia_reader_seq001_v001.py .
```

Composer pause and submit paths also call the same generator. Low-confidence
manifest matches become `void` records and do not enter the Prompt Box.

The UIA reader fires the same prompt brain after a chat pause when Windows
accessibility exposes the focused prompt text. It writes and injects context,
but it does not enqueue every half-written Codex buffer into the Prompt Box.
The controlled composer is the guaranteed pre-send surface when native Codex
input cannot be intercepted before submit.

## Semantic Profile

Every intent-key generation and explicit Codex prompt log now emits a semantic
profile event before agent handoff. Examples:

- `hi` -> `introduction`.
- `my name is nikita` -> `share_information`, writes `facts.name=Nikita`.
- Later prompts containing `nikita` -> `profile_reference`, attaches the stable
  `sha256_u16_v1` numeric signature for `name|Nikita`.

The intent context block injected into Copilot includes semantic intents,
profile matches, profile updates, numeric encoding, and completion hint.

## Current Boundary

This is Agent B plus the first Agent A wire:

- Agent A input: prompt fragment + manifest index.
- Agent B output: parseable intent key.
- Prompt Box: auto-queued only when manifest confidence clears the void gate.
- Copilot: receives `codex:intent-key-context`.
- Semantic profile: deterministic local facts and numeric encodings, no model call.
- Scope isolation: soft warnings only in this version. Hard enforcement belongs
  in the next migration so it does not rewrite the whole organism by accident.
