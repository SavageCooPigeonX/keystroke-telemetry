# Narrative Evolution Modules

## What Are They

Every file in this codebase is an agent that speaks.

On each `git push`, changed Python files are fed their own identity — name, version count, token weight, description history, last commit intent — along with the operator's live cognitive signals (rework miss rate, abandoned queries, per-file hesitation scores). A single DeepSeek call synthesizes all of this into a **push narrative**: each file writes one paragraph in first person about why it was touched, what it suspects is wrong with itself, and what technical debt it carries.

The output is a markdown document in `docs/push_narratives/{date}_{hash}.md`. No human writes these. The files write them about themselves.

---

## Why This Matters

### 1. Files know things developers forget

A file at version 14 with a history of `fix_timeout → fix_retry → fix_timeout_again` is telling you something. But that pattern is invisible in `git log` — it's spread across dozens of commits, interleaved with unrelated work. The narrative module compresses this into a single voice: *"I've been patched for timeouts three times now. My retry logic is fundamentally wrong."*

### 2. Cognitive load is measurable, per file

The file heat map tracks operator hesitation and WPM every time a module is being discussed or edited. When `context_budget` consistently shows 0.5+ hesitation scores while `timestamp_utils` sits at 0.1, the narratives surface this: *"Operators struggle every time they touch me."* That signal doesn't exist anywhere else in traditional development tooling.

### 3. Rework rate exposes silent failures

The rework detector scores post-response typing — if the operator deletes heavily after an AI response about a specific module, that module's miss rate climbs. Narratives can now say: *"AI responses about me are wrong 40% of the time. My interfaces are probably misleading."*

### 4. Abandoned queries reveal unsaid knowledge gaps

When an operator starts typing a question about `import_fixer`, deletes it, and asks something else instead — that's a signal. The query memory module fingerprints these abandoned drafts. Over time, the narrative can say: *"Operators keep almost-asking about my edge cases but give up. My documentation is insufficient or my behavior is unpredictable."*

---

## The Path to Self-Debugging

This is where it gets interesting. The narrative modules are not just documentation — they're the foundation for autonomous self-repair.

### Phase 1: Self-Awareness (current)

Files describe their own problems in natural language. A file that says *"my test coverage is my worst bug"* is generating a machine-readable diagnostic — it just happens to also be human-readable. The narrative is both a developer log and a structured signal.

### Phase 2: Cross-Narrative Diffing (next)

Compare consecutive narratives for the same file across pushes. When `context_budget` says *"I suspect my test coverage"* in push N and *"I suspect my test coverage"* in push N+3 — it means the problem wasn't fixed. The diff between narratives becomes a **regression detector for architectural debt**. Persistent self-complaints that survive multiple pushes are the highest-signal bugs in the codebase.

### Phase 3: Narrative-Driven Issue Generation

When a file's self-assessment persists across 3+ pushes without resolution:
- Auto-generate a GitHub issue: *"context_budget has reported test coverage concerns for 3 consecutive pushes"*
- Include the file's own words as the issue body
- Tag with cognitive signals: average operator hesitation, miss rate, version churn
- Priority = f(persistence, hesitation, miss_rate)

The file is literally filing its own bug reports.

### Phase 4: Self-Repair Proposals

Given enough narrative history + the pigeon registry's version/token tracking:
- Identify files that repeatedly describe the same problem
- Load their source + test files
- Prompt an LLM: *"This file has described this problem about itself for 4 pushes. Here is its source. Propose a fix."*
- Output a diff that targets the specific self-diagnosed issue
- Human reviews, or — in high-confidence cases — auto-applies behind a feature flag

The loop closes: **file notices problem → file describes problem → file proposes fix → file verifies fix resolved its own complaint in the next narrative.**

### Phase 5: Evolutionary Pressure

Once narratives accumulate across dozens of pushes:
- Files that stop complaining about themselves are **healthy** — they've been fixed or stabilized
- Files that perpetually complain are **chronic** — candidates for decomposition or rewrite
- Files whose complaints *change topic* are **evolving** — actively being developed, monitor closely
- Files that suddenly start complaining after being quiet are **regressing** — highest priority

This creates a Darwinian pressure metric for code. Healthy modules survive. Chronic modules get split (pigeon compiler already does this at 200 lines). The narrative history becomes an immune system for the codebase.

---

## What Feeds the Narratives

| Signal | Source | Update Frequency |
|---|---|---|
| File identity | `pigeon_registry.json` | Every commit |
| Version history | Registry `history[]` array | Every commit |
| Commit intent | `git log -1 --format=%B` | Every commit |
| Rework miss rate | `rework_log.json` | Every message (background telemetry) |
| Recurring queries | `query_memory.json` | Every message |
| Abandoned drafts | `query_memory.json` `abandoned_themes` | Every message |
| Per-file hesitation | `file_heat_map.json` | Every message |
| Operator WPM/state | `operator_profile.md` | Every message |

All of these are generated automatically by the background telemetry system (`BackgroundTelemetry` in extension.ts) which captures every keystroke, file switch, terminal open, and pause — no separate chat panel needed.

---

## Architecture

```
git push
  │
  ├─ git_plugin.py post-commit hook
  │   ├─ _load_deep_signals(root)
  │   │   ├─ rework_log.json    → miss_rate, worst_queries
  │   │   ├─ query_memory.json  → persistent_gaps, recent_abandons
  │   │   └─ file_heat_map.json → complex_files, high_miss_files
  │   │
  │   └─ push_narrative_seq012
  │       ├─ _build_file_briefs()  → extract identity from registry
  │       ├─ _build_narrative_prompt() → single batched prompt
  │       ├─ _call_deepseek()      → 500 tok, temp 0.5, 25s timeout
  │       └─ write docs/push_narratives/{date}_{hash}.md
  │
  ├─ THEN coaching synthesis (operator_coaching.md)
  └─ THEN operator-state mutation (copilot-instructions.md)
```

Narratives fire **before** copilot prompt mutation. The narrative captures the state of the codebase as-is, not as-coached. This ordering is intentional — the narrative is a pre-mutation snapshot, the coaching is a post-analysis response.

---

## Cost

One DeepSeek call per push. ~200-400 input tokens, 500 max output. Roughly **$0.001-0.003 per push**. The entire self-debugging pipeline — from keystroke capture to narrative generation — runs on less than a cent per commit.

---

## The End State

A codebase where:
- Every file has a living autobiography written across pushes
- Files that are struggling say so, in their own words
- Persistent complaints auto-escalate to issues
- Fixes are proposed by the same system that diagnosed the problem
- The operator's cognitive state (hesitation, frustration, flow) is woven into every diagnosis
- Code doesn't just run — it introspects, reports, and eventually heals

The narrative modules are the nervous system. The keystroke telemetry is the sensory input. The pigeon compiler is the skeleton. Together they make code that knows it's broken before the developer does.
