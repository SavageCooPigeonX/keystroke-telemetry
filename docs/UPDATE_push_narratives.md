# Update: Push Narrative System

**Date**: 2026-03-16  
**Commit**: pending (built this session)  
**Module**: `push_narrative_seq012_v001.py` (src/)  
**Hook**: `pigeon_compiler/git_plugin.py`  

---

## What Was Built

A **per-push development narrative generator** where every changed Python file speaks in first person about why it was touched, what it suspects about its own bugs, and what technical debt it carries — all synthesized by DeepSeek from the pigeon registry + deep operator signals.

### Output

Each `git push` that touches `.py` files now produces:

```
docs/push_narratives/{YYYY-MM-DD}_{commit_hash}.md
```

Example (live-tested against real registry):

> *I am context_budget, a scorer that allocates token windows for LLM sessions. My last five versions were all about coaching workflows, but now I'm being wired into a narrative agent system. I suspect my test coverage is my worst bug; a miss_rate of 1.0 on my tests means any new branching logic I'm given could fail silently.*

---

## Pipeline Position

The narrative fires **after** file changes are processed but **before** copilot prompt mutation — so the narrative captures the state of the codebase without being influenced by coaching rewrites.

```
git commit (post-commit hook)
  │
  ├─ 1. Parse intent, rename files, rewrite imports
  ├─ 2. Inject prompt boxes, save registry
  ├─ 3. Refresh auto-index in copilot-instructions.md
  │
  ├─ 4. ██ PUSH NARRATIVE ██  ← NEW
  │     │  Load deep signals (rework_log, query_memory, file_heat_map)
  │     │  Build file briefs from registry (name, seq, ver, tokens, history)
  │     │  Single batched DeepSeek call (500 tok max, temp 0.5)
  │     └─ Write docs/push_narratives/{date}_{hash}.md
  │
  ├─ 5. Generate commit coaching → operator_coaching.md
  ├─ 6. Refresh operator-state in copilot-instructions.md (prompt mutation)
  └─ 7. Auto-commit [pigeon-auto]
```

---

## Architecture

### Module: `src/push_narrative_seq012_v001.py`

| Function | Purpose |
|---|---|
| `generate_push_narrative()` | Entry point. Loads briefs, calls DeepSeek, writes markdown |
| `_build_file_briefs()` | Extracts identity from registry: name, seq, ver, desc, intent, tokens, history depth |
| `_build_narrative_prompt()` | Single batched prompt — all files voice themselves + operator deep signals |
| `_call_deepseek()` | stdlib urllib, 25s timeout, no external deps |

### Hook: `git_plugin.py` additions

| Addition | Purpose |
|---|---|
| `_load_deep_signals(root)` | Shared helper — loads rework_log, query_memory, file_heat_map into a dict |
| `_load_glob_module(root, folder, pattern)` | Dynamic pigeon import by glob (filenames mutate on commit) |
| Narrative call block (line ~808) | Calls `generate_push_narrative()` between auto-index and coaching |

---

## Input Signals

The narrative prompt receives:

| Signal | Source | What It Tells the File |
|---|---|---|
| Registry entry | `pigeon_registry.json` | Version count, token history, description lineage |
| Commit intent | `git log -1` | Why the push happened |
| Rework stats | `rework_log.json` | Miss rate, worst queries — AI answer quality |
| Query memory | `query_memory.json` | Recurring questions, abandoned themes — persistent knowledge gaps |
| File heat map | `file_heat_map.json` | Per-module hesitation, WPM, miss count — cognitive load per file |

---

## Cost

- **Single DeepSeek call per push** (not per file)
- Max 500 output tokens, ~200-400 input tokens depending on file count
- Estimated: **~$0.001–0.003 per push**
- Only fires when `.py` files are changed (documentation-only commits skip)

---

## Constraints

- **Only fires on changes**: If `renames` and `box_only` are both empty, narrative is skipped entirely
- **Gracefully absent signals**: If rework_log / query_memory / file_heat_map don't exist yet, narrative still generates with reduced context
- **No API key = silent skip**: Returns `None`, prints nothing, doesn't block the pipeline
- **Timeout 25s**: Single call, no retry loop — if DeepSeek is slow, pipeline continues without narrative

---

## Testing

| Test | Result |
|---|---|
| Syntax check (ast.parse) | PASS — both narrative module and git_plugin |
| Dry run (no LLM) | PASS — prompt builds correctly from registry |
| Live DeepSeek call | PASS — generated `2026-03-16_abc1234.md` |
| Core tests (test_all.py) | 4/4 PASS |
| Deep tests (deep_test.py) | 8/8 PASS |

---

## What's Next

- **Claude audit layer** (discussed, not yet built): Takes the narrative output + all deep signals and writes a longer-form development journal. Would sit between step 4 and 5, or as a separate post-push webhook.
- **Narrative diffing**: Compare consecutive narratives to detect when a file's self-assessment changes — signal for architecture drift.
- **Auto-gitignore test narratives**: The `abc1234` test file should be cleaned up before commit.
