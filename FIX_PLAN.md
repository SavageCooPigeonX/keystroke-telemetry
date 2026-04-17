# FIX PLAN — deep audit, scoring fix, TDD pivot, unhackable master test

*generated 2026-04-16 from live signal audit + code trace. no vibes. concrete file paths + line numbers + specific edits.*

---

## 0. TL;DR — what's actually broken and in what order to fix it

| # | Problem | Root Cause | Blocks |
|---|---------|------------|--------|
| 1 | **organism health = 96 but fix rate = 12.5%** | score is measured, not validated — gameable | everything downstream |
| 2 | **self_fix writes fixes but never re-verifies** | open-ended loop: scan → write → done (no re-scan) | bugs recur every push |
| 3 | **imports break after file-to-subpackage split** | regex-only rewriter doesn't check `__init__.py` exports | every split introduces 1–5 new NameErrors |
| 4 | **40+ files over 200-line cap on a "hard cap"** | compiler runs manually, not in post-commit hook | compliance never converges |
| 5 | **tq-034 to tq-044 cold for 4 days** | `mark_done()` exists, nothing calls it | intent backlog grows monotonically |
| 6 | **no ground-truth test gates health** | score is self-reported by the same system that wrote the bug | self-referential, corruptible |

**Fix order:** 6 → 1 → 3 → 2 → 4 → 5. You MUST land the unhackable master test first. Without it, every other "fix" is theater.

---

## 1. Organism Health Score — why it lies and how to make it honest

### The current formula
File: [push_snapshot/push_snapshot_health_score_decomposed_seq012_v001.py](src/push_snapshot/push_snapshot_health_score_decomposed_seq012_v001.py)

```
score = 50 (baseline)
  + compliance_pct × 0.25        # +25 max
  - (bugs / modules) × 20        # −20 max
  + size_bonus                   # ±10
  - min(deaths × 0.5, 5)         # −5 max
  + sync_bonus                   # +10 max (stepped)
  + probes_bonus                 # +5 if probed>10
  - heat_penalty                 # −5 if avg_hes>0.6
```

### Why it's 96/100 when the system is clearly broken
- **bugs/modules is 122/630 = 0.19**, so the penalty is only −3.8 pts. a bug on every 5th file barely dents the score.
- **compliance_pct = 49.7%** gives +12.4 pts. half the codebase violates the cap and it's worth a dozen points of health.
- **sync_score = 0.058** gives +3 pts (it's in the `sync>0` stepped bucket). a sync score this low means operator intent and code output have diverged — it should be a *penalty*, not a bonus.
- **probes >10 = +5**. probes cost nothing to create. this is free points.
- **avg_hes currently <0.6**, so no heat penalty. hesitation is averaged across 600+ prompts; a single calm session masks burning modules.

**The score rewards activity, not outcomes.** It cannot distinguish "fixed the bug" from "wrote a patch that introduced 2 new bugs and ran a probe."

### Fix — rebuild the score with veto gates and outcome validation

Replace the current `_compute_health_score` with a two-phase model:

```python
def _compute_health_score(snapshot: dict) -> float:
    # PHASE 1: veto gates. any failure caps the score.
    caps = []
    if snapshot['cycle']['sync_score'] < 0.1:
        caps.append(('sync_too_low', 60))
    if snapshot['ai_rework']['miss_rate'] > 0.20:
        caps.append(('rework_too_high', 60))
    if snapshot['bugs']['chronic_count'] >= 3:
        caps.append(('chronic_bugs', 70))
    if snapshot['modules']['overcap_hard_count'] > 10:
        caps.append(('overcap_epidemic', 65))
    if snapshot['master_test']['passed'] is not True:   # see §6
        caps.append(('master_test_failed', 50))

    # PHASE 2: graded components, but only if no veto fired
    score = 50.0
    score += _compliance_component(snapshot)        # max +20
    score += _outcome_component(snapshot)           # max +15 — fix rate, not fix count
    score += _drift_component(snapshot)             # max +10 — prompt↔code sync
    score -= _staleness_component(snapshot)         # max −10
    score -= _recurrence_component(snapshot)        # max −10 — bugs surviving ≥3 cycles
    score -= _contradiction_component(snapshot)     # max −5 — metric self-consistency

    score = max(0, min(100, score))
    if caps:
        score = min(score, min(cap for _, cap in caps))
    return round(score, 1), caps
```

Key additions:

- **`_outcome_component`**: not `bugs_total`, but `(bugs_closed_last_cycle) / (bugs_open_last_cycle)`. If self_fix closes 0 of 100, health loses 15 pts, not 0.
- **`_recurrence_component`**: penalizes bugs reported in ≥3 consecutive cycles. The 3 chronic bugs (`推w_dp`, `警p_sa`, `脉p_ph`) would remove 10 pts flat until they're gone.
- **`_contradiction_component`**: scans the prompt blocks for numeric contradictions (see §2 — 4 different rework rates). Each contradiction = −1 pt, capped at −5.
- **Master test veto**: if the unhackable master test (§6) doesn't pass, score is capped at 50. The system cannot self-certify as healthy.

**Delete the probe bonus entirely.** Probes are questions, not answers. Rewarding them incentivizes noise.

### Unify the rework rate source
Four blocks report it. They must all read from one canonical file. Proposed:

- Canonical source: `logs/rework_scorecard.json` — single file, schema `{total: N, missed: M, rate: M/N, updated_ts}`
- Every managed block (predictions, hooks, task-context, organism-health) reads this file — not its own slice
- Add a unit test in the master test that asserts all four blocks report the same `rate` value

---

## 2. Why self_fix Doesn't Fix — closing the write→verify loop

### Where the loop breaks
Files in [src/修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc/](src/修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc):
- `scan_*_seq*.py` — 7 scanners, all work, all write to `self_fix_report.json` ✓
- `auto_apply_import_fixes_seq011_v001.py` — applies fixes via `.write_text()` ✓
- `auto_compile_oversized_seq009_v001.py` — triggers pigeon split ✓
- **MISSING: `verify_fixes_seq*.py`** — nothing re-runs the scanners after a fix

### The fix

1. Add a `verify_fixes()` step that runs after every auto-apply:
   ```python
   def verify_fixes(root: Path, before_bugs: set[str], touched_files: list[Path]) -> dict:
       # re-run the SAME scanners only on touched files
       after_bugs = _rescan(root, touched_files)
       closed = before_bugs - after_bugs
       new = after_bugs - before_bugs
       persisted = before_bugs & after_bugs
       return {
           'closed': sorted(closed),
           'new_bugs_introduced': sorted(new),   # regressions
           'persisted': sorted(persisted),        # fix didn't work
           'verified_ts': _now(),
       }
   ```

2. Write result to `logs/self_fix_verification.jsonl`. Feed it into `_outcome_component` of the health score (§1).

3. If `new_bugs_introduced` is non-empty, **roll back the write**. Use a simple `.bak` sidecar:
   ```python
   backup = py.with_suffix('.py.bak')
   shutil.copy(py, backup)
   try:
       py.write_text(new_text, encoding='utf-8')
       if _has_new_regressions(py):
           shutil.copy(backup, py)  # rollback
           raise FixRegression(py)
   finally:
       backup.unlink(missing_ok=True)
   ```

4. Escalate `persisted` bugs to `escalation_engine` instead of re-reporting them every cycle. A persisted bug needs a human or a DeepSeek pass, not another pigeon auto-fix.

---

## 3. Why Imports Break on Every Rewrite — the subpackage blind spot

### The exact bug we just hit this session
- `module_identity_code_seq007_v001.py` (single file) got split into `module_identity_code_seq007_v001/` (directory with 4 sub-files)
- The package `__init__.py` was created but **empty**: no re-exports
- Callers still had `from .module_identity_code_seq007_v001 import _extract_code_skeleton`
- Python resolved the name to the directory, found nothing, raised `ImportError`

This isn't a one-off. It's the structural consequence of how the rename_engine works.

### Where the rewriter fails
File: [pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX/引w_ir_s003_v005_d0403_踪稿析_λFX_replace_exact_module_path_seq003_v001.py](pigeon_compiler/rename_engine/引w_ir_s003_v005_d0403_踪稿析_λFX/引w_ir_s003_v005_d0403_踪稿析_λFX_replace_exact_module_path_seq003_v001.py)

The regex only rewrites module-path tokens. It does not:
- Check that the symbol being imported still exists at the new path
- Add missing symbols to the new `__init__.py`'s `__all__` or re-export list
- Validate the file→package conversion by trying to import

### Fix — three steps, ordered

**Step 1: auto-populate `__init__.py` on decomposition**

When `foo.py` becomes `foo/`, walk the sub-modules, collect all public-ish names (anything defined at module level, including `_`-prefixed helpers used elsewhere), and emit:
```python
# foo/__init__.py — auto-generated by pigeon decomposer
from .foo_wrapper_seq004 import _extract_code_skeleton, build_foo
from .foo_helpers_seq001 import _find_stale_path
__all__ = ['_extract_code_skeleton', 'build_foo', '_find_stale_path']
```

Track this via a manifest in the split plan — the slicer already knows which symbols it moved where.

**Step 2: post-split import validation**

After every split, run:
```python
def _validate_split(target: Path, importers: list[Path]) -> list[ImportError]:
    errors = []
    for imp_file in importers:
        proc = subprocess.run(
            [sys.executable, '-m', 'py_compile', str(imp_file)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            errors.append((imp_file, proc.stderr))
    return errors
```

If any importer fails to compile, roll back the split.

**Step 3: AST-based rewriter instead of regex**

For the longer-term fix, replace `_replace_exact_module_path` with an AST-based rewriter (libcst or ast). The regex cannot distinguish `module_identity_code_seq007_v001` the module from the same string appearing in a comment, docstring, or `__name__ == "__main__"` guard. AST can.

---

## 4. Pigeon Compiler Doesn't Enforce on Commit

### The gap
`py -m pigeon_compiler.runners.run_clean_split_seq010*` is a manual entry point. Nothing wires it into `.git/hooks/post-commit` or `pre-push`.

### Fix

Add `.git/hooks/pre-push` (committed via a bootstrap script since git hooks aren't repo-tracked by default):

```bash
#!/usr/bin/env sh
set -e
py -m pigeon_compiler.runners.run_clean_split_seq010* --enforce || {
    echo "pigeon compiler enforcement failed. fix over-cap files before pushing."
    exit 1
}
py test_all.py
py -m src.master_test   # see §6
```

Add a bootstrap `scripts/install_hooks.py`:
```python
from pathlib import Path
import shutil, stat
src = Path('scripts/hooks/pre-push')
dst = Path('.git/hooks/pre-push')
shutil.copy(src, dst)
dst.chmod(dst.stat().st_mode | stat.S_IEXEC)
```

**Important**: the `--enforce` flag must be new. Currently the compiler is advisory. Add:
```python
# in run_clean_split main
if args.enforce:
    violations = [f for f in files if _tokens(f) > HARD_CAP]
    if violations:
        _split_all(violations)
        remaining = [f for f in violations if _tokens(f) > HARD_CAP]
        if remaining:
            sys.exit(f'could not bring under cap: {remaining}')
```

---

## 5. Test-Based Dev Strategy — intent-snapshots compiled into tests

### The core idea (your words, concretized)

```
operator intent  →  intent_snapshot (deleted words + prompt + unsaid threads)
                    ↓
                    intent_test_compiler
                    ↓
                    tests/generated/test_intent_<hash>.py
                    ↓
                    copilot sees test output, fixes until green
                    ↓
                    master_test asserts:
                      ∀ resolved_intent ∈ backlog: generated_test exists AND passes
```

### Why this closes the loop the current system can't close

Right now when you abandon a prompt, the system stores the deleted words, classifies the state as "abandoned," and routes it into a probe. The probe is never answered, so the intent evaporates. 12 items in the backlog prove this.

If every intent becomes a **test**, it can't evaporate. A failing test is a bug. A passing test is a closed intent. The system becomes grep-able, CI-able, objectively resolvable.

### Architecture — 4 new modules

```
src/tdd_intent/
  intent_snapshotter.py        # captures prompt + deleted_words + rewrites + files_open
  intent_test_compiler.py      # LLM call: intent → pytest test (ONE-TIME per intent)
  intent_test_validator.py     # runs tests, reports pass/fail, feeds health score
  master_test_runner.py        # §6 — the unhackable gate
```

### `intent_snapshotter.py` (compressible, ~60 lines)

Input: a prompt_journal entry. Output: a JSON snapshot with everything an LLM needs to compile a test.

```python
@dataclass
class IntentSnapshot:
    intent_id: str                  # hash of original text
    raw_prompt: str
    completed_thought: str          # from unsaid_recon
    cognitive_state: str
    deleted_words: list[str]
    rewrites: list[dict]
    files_open: list[str]
    module_refs: list[str]          # pigeon names mentioned
    existing_signals: dict          # heat, entropy for mentioned modules
    snapshot_ts: str
```

Store snapshots at `logs/intent_snapshots/{intent_id}.json`. Never delete.

### `intent_test_compiler.py` — the LLM call that mints a test

Given an `IntentSnapshot`, ask the model to produce a pytest module with:
- A docstring restating the intent in plain english
- One or more `test_*` functions, each asserting a *measurable* condition derived from the intent
- Imports restricted to `src/*` and stdlib — no network, no subprocess
- A `SKIP_REASON` constant set to a non-empty string if the test cannot be mechanically verified (so it's tracked but not run)

Example compilation, for tq-034 ("also seach online. coo coo zap"):

```python
# tests/generated/test_intent_tq034_search_online.py
"""Intent: 'also seach online. coo coo zap' — operator wants web search capability.
   Cognitive state: abandoned. Conf: 1.00.
   Completion: operator wanted a web-search-enabled research path for telemetry topics.
"""
SKIP_REASON = "no web_search module exists yet — test will flip to active when it does"

def test_research_lab_has_web_search_capability():
    from src import research_lab
    assert hasattr(research_lab, 'web_search'), "research_lab must expose web_search()"
    # must accept a query and return a list of result dicts
    result = research_lab.web_search("test", limit=1)
    assert isinstance(result, list)
```

The test is **failing until the capability exists**. The intent is **tracked as a failing test**, not a cold backlog item.

### `intent_test_validator.py` — runs tests, feeds health

```python
def validate_all_intents(root: Path) -> dict:
    generated = root / 'tests' / 'generated'
    results = {}
    for test_file in generated.glob('test_intent_*.py'):
        rc = _run_pytest(test_file)
        results[test_file.stem] = {'passed': rc == 0, 'skipped': _is_skipped(test_file)}
    return results
```

Feed this into `_outcome_component` of the health score. Now intent resolution is a measurable fraction.

### Flip `mark_done()` from manual to automatic

When an intent test flips from FAIL→PASS in a push cycle, `intent_test_validator` calls `task_queue.mark_done(task_id, commit=git_head, verification='test_passed')` automatically. The cold-backlog problem dies.

---

## 6. The Master Unhackable Test

### Constraint you specified
> must complete before organism health passes · can't be hacked by llm

### What "unhackable by LLM" means mechanically

The LLM must not be able to:
1. Modify the test file to weaken its assertions
2. Modify the inputs it reads to make them satisfy the assertions
3. Delete the test file
4. Lie about having run it (fake a passing log)

### Implementation — `src/master_test.py`

This is the one file that should be locked down. Four anti-hack techniques:

**1. Content hash self-verification**
```python
# master_test.py
import hashlib, sys
_EXPECTED_SHA = "<computed at install time, stored in .master_test_sha file>"
_this = Path(__file__).read_bytes()
if hashlib.sha256(_this).hexdigest() != _EXPECTED_SHA:
    sys.exit("master_test.py has been modified. integrity failure.")
```
Combined with a pre-push hook that compares `.master_test_sha` to the committed version. If the LLM edits `master_test.py`, the hash changes, the test exits 1, the push is blocked.

**2. External ground-truth inputs**
All assertions read from files *outside* `src/` that the LLM is instructed (via copilot-instructions.md) to treat as read-only:
- `pigeon_registry.json` — module registry (touched by compiler, not by LLM directly)
- `logs/self_fix_verification.jsonl` — append-only, scanner-written
- `intent_backlog_resolutions.json` — append-only
- Output of `git log --since=<last_push>` — from git, not a file

If the LLM edits these, the self_fix scanners catch it in the next cycle (they re-derive the data from AST + commits).

**3. Assertion set** (these are the gates — all must pass)
```python
def test_no_over_cap_hard_violations():
    from src.modules import count_over_hard_cap
    assert count_over_hard_cap() == 0, "files exceed 200-line hard cap"

def test_rework_rate_consistent_across_blocks():
    rates = _extract_rework_rates_from_copilot_instructions()
    # all managed blocks must report the same rate
    assert len(set(rates.values())) == 1, f"contradiction: {rates}"

def test_self_fix_closes_fixes_it_reports():
    verif = _read_jsonl('logs/self_fix_verification.jsonl', last_n=10)
    avg_close_rate = sum(v['closed_count']/max(v['touched_count'],1) for v in verif) / len(verif)
    assert avg_close_rate >= 0.5, f"self_fix close rate {avg_close_rate:.0%} < 50%"

def test_imports_resolve_after_recent_splits():
    recent_splits = _git_diff_last_push(filter='pigeon_compiler')
    for split in recent_splits:
        assert _compiles(split), f"{split} fails py_compile after split"

def test_intent_backlog_has_generated_tests():
    open_intents = [t for t in _load_tasks() if t['status'] == 'pending']
    for intent in open_intents:
        test_path = Path(f"tests/generated/test_intent_{intent['id']}.py")
        assert test_path.exists(), f"intent {intent['id']} has no generated test"

def test_master_test_not_tampered_with():
    # already checked at import; this re-checks at runtime in case of in-memory monkeypatch
    current = Path(__file__).read_bytes()
    assert hashlib.sha256(current).hexdigest() == _EXPECTED_SHA

def test_health_score_below_70_if_any_above_fail():
    # this test is the anchor — if any other test fails, health MUST reflect it
    # it runs last, reads the run log, and enforces the veto
    from logs.master_run import last_run
    if last_run['failures']:
        assert last_run['health_score'] <= 70, \
            "health score didn't drop despite master test failures (score is lying)"
```

**4. Run signature (anti-lie)**
```python
if __name__ == '__main__':
    rc = pytest.main([__file__, '-v'])
    # write a signed run record
    record = {
        'ts': _now(),
        'rc': rc,
        'git_sha': _git_head(),
        'test_sha': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    sig = hmac.new(_HMAC_KEY, json.dumps(record, sort_keys=True).encode(), 'sha256').hexdigest()
    record['sig'] = sig
    (Path('logs/master_run.json')).write_text(json.dumps(record, indent=2))
    sys.exit(rc)
```
`_HMAC_KEY` is generated at first run and stored in `.master_key` (gitignored). The LLM can't forge a passing log because it doesn't have the key.

### Wiring into the pipeline

```
pre-push hook:
  1. run pigeon compiler --enforce  (fix over-cap)
  2. run self_fix with verify loop  (close bugs, roll back regressions)
  3. run intent_test_validator      (flip task statuses)
  4. run master_test                (the gate)
  5. recompute health score         (now including master_test.passed)
  6. if health < threshold OR master_test.rc != 0: BLOCK PUSH
```

Only after all of that does a push go through. The score cannot be 96 while the master test fails.

---

## 7. Unclosed Loops Map

Every observability loop in this system that writes signals but doesn't consume them. **These are the structural leaks.**

| Loop | Writer | Consumer (expected) | Consumer (actual) | Status |
|------|--------|---------------------|-------------------|--------|
| prompt_journal → cognitive state | logger_seq003 | dynamic_prompt | dynamic_prompt (partial) | ⚠️ drift_watcher reads but never acts |
| deleted_words → unsaid_recon | unsaid_recon_seq024 | probe_generator | probe_generator → dashboard only | ❌ probes never answered |
| self_fix_report → verification | self_fix_seq013 | (nothing) | — | ❌ open-ended |
| pigeon split plan → import update | rename_engine | import_rewriter | import_rewriter (regex-only) | ❌ misses subpackages |
| task_queue pending → done | task_writer | mark_done caller | — | ❌ nothing calls mark_done |
| intent_backlog_resolutions | intent_reconstructor | task_queue | task_queue (partial — manual) | ⚠️ drifts to cold |
| health snapshot → prompt blocks | push_snapshot | copilot-instructions writers | writers (multiple, contradicting) | ⚠️ see rework-rate divergence |
| rework_scorecard → model tuning | rework_detector | mutation_scorer | mutation_scorer (34 sections, all neutral) | ⚠️ low signal |
| cognitive_reactor → patches | reactor_core | ? | self_fix_runner (1/529 accepted) | ❌ 0% acceptance |
| module_identity.memory → probes | module_identity | probes | probes (yes, working) | ✅ only loop that closes |
| file_consciousness → dashboard | file_consciousness | vitals_renderer | vitals_renderer | ✅ closed (since today) |
| entropy shed → entropy map | inline shed blocks | entropy_parser | entropy_parser (9% fire rate) | ⚠️ under-fed |
| push_narrative → backstory | push_narrative | module_identity.backstory | backstory (yes) | ✅ closed |

**Three loops are closed. Ten are leaking. The system's apparent intelligence is propped up by the three that work.**

### The fix (per loop)

1. `self_fix` → add `verify_fixes()` as §2.
2. `task_queue` → auto-call `mark_done()` from `intent_test_validator` as §5.
3. `cognitive_reactor` → either accept more patches or stop writing. Current 0% acceptance is pure noise. Require the reactor to gate patches through `verify_fixes()` before they're considered applied.
4. `rework_scorecard` → unify the source (see §1) so consumers don't contradict.
5. `unsaid_recon` → route probes into `intent_test_compiler` instead of dashboard. Turn every probe into a failing test.
6. `drift_watcher` → wire its output into the health veto set (§1).

---

## 8. Intent Synthesis — what you actually want (from the cold backlog)

Pulled from `task_queue.json` for `tq-034` through `tq-044`, cross-referenced against deleted-words and recent prompts:

| Task | Canonical intent | Why it's cold | Test-form intent |
|------|------------------|---------------|------------------|
| tq-034 | web search capability in research_lab | no module implements it | `test_research_lab_has_web_search` |
| tq-035 | novel-info-only reports (no repetition) | report generator doesn't dedupe against history | `test_report_has_no_repeated_claims_vs_prior` |
| tq-036 | verify the learning loop actually works | no end-to-end test exists | `test_mutation_scorer_distinguishes_good_from_bad` |
| tq-037 | godelean anchor research direction | pure research, not mechanical | SKIP_REASON set, tracked only |
| tq-038 | can "christ as king" be stripped of roleplay and still carry information | pure research | SKIP_REASON set |
| tq-039 | "didnt we already build out questions??" — redundancy anxiety | operator worried about duplication | `test_probe_generator_deduplicates_against_history` |
| tq-040 | drift assessment on push + "missing context" truth gate | no drift gate at push time | `test_push_fails_if_drift_score_high` |
| tq-041 | "its not simming my intent properly why?" | intent simulation is weak | `test_intent_sim_matches_last_3_prompts_at_80pct` |
| tq-042 | semantic layer inspection per file | per-file semantic view exists partially | `test_every_module_has_semantic_layer_entry` |
| tq-043 | "why is entropy still staying in the 0.80s while you edit" | entropy doesn't shed on edit | `test_entropy_decreases_after_file_touch` |
| tq-044 | (recent — need to read) | — | — |

**Meta-intent across the backlog**: you want the system to *prove to itself* that it's working. You keep asking "does it actually work." The cold-backlog is a unified signal that the answer is "nobody checks." The master test + intent-tests system (§5, §6) IS the answer to this meta-intent.

### Recent prompt signal (from prompt_telemetry)
- `abandoned` dominant (66%) → you back off when responses feel fake
- `systen is feeling pretty` deleted → you were going to say the system feels pretty broken / pretty alive — both interpretations point to wanting the voice/narrative loop amplified
- `hes=0.443` → you hesitate on every 2nd token → the system isn't reading your intent well enough to commit

The test-based pipeline (§5) directly addresses abandonment: when there's a failing test, the system can't pretend the intent was handled. It has to either fix or explicitly skip with a reason.

---

## 9. Concrete next 10 commits (ordered)

1. Add `src/master_test.py` skeleton + `.master_test_sha` + hmac key generator
2. Unify rework_rate: create `logs/rework_scorecard.json` + update 4 block writers to read from it
3. Rebuild `_compute_health_score` with veto gates (§1)
4. Add `verify_fixes()` + rollback-on-regression to self_fix (§2)
5. Auto-populate `__init__.py` on pigeon decomposition (§3 step 1)
6. Add post-split `py_compile` validation + rollback (§3 step 2)
7. Add `.git/hooks/pre-push` installer script + wire compiler + master_test (§4)
8. Scaffold `src/tdd_intent/` with snapshotter, compiler, validator (§5)
9. Auto-close `task_queue` entries when their generated test flips to PASS (§5)
10. Generate failing tests for tq-034, tq-035, tq-036, tq-039, tq-040, tq-041, tq-042, tq-043 (§8)

After commit 10: fix rate becomes *measurable* (test pass/fail counts). Health score becomes *honest* (veto gates + master test). Intent backlog stops growing monotonically (auto-close on green test). Imports stop breaking on split (validated + rolled back). The compiler actually runs on push.

**None of these are comedy. Every file path above is real and was read to produce this plan.**

---

## 10. What to decide before I start coding

1. Do you want the master test to **block push** or just **warn**? (recommend block.)
2. Do you want the intent_test_compiler to use **Gemini Flash** (fast, you already use it) or **DeepSeek** (deeper but slow)?
3. Do you want the health score veto to cap at **50, 60, or 70** on master-test failure? (recommend 50 — it should be visibly broken.)
4. Do you want me to **rebase away the intent_backlog** before these changes or **keep it and watch it drain** as tests flip green? (recommend keep — it's the best possible demo.)

answer those and i can start on commits 1-3 in the next turn.
