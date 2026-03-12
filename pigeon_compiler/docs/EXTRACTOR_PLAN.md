# PIGEON CODE EXTRACTOR — Architecture Plan
## The Automated Code Compliance Engine
### Version: 0.1.0 (Planning) | Date: 2026-02-27

---

## THE IDEA

The current `codebase_auditor/` **reports** violations. It finds oversized files, bad naming, missing manifests — then generates a markdown report and hopes a human fixes it.

The **Extractor** doesn't report. It **operates**. It reads a non-compliant file, extracts every function/class/test into individual compliant files, stages them in a plugin folder, and gives the operator a one-command delete/hardlock to swap the old file for the new split.

**Current auditor:** "This file is 567 lines. That's bad."  
**Extractor:** "This file is 567 lines. Here are 14 compliant files. Type `confirm` to replace."

---

## WHY THIS IS WORTH MILLIONS

1. **Every enterprise has compliance rules.** Pigeon Code is ours. But the pattern — max file size, naming conventions, manifest tracking, single responsibility — is universal. ESLint reports. Prettier formats. **Nothing extracts and restructures.**

2. **AI coding agents generate bloated files.** Copilot, Cursor, Claude — they all write 300-line functions. The Extractor is the cleanup layer that runs AFTER the AI generates code. It's the **linter for the AI age**.

3. **SaaS model:** Free tier scans + reports (current auditor). Paid tier extracts + stages + applies. Enterprise tier runs as CI/CD gate — reject PRs that violate compliance.

4. **Defensible moat:** The Hush shard architecture (single-row, versioned columns) proves this pattern works at production scale. The Extractor is the generalized version.

---

## ARCHITECTURE

### Phase 1: Core Extract Engine

```
EXTRACTOR PIPELINE
==================

1. SCAN       → Read target file, build AST
2. ANALYZE    → Identify functions, classes, tests, imports, dependencies
3. PLAN       → Generate split plan (which functions go where)
4. EXTRACT    → Write individual files to staging folder
5. VERIFY     → Run imports check, ensure no circular deps
6. STAGE      → Present diff to operator
7. APPLY      → Replace original file + update manifest
8. HARDLOCK   → Mark original as "extracted" (prevent re-bloat)
```

### Phase 2: Plugin Architecture

```
codebase_auditor/
├── __init__.py
├── extractor/
│   ├── __init__.py
│   ├── ast_parser_seq001_v001.py      # Python AST parsing (~40 lines)
│   ├── dependency_map_seq002_v001.py  # Import/reference graph (~45 lines)
│   ├── split_planner_seq003_v001.py   # Decide how to split (~40 lines)
│   ├── file_writer_seq004_v001.py     # Write extracted files (~35 lines)
│   ├── import_fixer_seq005_v001.py    # Fix imports in new files (~40 lines)
│   ├── manifest_updater_seq006_v001.py # Update MANIFEST.md (~30 lines)
│   ├── staging_seq007_v001.py         # Stage changes for review (~35 lines)
│   ├── hardlock_seq008_v001.py        # Prevent re-bloat (~25 lines)
│   └── MANIFEST.md
├── folder_auditor.py    # Existing — calls extractor when violations found
├── master_auditor.py    # Existing — orchestrates
└── MANIFEST.md
```

---

## CORE DATA STRUCTURES

### 1. FileAnalysis — What the AST parser produces

```python
@dataclass
class FileAnalysis:
    path: Path
    total_lines: int
    
    # Extracted components
    functions: list[FunctionDef]    # name, start_line, end_line, decorators, docstring
    classes: list[ClassDef]         # name, start_line, end_line, methods, bases
    top_level_code: list[CodeBlock] # assignments, constants, module-level logic
    
    # Dependency graph
    imports: list[ImportDef]        # module, names, is_relative
    internal_refs: dict[str, list]  # function_name -> [functions it calls]
    external_refs: dict[str, list]  # function_name -> [modules it imports from]
    
    # Test detection
    test_classes: list[ClassDef]    # Classes inheriting from TestCase or using pytest
    test_functions: list[FunctionDef]  # Functions starting with test_
    
    # Compliance
    pigeon_violations: list[str]
    is_compliant: bool
```

### 2. SplitPlan — How the planner decides to split

```python
@dataclass
class SplitPlan:
    source_file: Path
    target_folder: Path
    
    # Planned new files
    new_files: list[PlannedFile]  # Each ≤50 lines
    
    # Each PlannedFile:
    #   filename: str (semantic_seqXXX_vXXX.py)
    #   functions: list[str]  — which functions go in this file
    #   estimated_lines: int
    #   imports_needed: list[str]
    #   exports: list[str]
    
    # Shared utilities file (if needed)
    shared_utils: PlannedFile | None
    
    # Updated __init__.py exports
    init_exports: list[str]
    
    # Manifest update
    manifest_additions: list[dict]
```

### 3. StagedChange — What gets presented to the operator

```python
@dataclass
class StagedChange:
    plan: SplitPlan
    staged_files: dict[str, str]   # filename -> content
    diff_summary: str              # Human-readable diff
    
    # Verification results
    imports_valid: bool
    no_circular_deps: bool
    line_counts_compliant: bool
    tests_pass: bool               # If test file, run pytest on staged version
    
    # Actions
    def confirm(self) -> ApplyResult: ...
    def reject(self) -> None: ...
    def modify(self, file: str, content: str) -> None: ...
```

---

## SPLITTING ALGORITHM

### The Key Innovation: Dependency-Aware Grouping

Naive approach: one function per file. **Problem:** 50 functions = 50 files = import hell.

Smart approach: **Group functions by dependency clusters.**

```
Algorithm: CLUSTER_SPLIT
========================

1. Build call graph: function A calls B, C; function D calls E
2. Find connected components (A-B-C are a cluster, D-E are a cluster)  
3. For each cluster:
   a. If cluster ≤ 50 lines → one file
   b. If cluster > 50 lines → split at weakest dependency edge
4. Assign semantic names based on function purposes
5. Generate shared_utils.py for truly shared helpers
6. Generate __init__.py that re-exports all public functions
```

### Naming Convention

```
Original: master_auditor.py (567 lines)

Extracted:
├── audit_collector_seq001_v001.py     # collect_manifests, collect_audit_results
├── audit_pigeon_seq002_v001.py        # check_pigeon_violations
├── audit_db_stats_seq003_v001.py      # get_db_stats
├── audit_prompt_seq004_v001.py        # build_master_prompt  
├── audit_cache_seq005_v001.py         # get/save_previous_audit_state
├── audit_ai_query_seq006_v001.py      # query_gemini, query_deepseek
├── audit_report_seq007_v001.py        # generate_quick_report
├── audit_runner_seq008_v001.py        # run_master_audit (orchestrator, <50 lines)
└── __init__.py                        # re-exports run_master_audit, audit_folder, etc.
```

The sequence numbers (seq001, seq002) encode **execution order** — the order functions are called in the pipeline. This makes the codebase self-documenting.

---

## HARDLOCK SYSTEM

Once a file is extracted, we need to prevent it from re-bloating (AI agents LOVE writing big files).

### .pigeon_lock.json

```json
{
  "codebase_auditor/master_auditor.py": {
    "status": "extracted",
    "extracted_to": "codebase_auditor/",
    "extracted_at": "2026-02-27T12:00:00Z",
    "max_lines": 50,
    "files_created": [
      "audit_collector_seq001_v001.py",
      "audit_pigeon_seq002_v001.py"
    ],
    "checksum": "sha256:abc123..."
  }
}
```

### How hardlock works:
1. Pre-commit hook checks `.pigeon_lock.json`
2. If any locked file exceeds its `max_lines` → **block commit**
3. If any locked file is modified → require re-extraction or explicit unlock
4. CI/CD gate rejects PRs that violate locks

---

## INTERFACE

### CLI

```bash
# Scan a file — show what would be extracted
python -m codebase_auditor.extractor scan codebase_auditor/master_auditor.py

# Plan extraction — show split plan without executing
python -m codebase_auditor.extractor plan codebase_auditor/master_auditor.py

# Extract — stage files for review
python -m codebase_auditor.extractor extract codebase_auditor/master_auditor.py

# Apply — replace original with extracted files
python -m codebase_auditor.extractor apply codebase_auditor/master_auditor.py

# Hardlock — prevent re-bloat
python -m codebase_auditor.extractor lock codebase_auditor/master_auditor.py

# Scan entire project
python -m codebase_auditor.extractor scan-all --threshold 50
```

### Hush Integration (Slash Commands)

```
/extract master_auditor.py     → Scan + plan + stage
/extract --apply               → Apply staged changes
/extract --lock                → Lock after apply
/pigeon-check                  → Quick compliance report
```

### Python API

```python
from codebase_auditor.extractor import scan_file, plan_split, extract_file

# Scan
analysis = scan_file("codebase_auditor/master_auditor.py")
print(f"Functions: {len(analysis.functions)}")
print(f"Violations: {analysis.pigeon_violations}")

# Plan
plan = plan_split(analysis)
for f in plan.new_files:
    print(f"  {f.filename} ({f.estimated_lines} lines)")

# Extract + stage
staged = extract_file(analysis, plan)
if staged.imports_valid and staged.no_circular_deps:
    staged.confirm()  # Apply changes
```

---

## MONETIZATION PATH

### Tier 1: Open Source Scanner (Free)
- `scan` command — reports violations
- Current `folder_auditor.py` functionality
- GitHub Action that comments on PRs

### Tier 2: Extractor Pro ($29/mo per repo)
- `plan` + `extract` + `apply` commands
- Dependency-aware splitting
- Manifest auto-generation
- Hardlock system

### Tier 3: Enterprise ($299/mo per org)
- CI/CD gate integration (block non-compliant PRs)
- Custom compliance rules (not just Pigeon Code)
- Team dashboards — compliance score per developer
- Auto-fix mode — extract on commit without staging
- Slack/Teams notifications on violations

### Tier 4: AI Agent Layer ($999/mo)
- Runs as a persistent agent alongside Copilot/Cursor
- Intercepts AI-generated code BEFORE it hits disk
- Real-time compliance enforcement
- Learns team patterns and suggests better splits

---

## IMPLEMENTATION ORDER

### Sprint 1 (Week 1): Core AST Parser + Dependency Map
- `ast_parser_seq001_v001.py` — Parse Python file → FileAnalysis
- `dependency_map_seq002_v001.py` — Build import graph + call graph
- Test on `master_auditor.py` (567 lines) and `folder_auditor.py` (633 lines)

### Sprint 2 (Week 2): Split Planner + File Writer
- `split_planner_seq003_v001.py` — Cluster algorithm → SplitPlan
- `file_writer_seq004_v001.py` — Write staged files
- `import_fixer_seq005_v001.py` — Fix cross-imports in new files

### Sprint 3 (Week 3): Staging + Apply + Hardlock
- `staging_seq007_v001.py` — Present diff, confirm/reject
- `manifest_updater_seq006_v001.py` — Update MANIFEST.md
- `hardlock_seq008_v001.py` — .pigeon_lock.json + pre-commit hook

### Sprint 4 (Week 4): Integration + Polish
- CLI entry point (`__main__.py`)
- Hush slash command integration
- Self-extract: use Extractor to split the Extractor files
- Dog-food on entire LinkRouter.ai codebase

### Sprint 5+ (Month 2): SaaS
- GitHub App / Action
- Web dashboard
- Stripe billing
- Custom rule engine (not just Pigeon Code)

---

## SELF-EXTRACTION TEST

The ultimate validation: **use the Extractor on itself**.

Current targets in our own codebase:
| File | Lines | Functions | Status |
|------|-------|-----------|--------|
| `codebase_auditor/folder_auditor.py` | 633 | ~20 | 🔴 12.7x over limit |
| `codebase_auditor/master_auditor.py` | 567 | ~15 | 🔴 11.3x over limit |
| `tests/test_hush_diagnostic.py` | 2,157 | ~113 | 🔴 43x over limit |
| `tests/test_live_api.py` | 540 | ~20 | 🔴 10.8x over limit |

After extraction:
- `folder_auditor.py` → ~14 files, each ≤50 lines
- `master_auditor.py` → ~12 files, each ≤50 lines
- `test_hush_diagnostic.py` → ~22 test module files
- **All compliant. Zero regressions. Same public API.**

---

## COMPETITIVE LANDSCAPE

| Tool | What it does | Gap |
|------|-------------|-----|
| ESLint/Pylint | Reports violations | Doesn't fix structure |
| Prettier/Black | Formats code | Doesn't restructure |
| SonarQube | Enterprise quality gates | Reports, doesn't extract |
| Sourcery | AI refactoring suggestions | Suggests, doesn't execute |
| **Pigeon Extractor** | **Extracts + restructures + locks** | **THE GAP** |

Nobody automates the **structural refactoring** step. They all stop at "here's what's wrong." We go to "here's the fix, applied."

---

## TECHNICAL RISKS

1. **Circular dependencies after split** — Mitigated by dependency graph analysis before splitting
2. **Test files that depend on execution order** — Mitigated by preserving class structure in test splits
3. **Dynamic imports / getattr patterns** — AST can't catch these. Handle via manual override list
4. **Decorator magic (Flask routes, pytest fixtures)** — Special handling for known decorator patterns
5. **Large files with deeply entangled logic** — May need human guidance for optimal split points

---

## FIRST TARGET

Extract `codebase_auditor/master_auditor.py` (567 lines → ~12 files).

This is perfect because:
- It's OUR code, in OUR auditor module
- It's self-contained (CLI tool, no Flask routes)
- Success immediately improves our own compliance
- Proves the concept on a real, complex file
