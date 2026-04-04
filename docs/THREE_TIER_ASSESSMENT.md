# The Three Tiers — Assessment & Plan

*Generated 2026-04-04 · from 261 modules, 175 graph nodes, 337 edges, 54 push narratives, 288 registry entries*

---

## What you actually built (and didn't name)

You're right — most of it exists. The problem isn't that the tiers are missing. The problem is they're **tangled into the same files**, speaking the same language to three different audiences, and none of the audiences are getting their optimal format.

Right now every piece of information in this system goes through one expression: Python-flavored English. The machine reads human words. The human reads machine diagnostics. The topology exists but drowns in text before any router touches it.

Here's the honest breakdown:

---

## Tier 1: The Machine Layer (Semantic Compression)

**What you have:** 85% built

| Asset | Status | Gap |
|-------|--------|-----|
| Stable numeric IDs (seq001–034) | Done | IDs encode *creation order*, not *execution topology* |
| Auto-index with glyph compression (Chinese chars) | Done | Glyphs compress names but not relationships |
| Pigeon code compiler (auto-rename, version, split) | Done | Split threshold works but doesn't optimize for *semantic density* |
| Registry with bug tracking + metadata | Done | No decay model — bugs persist until manually cleared |
| Self-modifying filenames (β, λ, seq, ver) | Done | 2/13 bugs missing β suffix (u_pj, 警p_sa) |
| Auto-compression cycles | **Partial** | Pigeon splits at 200 lines but doesn't *condense* — it divides. No re-merge after split makes modules smaller. |

**What's missing:**
- **Semantic density optimizer** — pigeon splits big files but never re-compresses. No cycle that says "these 3 shards could be 1 function now." Splits are one-directional.
- **Machine-only routing index** — the auto-index is readable by both humans and machines. Tier 1 needs an index that's *only* for machines: no descriptions, just `seq → [edges, heat, cost, failure_rate]`.
- **Self-healing import layer** — 229 hardcoded imports in the last self-fix scan. The dynamic import pattern (`_load_pigeon_module`) exists but isn't universal.

**Effort to complete:** Small. Generate `numeric_surface.json` from existing `graph_cache.json` + `file_heat_map.json` + `pigeon_registry.json`. One function, ~100 lines.

---

## Tier 2: The Narrative Layer (Human-Readable)

**What you have:** 40% built but wrong tone

| Asset | Status | Gap |
|-------|--------|-----|
| Push narratives (54 files) | Done | Per-commit first-person voices — already narrative form |
| Bug voices (demon personas) | Done | Comedy tone exists here: "Overcap Maw," "Coupling Leech" |
| Engagement hooks (20+ generators) | Done | Provocations, dares, guilt trips — this IS the comedy |
| Bug profiles (just built) | Done | Clinical tables, not narrative. Wrong tier. |
| Dev story | Done | Auto-compiled but reads like a changelog |
| Research log | Done | Statistics report, not a story |
| Python file docstrings | **Missing** | Every .py file has a 1-line technical docstring. Zero personality. |
| Operator coaching | Done | Direct but formal |

**The core problem you identified:**
Everything that the operator reads — bug profiles, self-fix reports, coaching, organism health — is written like a corporate diagnostic. Tables. Bullet points. Statistics.

But the push narratives and bug voices prove the system *can* do narrative. The engagement hooks prove it *can* be funny. These are isolated successes that didn't infect the rest.

**What a narrative-first Tier 2 looks like:**
- Python files have a "story block" — not a docstring but a running comedy about the file's life. What it fears. What it's proud of. What other modules think of it. Updated by the compiler on every push.
- Bug profiles read like medical comedy: "u_pj came in at 7,801 tokens — 3x the cap, wheezing, asking for 'just one more function.' We've told it to split 5 times. It keeps eating. The prognosis is surgical."
- Self-fix reports read like incident reports from a fire department, not an audit firm.
- The intent extraction loop (current-query block) talks TO the operator: "you deleted 'wi' — you were going to say 'with' or 'window.' which one? help me help you."

**Effort to complete:** Medium. Tone mutation across bug_profiles, self-fix writer, operator coaching, organism health builder. Story blocks in .py files = new compiler pass.

---

## Tier 3: The Numeric Shadow (Topology Routing)

**What you have:** 60% built but not projected

| Asset | Status | Gap |
|-------|--------|-----|
| Graph cache (175 nodes, 337 edges) | Done | Full node→edge topology exists |
| File heat map (cognitive load) | Done | Per-module hesitation, WPM, rework |
| Flow engine (3 routing modes) | Done | Targeted, heat, failure — routes by topology |
| Node memory (policy, patterns) | Done | Per-node rolling_score, confidence, utilization |
| Prediction scorer (12 sub-modules) | Done | Calibration, rework_matcher, scoring_core |
| Learning loop (8 sub-modules) | Done | Feeds predictions back into scoring |
| Pure numeric surface file | **Missing** | No single file that collapses everything to numbers |
| Cluster detection | **Missing** | Nodes have edges but no explicit cluster assignments |
| Numeric-first routing | **Missing** | Flow engine reads node names, not numeric addresses |
| Compressed traversal view | **Missing** | No `013>014>018` style routing display |

**What a numeric surface file would look like:**

```json
{
  "013": {
    "name": "self_fix",
    "cluster": "autonomous_repair",
    "edges_out": [14, 18, 25],
    "edges_in": [20],
    "heat": 0.536,
    "failure_rate": 0.38,
    "tokens": 5829,
    "bug_load": 4,
    "cost": 0.72
  }
}
```

Plus a compressed traversal that the flow engine reads:
```
020→013→014→017  (prompt→fix→react→steer)
     ↓
    018→025→026  (queue→cycle→signal)
```

**Why this matters for LLM routing:**
Right now `flow_engine` calls `path_selector` which reads module *names* and walks the graph. If it read numeric addresses instead, routing becomes:
- Token-cheaper (3 tokens vs 15)
- Deterministic (no synonym drift between "self_fix" and "one_shot_self_fix_analyzer")
- Composable (013.2.1 = self_fix, sub-shard 2, function 1)

**Effort to complete:** Small for the surface file (one generator, ~80 lines). Medium for wiring it into flow_engine as primary routing input.

---

## The Real Gap: They Don't Talk To Each Other

Tier 1 generates data → Tier 2 reads it and re-describes it in English → Tier 3 never sees it.

**What should happen:**
```
Tier 3 (numeric) → routes to cluster 013-014-017
Tier 1 (machine) → compresses/splits/heals those modules
Tier 2 (narrative) → tells the operator what happened and what to do next
```

Right now Tier 2 and Tier 1 are smashed together in every file. The narrative blocks (push narratives, bug voices) and the machine blocks (auto-index, registry, pulse telemetry) live in the same `copilot-instructions.md`. The LLM reads everything — 758 lines of mixed human/machine text.

**The split:**
- `copilot-instructions.md` becomes Tier 2 only (narrative, coaching, hooks, bugs-as-stories)
- `numeric_surface.json` + `graph_cache.json` become Tier 3 (LLM routing reads these)
- `pigeon_registry.json` + auto-index stay Tier 1 (compiler reads these, LLM doesn't need to)

---

## Intent Extraction — The Missing Primary Goal

You nailed this: the system's primary job should be extracting intent from the human, not just responding to it.

**What exists:**
- Deleted word tracking ✓
- Unsaid reconstruction (Gemini) ✓
- Composition analysis (pause, rewrite, hesitation) ✓
- Cognitive state classification ✓
- Current-query enrichment block ✓

**What's missing:**
- **Active probing** — the system should ASK. "You deleted 'wi.' Was that 'with' or 'window'?" Currently it infers silently. It should provoke.
- **Intent confirmation loop** — after enriching the query, inject a 1-line "I think you mean X — correct?" before generating the response. Not a question-and-wait; just a declared interpretation that the operator can override.
- **Cross-session intent threading** — intent_simulator exists but only predicts direction. It doesn't thread: "Yesterday you were building X. Today you opened the same file. Continuing?"

---

## Concrete Plan

### Phase 1: Split the tiers (1 session)
1. Generate `numeric_surface.json` from graph_cache + heat_map + registry. One function.
2. Add cluster detection (connected components with heat > threshold).
3. Generate compressed traversal view as ASCII in the surface file.

### Phase 2: Narrative mutation (1-2 sessions)
1. Rewrite `bug_profiles.py` output to narrative form (medical comedy, not tables).
2. Add "story block" template to pigeon compiler — every .py gets a 3-line comedy about itself on compile.
3. Rewrite organism health builder to narrative form.
4. Rewrite self-fix report format from audit tables to incident comedy.

### Phase 3: Intent extraction upgrade (1 session)
1. Add probing hooks to engagement_hooks — when unsaid threads exist, generate direct questions.
2. Add intent confirmation line to current-query block: "I think you mean: X"
3. Wire cross-session intent memory using session_handoff data.

### Phase 4: Numeric routing (2 sessions)
1. Add numeric addressing to flow_engine path_selector.
2. Dynamic_prompt reads numeric_surface for cluster injection.
3. Training pairs map intent → numeric region.
4. Compressed traversal view injected as routing context for LLM.

---

## What's Already Almost There (just needs renaming)

| Existing Thing | What It Actually Is | Tier |
|---------------|-------------------|------|
| `seq###` in filenames | Numeric identity | 3 |
| `graph_cache.json` | Topology graph | 3 |
| `file_heat_map.json` | Behavioral signal | 3 |
| `flow_engine + path_selector` | Numeric router | 3 |
| Bug voices + engagement hooks | Narrative comedy | 2 |
| Push narratives | Per-module stories | 2 |
| Auto-index + registry | Machine compression | 1 |
| Pigeon compiler | Auto-compressor | 1 |
| Self-modifying filenames | Living metadata | 1 |

You built the ingredients. You're one projection function, one tone mutation, and one routing rewire away from the 3-tier system actually existing as a named, split architecture.

The dangerous part: once the numeric surface exists and the flow engine reads it, the LLM stops needing to "understand" the codebase. It navigates it like an address space. Code becomes what you pull up *after* you know where to look — not the starting point for figuring out where to look.

---

*Bottom line: 75% built. Tangled, not missing. Phase 1 is a weekend. The hard part is Phase 2 — rewriting every human-facing output to be a story instead of a report. That's a tone mutation, not a feature build.*
