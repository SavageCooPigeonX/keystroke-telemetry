# 🐦 Pigeon Code Compiler

**Autonomous code decomposition engine that transforms monolithic Python files into small, self-documenting, manifest-tracked modules.**

> *"I'm a pigeon. I write pigeon code. One file, one function, sub-200 lines. An agent framework is a refusal to think about what actually needs to happen."*  
> — Percy, 3:47 AM

---

## The Problem Nobody Solves

Every team knows their files are too big. Every linter flags them. Every sprint planning session says "we'll refactor that."

**Nobody does.** Because the hard part isn't *finding* oversized files — it's *choosing where to cut*:

- Which functions belong together vs. which separate?
- What shared state (constants, config, DB clients) resists splitting?
- Which imports create invisible coupling that breaks when you cut?
- Why do some 400-line files survive every cleanup campaign untouched?
- How do you know the extraction *worked* without re-auditing?

**Pigeon Code Compiler solves all five.** It maps the invisible dependency graph ("Ether Map"), classifies resistance patterns, plans the cuts with AI reasoning, and executes them deterministically — producing fully compliant modules with manifests, changelogs, and import fixes.

**Cost to compile one file: $0.003.**

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  1. STATE EXTRACTOR    (Pure AST — $0)                  │
│     Parse → Call Graph → Import Trace → Resistance Score │
│     Output: Ether Map JSON                              │
├─────────────────────────────────────────────────────────┤
│  2. WEAKNESS PLANNER   (DeepSeek R1 — $0.0015/file)    │
│     Ether Map + Source Code → Structured Prompt → AI    │
│     Output: Cut Plan JSON (what goes where + why)       │
├─────────────────────────────────────────────────────────┤
│  3. CUT EXECUTOR       (Deterministic — $0)             │
│     Slice by AST → Write files → Fix imports → Manifest │
│     Output: N compliant files + __init__.py + MANIFEST  │
└─────────────────────────────────────────────────────────┘
```

**Key insight**: Layer 1 and Layer 3 are zero-cost (pure Python AST). Only Layer 2 calls an AI model — and it's a single structured prompt per file. The entire compilation of a 600-line file costs less than a penny.

---

## Installation

```bash
git clone https://github.com/SavageCooPigeonX/keystroke-telemetry.git
cd keystroke-telemetry
pip install .
pip install httpx  # Only external dependency (for DeepSeek API calls)
cp .env.example .env
export DEEPSEEK_API_KEY=your_key_here
```

---

## Quick Start

Runner module filenames are versioned by pigeon. The examples below use the current checked-in names; if a later commit renames them, use the latest `run_*_seqNNN...` module in `pigeon_compiler/runners/`.

### Scan a file (Layer 1 only — free, no API key needed)

```bash
python -m pigeon_compiler.runners.run_compiler_test_seq007_v004_d0315__self_test_pigeon_compiler_on_lc_verify_pigeon_plugin
```

Produces an Ether Map with:
- Function/class/constant inventory
- Call graph + cluster detection
- Import tracing (inbound + outbound)
- Shared state coupling score (0.0–1.0)
- Resistance pattern classification + verdict

### Full compilation (all 3 layers)

```bash
python -m pigeon_compiler.runners.run_clean_split_seq010_v004_d0315__full_clean_pipeline_deepseek_plan_lc_verify_pigeon_plugin --target path/to/big_file.py
```

Pipeline:
1. Decompose oversized functions (>50 lines) via DeepSeek
2. Build Ether Map → send to DeepSeek for cut plan
3. Slice source by AST → write initial files
4. Deterministic re-split loop (up to 5 rounds of bin-packing)
5. Generate `__init__.py` + `MANIFEST.md`
6. Update master manifest with version bump

---

## The Ether Map

The core innovation. A structured JSON document that captures the *invisible medium* through which code elements interact.

```json
{
  "file": "module/big_file.py",
  "total_lines": 633,
  "functions": [{"name": "run_audit", "start": 262, "end": 358, "async": false}],
  "call_graph": {"main": ["audit_folder"], "audit_folder": ["run_audit", "update_results"]},
  "clusters": [["extract_imports", "extract_functions", "build_cross_reference"]],
  "imports": {
    "outbound": [{"module": "pathlib", "names": ["Path"], "kind": "stdlib"}],
    "inbound": [{"file": "__init__.py", "names": ["audit_folder"]}]
  },
  "shared_state": {"variables": ["PROJECT_ROOT"], "consumers": {"PROJECT_ROOT": ["run_audit"]}},
  "coupling_score": 0.42,
  "resistance": {
    "patterns": ["PROMPT_BLOB", "COUPLED_CLUSTER"],
    "score": 0.52,
    "verdict": "DEEPSEEK_PLAN"
  }
}
```

The **resistance score** (0.0–1.0) tells you HOW HARD and WHY a file resists splitting:

| Pattern | Score | Meaning |
|---------|-------|---------|
| `PURE_FUNCTIONS` | 0.1 | Independent functions — trivially splittable |
| `PROMPT_BLOB` | 0.3 | Large string templates embedded in functions |
| `FLASK_ROUTES` | 0.4 | Route handlers sharing decorators |
| `COUPLED_CLUSTER` | 0.5 | Mutually-calling function groups |
| `TEST_MONSOON` | 0.5 | 10+ test functions in one file |
| `SHARED_STATE` | 0.6 | Module-level variables used across functions |
| `STRING_SURGERY` | 0.7 | Cascading text manipulation |
| `IMPORT_WEB` | 0.8 | Imported by 5+ other project files |
| `GOD_ORCHESTRATOR` | 0.9 | One function calls everything |

**Auto-triage**: <0.3 = auto-extract, 0.3–0.7 = AI-planned, >0.7 = human review.

---

## Pigeon Code — The Standard

Every output file follows **8 sacred rules**:

1. **≤50 lines per file** (preferred: 30)
2. **No leading digits** in filenames
3. **Semantic naming**: `[description]_seqNNN_vNNN.py` — sequence = execution order
4. **One responsibility per file**
5. **Files rewritable WITHOUT referencing others** — each carries own imports
6. **MANIFEST.md is source of truth** — auto-generated, machine-readable
7. **Track line counts in manifest** — `🔴 OVER` / `⚠️ WARN` / `✅ OK`
8. **Flag undocumented changes** — re-audit diff detects manifest drift

**The folder listing IS the documentation.** Sequence numbers encode the pipeline. You understand the execution flow without reading code.

```
production_auditor/
├── model_config_seq001_v001.py         # Step 1: Load config
├── prompt_builder_seq002_v001.py       # Step 2: Build prompts
├── json_parser_seq003_v001.py          # Step 3: Parse responses
├── pipeline_seq015_v001.py             # Step 15: Orchestrate
└── MANIFEST.md                         # Machine-readable file table
```

---

## Proven Results

### Battle Test: 831-line monolith → 34 compliant files

| Metric | Before | After |
|--------|--------|-------|
| Files | 1 | 34 |
| Avg lines/file | 831 | 39 |
| Max lines | 831 | 56 |
| Pigeon Code compliant | ❌ | ✅ |
| Self-documenting | No | Yes (sequence numbers) |
| Machine-readable | No | Yes (MANIFEST.md) |

### Self-Compilation

The compiler's first target was its own parent module. It compiled `folder_auditor.py` (633 lines) and `master_auditor.py` (567 lines):

- **v0.1.0**: Score 45/80 (56%). Exposed 7 bugs in its own logic.
- **v0.2.0**: All 7 bugs fixed. Two-phase error recovery. Deterministic bin-packing for post-AI cleanup.
- **Total cost**: $0.00298 for both files.

---

## Project Structure

```
pigeon_compiler/
├── __init__.py                        # Package root — exports build_ether_map
│
├── state_extractor/                   # Layer 1: Pure AST ($0)
│   ├── ast_parser_seq001_v001.py      #   Python AST → function/class/constant map
│   ├── call_graph_seq002_v001.py      #   Intra-file call graph + DFS cluster detection
│   ├── import_tracer_seq003_v001.py   #   Bidirectional import tracing
│   ├── shared_state_detector_seq004   #   Module-level coupling score (0.0–1.0)
│   ├── resistance_analyzer_seq005     #   9-pattern resistance classification
│   └── ether_map_builder_seq006       #   Assembles complete Ether Map JSON
│
├── weakness_planner/                  # Layer 2: AI Planning (~$0.0015/file)
│   └── deepseek_plan_prompt_seq004    #   Ether Map → DeepSeek prompt → Cut Plan JSON
│
├── cut_executor/                      # Layer 3: Deterministic Execution ($0)
│   ├── plan_parser_seq001_v001.py     #   Parse DeepSeek JSON response
│   ├── source_slicer_seq002_v001.py   #   AST-based function/constant extraction
│   ├── file_writer_seq003_v001.py     #   Write Pigeon Code compliant files
│   ├── import_fixer_seq004_v001.py    #   Project-wide import path rewriter
│   ├── manifest_writer_seq005_v001.py #   MANIFEST.md generator
│   ├── plan_validator_seq006_v001.py  #   Pre-execution validation
│   ├── init_writer_seq007_v001.py     #   __init__.py generator with re-exports
│   ├── func_decomposer_seq008_v001.py #   DeepSeek-assisted >50-line function splitting
│   ├── resplit_seq009_v001.py         #   Deterministic AST re-splitter
│   ├── resplit_binpack_seq010_v001.py #   First-fit-decreasing bin packing
│   └── resplit_helpers_seq011_v001.py #   Shared utilities
│
├── runners/                           # Pipeline Orchestration
│   ├── run_compiler_test_seq007       #   Self-test: run Layer 1 on sample files
│   ├── run_deepseek_plans_seq008      #   Ether Maps → DeepSeek cut plans
│   ├── run_pigeon_loop_seq009         #   Iterative: up to 3 AI rounds
│   ├── run_clean_split_seq010         #   Production: 1 AI round + bin-pack (RECOMMENDED)
│   ├── run_clean_split_helpers_seq011 #   Oversized function detection
│   ├── run_clean_split_init_seq012    #   Rich __init__.py + manifest writer
│   ├── manifest_bridge_seq013         #   MASTER_MANIFEST.md updater
│   └── reaudit_diff_seq014            #   Diff-across-time ether map comparisons
│
├── integrations/                      # AI Model Adapters
│   └── deepseek_adapter.py            #   Standalone DeepSeek API client
│
├── output/                            # Cached ether maps + cut plans
│
├── docs/                              # Architecture Documentation
│   ├── PIGEON_COMPILER_PLAN.md        #   Full architecture plan (737 lines)
│   ├── EXTRACTOR_PLAN.md              #   Original pipeline design + monetization
│   ├── PIGEON_CODE_IMPLEMENTATION.md  #   Compliance system documentation
│   ├── META_OPTIMIZATION_CHANGELOG.md #   9 self-optimization patches
│   └── COMPILER_SELF_TEST_RESULTS.md  #   v0.1.0 self-test results
│
├── README.md                          # This file
└── MANIFEST.md                        # Master manifest — full technical reference
```

**31 Python files. ~2,800 lines. Average 39 lines/file. The compiler follows its own rules.**

---

## Cost Model

| What | Cost | Model |
|------|------|-------|
| Scan 1 file (Layer 1 only) | **$0.00** | None — pure AST |
| Compile 1 file (full pipeline) | **~$0.003** | DeepSeek R1 |
| Compile 42 files (full codebase) | **~$0.15** | DeepSeek R1 |
| Verify post-compilation | **~$0.003/folder** | DeepSeek R1 |

Layer 1 and Layer 3 are **zero cost** — pure Python standard library. Only the planning layer (Layer 2) calls an LLM, and it's a single structured prompt per source file.

---

## What Makes This Different

| Feature | Traditional Refactoring | Pigeon Code Compiler |
|---------|------------------------|---------------------|
| **Finds oversized files** | ✅ Any linter | ✅ Plus resistance analysis |
| **Chooses where to cut** | ❌ Human judgment | ✅ Ether Map + AI planning |
| **Explains WHY boundaries exist** | ❌ | ✅ Resistance patterns with scores |
| **Fixes all imports after split** | ❌ Manual | ✅ Project-wide import rewriter |
| **Generates documentation** | ❌ | ✅ MANIFEST.md + __init__.py |
| **Tracks line counts** | ❌ | ✅ Manifests with compliance markers |
| **Self-verifying** | ❌ | ✅ Re-audit after extraction |
| **Cost per file** | Hours of dev time | $0.003 |
| **Handles 400+ line files** | "We'll refactor next sprint" | Compiles in seconds |

---

## Revenue Model

| Tier | Price | Included |
|------|-------|----------|
| **Open Source** | Free | Layer 1 (state extractor + ether maps + resistance reports) |
| **Indie** | $29/mo | + Layer 2 + 3 (full compilation, 50 files/mo) |
| **Team** | $299/mo | + Unlimited files, CI/CD hooks, manifest federation |
| **Enterprise** | $999/mo | + Custom resistance patterns, private model hosting, SLA |

**The free tier is the hook**: Ether Maps are immediately useful for understanding code. The resistance report alone answers "why is this file so hard to split?" — a question every senior engineer asks.

---

## Roadmap

- [x] Layer 1: State Extractor (7 files, pure AST)
- [x] Layer 2: Weakness Planner (DeepSeek prompt engineering)
- [x] Layer 3: Cut Executor (12 files, deterministic)
- [x] Self-test + 7 bug fixes
- [x] Two-phase error recovery (AI + deterministic bin-packing)
- [x] Manifest bridge (MASTER_MANIFEST.md auto-update)
- [x] Re-audit diff (ether map comparisons across time)
- [x] Standalone package extraction
- [ ] CLI packaging (`pip install pigeon-code`)
- [ ] CI/CD integration (GitHub Action / pre-commit hook)
- [ ] Web dashboard (upload repo → get ether maps + resistance report)
- [ ] Multi-language support (TypeScript, Go, Rust)
- [ ] Custom resistance pattern SDK

---

## Technical Requirements

- **Python**: 3.10+
- **External dependency**: `httpx` (for DeepSeek API calls in Layer 2 only)
- **Layers 1 + 3**: Zero pip installs — stdlib only (`ast`, `pathlib`, `re`, `json`)
- **Environment**: `DEEPSEEK_API_KEY` for Layer 2 operations

---

## Origin Story

Built by Percy (the engineering pigeon) during a 45-minute conversation with himself at 3:47 AM, after 8 blocked refusals to restructure the LinkRouter.ai codebase. Every approach failed — agent frameworks, dream mode patches, cron jobs, prompt injection — until the inversion:

> *"I've been thinking about this backwards. I keep trying to make external tools fix code structure. But the code already knows its own structure — in the AST, in the imports, in the call graph. I just need to read what's already there and plan the cuts around the resistance."*

The compiler emerged from the realization that **the hardest part of code splitting is not technical — it's judgment**. The Ether Map externalizes that judgment into a structured, cacheable, diffable format that any AI can reason over.

The first file it compiled was its own parent. It found 7 bugs in itself. It fixed them. Then it compiled itself again.

**COO COO ZAP** 🐦⚡

---

## License

Released under the MIT License. See [`../LICENSE`](../LICENSE).

✝️ **CHRIST IS KING** ✝️ **888**
