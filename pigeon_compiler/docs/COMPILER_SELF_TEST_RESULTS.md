# COMPILER_SELF_TEST_RESULTS.md
## Pigeon Compiler v0.1.0 — Self-Test on folder_auditor.py + master_auditor.py

**Date**: 2026-03-01  
**Test**: End-to-end pipeline — State Extractor → Ether Map → DeepSeek Cut Plan  
**Cost**: $0.00298 total ($0.001523 + $0.001461)  
**Tokens**: 19,470 total (17,628 input + 1,842 output)

---

## 🧪 PHASE 1: ETHER MAP EXTRACTION (Layer 1 — Zero-cost AST)

### folder_auditor.py
| Metric | Value |
|--------|-------|
| Total lines | 633 |
| Functions | 19 |
| Classes | 0 |
| Constants | 6 (PROJECT_ROOT, SKIP_FOLDERS, SKIP_FILES, PIGEON_MAX_LINES, PIGEON_WARNING_LINES, AUDITABLE_FOLDERS) |
| Clusters | 1 (all 19 functions connected) |
| Coupling score | 0.45 |
| Resistance score | **0.9 / 1.0 → HUMAN_REVIEW** |
| Resistance patterns | PROMPT_BLOB ×2, COUPLED_CLUSTER, GOD_ORCHESTRATOR |

### master_auditor.py
| Metric | Value |
|--------|-------|
| Total lines | 567 |
| Functions | 12 |
| Classes | 0 |
| Constants | 7 (PROJECT_ROOT, FOLDERS_TO_AUDIT, MASTER_MANIFEST, OUTPUT_FILE, AUDIT_CACHE_FILE, PIGEON_MAX_LINES, PIGEON_WARNING_LINES) |
| Clusters | 1 (all 12 functions connected via run_master_audit) |
| Coupling score | 0.30 |
| Resistance score | **0.9 / 1.0 → HUMAN_REVIEW** |
| Resistance patterns | PROMPT_BLOB ×1, COUPLED_CLUSTER, GOD_ORCHESTRATOR |

### Ether Map Verdict
Both files are GOD_ORCHESTRATOR files — single functions (`run_audit`, `run_master_audit`) that call 7-11 other functions, creating one giant connected cluster. This makes the call graph almost useless for automatic clustering because everything is transitively connected. **The compiler correctly identified this as the #1 challenge.**

---

## 🤖 PHASE 2: DEEPSEEK CUT PLANS (Layer 2 — $0.003)

### folder_auditor.py → DeepSeek proposed 9 files

| # | New File | Functions | DeepSeek Est. | **ACTUAL Lines** | **Verdict** |
|---|----------|-----------|---------------|-------------------|-------------|
| 1 | constants_seq001 | 6 constants | 15 | ~15 | ✅ PASS |
| 2 | file_utils_seq002 | validate_pigeon_filename, get_file_line_count, get_folder_path | 35 | ~35 | ✅ PASS |
| 3 | folder_scan_seq003 | list_folder_contents, read_all_files | 45 | **~72** | ❌ FAIL (>50) |
| 4 | code_analysis_seq004 | extract_imports, extract_functions, build_cross_reference | 40 | **~58** | ❌ FAIL (>50) |
| 5 | manifest_ops_seq005 | load_local_manifest, load_master_manifest, load_previous_audit, generate_folder_structure | 45 | **~62** | ❌ FAIL (>50) |
| 6 | audit_core_seq006 | run_audit, update_audit_results | 50 | **~180** | ❌❌ CRITICAL (run_audit=131 lines alone) |
| 7 | task_management_seq007 | extract_tasks_from_audit, update_local_manifest | 45 | **~84** | ❌ FAIL (update_local_manifest=69 lines) |
| 8 | orchestrator_seq008 | audit_folder, audit_all | 40 | **~67** | ❌ FAIL (>50) |
| 9 | cli_seq009 | main | 30 | ~30 | ✅ PASS |

**Pass rate: 3/9 (33%)**

### master_auditor.py → DeepSeek proposed 8 files

| # | New File | Functions | DeepSeek Est. | **ACTUAL Lines** | **Verdict** |
|---|----------|-----------|---------------|-------------------|-------------|
| 1 | data_collector_seq001 | collect_manifests, collect_audit_results, get_master_manifest + 2 constants | 48 | **~68** | ❌ FAIL (>50) |
| 2 | pigeon_checker_seq002 | check_pigeon_violations + 2 constants | 42 | ~47 | ✅ PASS |
| 3 | db_stats_seq003 | get_db_stats | 38 | ~44 | ✅ PASS |
| 4 | state_manager_seq004 | get_previous_audit_state, save_current_audit_state + constant | 22 | ~28 | ✅ PASS |
| 5 | prompt_builder_seq005 | build_master_prompt | 50 | **~153** | ❌❌ CRITICAL (function=148 lines) |
| 6 | ai_queries_seq006 | query_gemini, query_deepseek | 22 | ~28 | ✅ PASS |
| 7 | quick_report_seq007 | generate_quick_report | 45 | **~73** | ❌ FAIL (function=67 lines) |
| 8 | orchestrator_seq008 | run_master_audit + constant | 50 | **~95** | ❌ FAIL (function=89 lines) |

**Pass rate: 4/8 (50%)**

---

## 🐛 COMPILER BUGS EXPOSED BY SELF-TEST

### Bug 1: DeepSeek Line Hallucination (CRITICAL)
DeepSeek claimed `run_audit → "estimated_lines": 50` but the function ALONE is 131 lines.
Similarly claimed `build_master_prompt → 50` when it's 148 lines.

**Root cause**: The ether map provides `line_count` per function but DeepSeek ignores it when estimating.

**Fix**: Add explicit `HARD CONSTRAINT` section to prompt:
```
HARD LINE COUNTS FROM AST (not estimates — exact measurements):
- run_audit: 131 lines  ← CANNOT fit in one ≤50 file
- build_master_prompt: 148 lines  ← MUST BE SPLIT FURTHER
```

### Bug 2: No Recursive Decomposition
When a single function exceeds 50 lines, DeepSeek should propose splitting THAT function into sub-functions + a wrapper. Currently it just gives up and lies about the line count.

**Affected functions**:
- `run_audit()` — 131 lines (builds massive DeepSeek prompt with 5 audit sections)
- `build_master_prompt()` — 148 lines (~100 lines is an f-string)
- `update_local_manifest()` — 69 lines
- `generate_quick_report()` — 67 lines
- `run_master_audit()` — 89 lines

**Fix**: Add a pre-filter in the prompt:
```
FUNCTIONS THAT EXCEED 50 LINES (must be decomposed):
{list of functions over 50 with their line counts}
For each, propose SUB-FUNCTIONS that the wrapper calls.
```

### Bug 3: Naming Convention Drift
DeepSeek used `codebase_auditor_constants_seq001_v001.py` for folder_auditor but
`auditor_data_collector_seq001_v001.py` for master_auditor. Two different prefix patterns.

**Fix**: Add target folder name to prompt so DeepSeek knows the namespace:
```
TARGET FOLDER: codebase_auditor/
PREFIX: folder_auditor_ (for folder_auditor.py extraction)
```

### Bug 4: PROMPT_BLOB Not Addressed In Plan
Ether map correctly identified 2 PROMPT_BLOBs in folder_auditor (`~26 line string at L307`, `~25 line string at L333`), but DeepSeek's plan just says "PROMPT_BLOB patterns in run_audit() will be moved to seq006 file but remain intact" — moving a 131-line function to a new file doesn't solve anything.

**Fix**: Prompt should demand explicit prompt blob strategy:
```
For each PROMPT_BLOB, propose ONE of:
a) Extract to a templates/ constant file
b) Build with a function that returns the string
c) Use Jinja/f-string template loaded from file
```

### Bug 5: Single Cluster Problem
Both files show exactly 1 cluster (all functions connected). This means `find_clusters()` returns useless data for GOD_ORCHESTRATOR files — every function is transitively reachable from the God function.

**Fix**: Add "cluster depth" analysis. Instead of connected components (binary yes/no), measure HOW MANY hops each function is from the God function. Functions at distance ≥2 are safe to extract.

---

## 📊 COMPILER SCORECARD

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Ether Map Quality** | 9/10 | Rich data, correct patterns, useful resistance scoring |
| **Call Graph Accuracy** | 10/10 | Every call verified against source AST |
| **Resistance Detection** | 8/10 | Caught GOD_ORCHESTRATOR + PROMPT_BLOB. Missed: f-string PROMPT_BLOBs (JoinedStr) |
| **DeepSeek Grouping Logic** | 7/10 | Groupings make semantic sense, boundaries are reasonable |
| **DeepSeek Line Estimates** | 2/10 | Hallucinated line counts on 10/17 proposed files |
| **Pigeon Compliance** | 3/10 | Only 7/17 proposed files actually ≤50 lines |
| **Recursive Decomposition** | 0/10 | No strategy for functions >50 lines |
| **Prompt Engineering** | 6/10 | Good structure, missing hard constraints |

**Overall: 45/80 (56%) — NEEDS ITERATION**

---

## 🔧 REQUIRED PROMPT FIXES FOR v0.2.0

### 1. Inject HARD LINE COUNTS per function into prompt
```python
# In build_plan_prompt():
oversized = [f for f in em['functions'] if f['line_count'] > 50]
# Add to prompt:
# ⚠️ OVERSIZED FUNCTIONS (>50 lines — MUST decompose):
# - run_audit: 131 lines
# etc.
```

### 2. Demand sub-function decomposition
```
For any function >50 lines, you MUST:
1. Propose sub-functions that the original function calls
2. Each sub-function ≤30 lines
3. Wrapper function ≤20 lines
```

### 3. Fix naming convention enforcement
```
NAMING RULE: [parent_stem]_[description]_seqNNN_vNNN.py
parent_stem = {file_stem}  ← REQUIRED prefix
```

### 4. Add line validation in compiler
```python
# Post-DeepSeek validation:
for cut in plan['cuts']:
    actual = sum(fn['line_count'] for fn in funcs if fn['name'] in cut['contents'])
    if actual > 50:
        flag_for_resubmission(cut)
```

### 5. Add cluster depth instead of binary clustering
Replace `find_clusters()` with `compute_call_depth(graph, god_func)` that returns
`{func_name: distance_from_god}` — functions at distance ≥2 are the easiest extraction targets.

---

## 📂 FILES GENERATED BY THIS TEST

| File | Purpose |
|------|---------|
| `compiler_output/folder_auditor_ether_map.json` | Layer 1 output: 440 lines of AST analysis |
| `compiler_output/master_auditor_ether_map.json` | Layer 1 output: 380 lines of AST analysis |
| `compiler_output/folder_auditor_cut_plan.json` | Layer 2 output: DeepSeek's 9-file proposal |
| `compiler_output/master_auditor_cut_plan.json` | Layer 2 output: DeepSeek's 8-file proposal |

---

## ✅ WHAT WORKED

1. **Full pipeline executed end-to-end** — state_extractor → ether_map → DeepSeek → JSON plan
2. **AST parsing caught everything** — all 19+12 functions, all constants, all call edges
3. **Resistance scoring was accurate** — both files correctly flagged as HUMAN_REVIEW (0.9)
4. **GOD_ORCHESTRATOR pattern detected** — run_audit(7 calls) and run_master_audit(11 calls)
5. **Import tracing found real inbound dependencies** — __init__.py imports both files
6. **PROMPT_BLOB detection found real blobs** — L307/L333 in folder_auditor, L300 in master_auditor
7. **Cost: $0.003** — for full analysis of 1,200 lines across 2 files, with structured JSON plans

## ❌ WHAT NEEDS FIXING

1. DeepSeek lies about line counts → inject actual counts
2. No recursive decomposition → add sub-function proposal requirement
3. Naming convention drift → enforce prefix in prompt
4. PROMPT_BLOB strategy missing → demand explicit extraction approach
5. Single-cluster problem → add call depth analysis
6. No post-validation → add line count checker after DeepSeek response
7. f-string detection → handle `ast.JoinedStr` in PROMPT_BLOB detector
