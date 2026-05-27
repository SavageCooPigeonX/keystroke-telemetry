"""intent_orchestrator_seq001_v001.py — Self-rewriting code orchestrator.

The loop (grader-as-orchestrator):

  intent_job (from prompt history / file_sim.run_sim)
    │
    ├─► scaffold_test()       — operator/copilot/LLM writes test for intent
    │
    ├─► round 0..N:
    │     ├─► rotate_model()  — deepseek ↔ qwen for weight diversification
    │     ├─► rewrite()       — model produces candidate function body
    │     ├─► sandbox_run()   — exec candidate in-memory + run tests
    │     ├─► grade()         — tests_passed × self_score_delta × context_delta
    │     └─► plateau?        — escalate or converge
    │
    └─► commit_via_pigeon()   — atomic version bump + import rewrite
          │
          └─► compression_check — if file over hard cap, trigger split

Defaults to dry_run=True. Real mutations require --apply.

Inputs:
  - logs/intent_jobs.jsonl      (produced by file_sim.run_sim)
  - logs/intent_matrix.json     (numeric matrix)
  - logs/prompt_journal.jsonl   (intent reconstruction source)

Outputs:
  - logs/orchestration_log.jsonl   (every attempt, every grade)
  - logs/rewrite_attempts/*.py     (candidate files, never committed in dry-run)
  - logs/intent_backlog_latest.json  (escalated jobs for operator)
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).parent.parent
LOGS = ROOT / 'logs'
ATTEMPTS_DIR = LOGS / 'rewrite_attempts'
ORCH_LOG = LOGS / 'orchestration_log.jsonl'
INTENT_JOBS = LOGS / 'intent_jobs.jsonl'
INTENT_BACKLOG = LOGS / 'intent_backlog_latest.json'

MAX_ROUNDS = 5
ACCEPT_THRESHOLD = 0.65
PLATEAU_DELTA = 0.05  # if 3 consecutive rounds within this grade delta → plateau


# ───────────────────────── data ─────────────────────────

@dataclass
class IntentJob:
    """A unit of self-rewriting work."""
    intent_text: str
    target_file: str              # file stem (e.g. "file_sim")
    target_function: Optional[str] = None  # None → whole-file rewrite (discouraged)
    reason: str = ""              # why this rewrite is needed (from grader/sim)
    current_grade: float = 0.0    # baseline grade before any rewrite
    intent_code: str = "OT"       # FX, RF, FT, etc.
    test_code: Optional[str] = None  # pytest-style test source (string)
    source_job: Optional[dict] = None  # original intent_jobs.jsonl row

    @classmethod
    def from_sim_job(cls, sim_job: dict) -> list["IntentJob"]:
        """Expand a sim_job (which has top_files + grades) into per-file jobs."""
        out = []
        grades = sim_job.get('grades', {})
        for file_stem, grade in grades.items():
            # Only rewrite files the sim thinks need changing
            if grade > 0.1:  # needs_change + confidence > 0.1
                out.append(cls(
                    intent_text=sim_job.get('intent_text', ''),
                    target_file=file_stem,
                    reason=f"sim grade {grade:+.2f}",
                    current_grade=float(grade),
                    source_job=sim_job,
                ))
        return out


@dataclass
class RewriteAttempt:
    round_n: int
    model: str
    candidate_source: str         # full function body as string (or whole file)
    tests_passed: bool
    test_output: str              # truncated stdout/stderr
    self_score_delta: float       # change vs baseline (higher = better)
    context_size_delta: int       # token delta (negative = more compact = better)
    final_grade: float            # combined score in [-1, 1]
    error: Optional[str] = None
    ts: str = ""


# ───────────────────────── model clients ─────────────────────────

class ModelClient:
    """Abstract LLM client. Subclasses call actual APIs."""
    name = "abstract"

    def rewrite_function(self, *, intent: str, file_stem: str,
                         current_source: str, test_code: Optional[str],
                         prev_attempts: list[RewriteAttempt]) -> str:
        raise NotImplementedError

    def grade(self, *, intent: str, candidate: str, test_output: str) -> tuple[float, str]:
        """Returns (grade in [-1, 1], one-line reason)."""
        raise NotImplementedError


class DryRunClient(ModelClient):
    """Returns the source unchanged, fake-grades based on length.
    Use this to test the orchestrator flow without spending API credits.
    """
    name = "dryrun"

    def rewrite_function(self, *, intent, file_stem, current_source, test_code, prev_attempts):
        # In dry-run, pretend to "improve" by stripping trailing whitespace
        return '\n'.join(line.rstrip() for line in current_source.splitlines())

    def grade(self, *, intent, candidate, test_output):
        if 'PASS' in test_output:
            return 0.75, "dry-run pass"
        return -0.2, "dry-run fail"


class DeepseekClient(ModelClient):
    name = "deepseek"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _call(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        import urllib.request
        body = json.dumps({
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': 0.2,
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://api.deepseek.com/chat/completions',
            data=body,
            headers={'Content-Type': 'application/json',
                     'Authorization': f'Bearer {self.api_key}'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f'  [deepseek] failed: {e}')
            return None

    def rewrite_function(self, *, intent, file_stem, current_source, test_code, prev_attempts):
        prev_summary = ""
        if prev_attempts:
            prev_summary = "\n\nPrevious attempts failed. Do not repeat these patterns:\n"
            for a in prev_attempts[-2:]:
                prev_summary += f"- {a.model} attempt scored {a.final_grade:.2f}: {a.error or 'tests failed'}\n"

        prompt = f"""Rewrite this Python code to satisfy the operator intent.

INTENT: {intent}

FILE: {file_stem}
CURRENT SOURCE:
```python
{current_source}
```

TEST THAT MUST PASS:
```python
{test_code or "# no test provided — write defensive code that preserves public API"}
```
{prev_summary}

RULES:
- Return ONLY the rewritten Python code (no markdown, no explanation)
- Preserve all public function signatures
- Keep imports minimal and necessary
- Prefer clarity over cleverness
- Aim for FEWER lines than original (context-efficiency objective)

OUTPUT:"""
        raw = self._call(prompt, max_tokens=3000)
        if not raw:
            return current_source
        # Strip markdown fences if present
        raw = raw.strip()
        if raw.startswith('```'):
            lines = raw.splitlines()
            raw = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
        return raw

    def grade(self, *, intent, candidate, test_output):
        prompt = f"""Grade this code rewrite. JSON only.

INTENT: {intent}

CANDIDATE (first 80 lines):
{chr(10).join(candidate.splitlines()[:80])}

TEST OUTPUT:
{test_output[:1000]}

Respond:
{{"grade": -1.0 to 1.0, "reason": "one sentence"}}

grade > 0.7 = strong rewrite, 0.3-0.7 = acceptable, < 0 = worse than original"""
        raw = self._call(prompt, max_tokens=200)
        if not raw:
            return 0.0, "grader unavailable"
        try:
            start = raw.find('{')
            end = raw.rfind('}') + 1
            parsed = json.loads(raw[start:end])
            return float(parsed.get('grade', 0)), str(parsed.get('reason', ''))[:200]
        except Exception:
            return 0.0, f"parse fail: {raw[:80]}"


class QwenClient(ModelClient):
    """Qwen via DashScope / compatible endpoint. Used for diversification.

    If QWEN_API_KEY not set, falls back to Deepseek with slightly different prompt
    so the adversarial-grading still operates on two distinct prompts.
    """
    name = "qwen"

    def __init__(self, api_key: str, fallback: Optional[ModelClient] = None):
        self.api_key = api_key
        self.fallback = fallback

    def _call(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        if not self.api_key:
            return None
        import urllib.request
        # Qwen OpenAI-compatible endpoint (DashScope)
        body = json.dumps({
            'model': 'qwen-plus',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': 0.4,  # higher — divergence from deepseek
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions',
            data=body,
            headers={'Content-Type': 'application/json',
                     'Authorization': f'Bearer {self.api_key}'},
            method='POST',
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data['choices'][0]['message']['content']
        except Exception as e:
            print(f'  [qwen] failed: {e}')
            return None

    def rewrite_function(self, *, intent, file_stem, current_source, test_code, prev_attempts):
        if not self.api_key and self.fallback:
            # fallback with a diversifying framing prompt
            alt_intent = f"[divergent perspective] {intent}"
            return self.fallback.rewrite_function(
                intent=alt_intent, file_stem=file_stem,
                current_source=current_source, test_code=test_code,
                prev_attempts=prev_attempts)
        # Same prompt skeleton as Deepseek but framed for Qwen's preferred style
        prompt = f"""# Task
Refactor Python code to satisfy operator intent. Return only code.

## Intent
{intent}

## Current ({file_stem})
```python
{current_source}
```

## Required Test
```python
{test_code or "# preserve public API"}
```

## Rules
1. Pure Python output — no prose
2. Public signatures unchanged
3. Shorter than original when possible
"""
        raw = self._call(prompt, max_tokens=3000)
        if not raw and self.fallback:
            return self.fallback.rewrite_function(
                intent=intent, file_stem=file_stem,
                current_source=current_source, test_code=test_code,
                prev_attempts=prev_attempts)
        if not raw:
            return current_source
        raw = raw.strip()
        if raw.startswith('```'):
            lines = raw.splitlines()
            raw = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
        return raw

    def grade(self, *, intent, candidate, test_output):
        # Qwen grades Deepseek's output and vice versa → adversarial
        if self.fallback:
            # If we don't have qwen key, reuse deepseek grader — not ideal
            return self.fallback.grade(intent=intent, candidate=candidate, test_output=test_output)
        prompt = f"""Grade this code rewrite (JSON only):

INTENT: {intent}
CANDIDATE (first 80 lines):
{chr(10).join(candidate.splitlines()[:80])}

TEST OUTPUT: {test_output[:800]}

{{"grade": float in [-1,1], "reason": "one line"}}"""
        raw = self._call(prompt, max_tokens=200)
        if not raw:
            return 0.0, "qwen grader unavailable"
        try:
            s, e = raw.find('{'), raw.rfind('}') + 1
            p = json.loads(raw[s:e])
            return float(p.get('grade', 0)), str(p.get('reason', ''))[:200]
        except Exception:
            return 0.0, "parse fail"


# ───────────────────────── key loader ─────────────────────────

def _load_key(name: str) -> str:
    v = os.environ.get(name, '')
    if v:
        return v
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith(f'{name}='):
                return line.split('=', 1)[1].strip()
    return ''


def build_default_models() -> list[ModelClient]:
    """Returns the model rotation pool based on available API keys."""
    dk = _load_key('DEEPSEEK_API_KEY')
    qk = _load_key('QWEN_API_KEY') or _load_key('DASHSCOPE_API_KEY')
    pool: list[ModelClient] = []
    deepseek = DeepseekClient(dk) if dk else None
    if deepseek:
        pool.append(deepseek)
    qwen = QwenClient(qk, fallback=deepseek) if (qk or deepseek) else None
    if qwen:
        pool.append(qwen)
    if not pool:
        pool.append(DryRunClient())
    return pool


# ───────────────────────── source extraction ─────────────────────────

def find_file_path(file_stem: str) -> Optional[Path]:
    """Locate a source file by stem (handles pigeon-suffixed names)."""
    candidates = []
    for pattern in (f'{file_stem}.py', f'{file_stem}_seq*.py',
                    f'src/{file_stem}.py', f'src/{file_stem}_seq*.py',
                    f'src/**/{file_stem}.py', f'src/**/{file_stem}_seq*.py',
                    f'client/**/{file_stem}.py', f'client/**/{file_stem}_seq*.py',
                    f'pigeon_compiler/**/{file_stem}.py',
                    f'pigeon_compiler/**/{file_stem}_seq*.py'):
        candidates.extend(ROOT.glob(pattern))
    if not candidates:
        return None
    # Prefer latest version (highest _vNNN)
    candidates.sort(key=lambda p: (str(p.name).count('_v'), p.name), reverse=True)
    return candidates[0]


def extract_function_source(file_path: Path, function_name: str) -> Optional[str]:
    """Extract one function/method source from a file via AST."""
    try:
        src = file_path.read_text('utf-8', errors='replace')
        tree = ast.parse(src)
    except SyntaxError:
        return None
    src_lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                start = node.lineno - 1
                end = node.end_lineno or (start + 1)
                return '\n'.join(src_lines[start:end])
    return None


# ───────────────────────── sandbox ─────────────────────────

def sandbox_run(candidate_source: str, test_code: Optional[str],
                module_name: str = "_candidate") -> tuple[bool, str]:
    """Exec candidate in a subprocess, run test_code against it.

    Returns (passed, combined_output). Timeout = 15s.
    Never writes to the real filesystem.
    """
    if not test_code:
        # No test → syntax check only
        try:
            ast.parse(candidate_source)
            return True, "PASS (syntax only, no test provided)"
        except SyntaxError as e:
            return False, f"FAIL syntax: {e}"

    script = textwrap.dedent(f"""
        import sys, types, traceback
        _m = types.ModuleType({module_name!r})
        try:
            exec(compile({candidate_source!r}, {module_name!r}, 'exec'), _m.__dict__)
            sys.modules[{module_name!r}] = _m
        except Exception:
            print('LOAD_FAIL')
            traceback.print_exc()
            sys.exit(1)
        try:
            exec(compile({test_code!r}, '<test>', 'exec'),
                 {{'_mod': _m, '__builtins__': __builtins__}})
            print('PASS')
        except AssertionError as e:
            print('FAIL_ASSERT:', e)
            sys.exit(2)
        except Exception:
            print('FAIL_EXC')
            traceback.print_exc()
            sys.exit(3)
    """)
    try:
        res = subprocess.run(
            [sys.executable, '-c', script],
            capture_output=True, text=True, timeout=15,
            cwd=str(ROOT),
        )
        out = (res.stdout + res.stderr)[:2000]
        return (res.returncode == 0 and 'PASS' in out), out
    except subprocess.TimeoutExpired:
        return False, "FAIL: sandbox timeout 15s"
    except Exception as e:
        return False, f"FAIL sandbox error: {e}"


# ───────────────────────── grading ─────────────────────────

def _token_estimate(src: str) -> int:
    return max(1, len(src) // 4)


def compute_grade(*, tests_passed: bool, original_source: str,
                  candidate_source: str, model_grade: float) -> tuple[float, int, float]:
    """Combine test result + compression delta + model self-grade into final grade.

    Returns (final_grade, context_size_delta, compression_reward).
    context_size_delta: negative = smaller = better.
    """
    orig_tokens = _token_estimate(original_source)
    new_tokens = _token_estimate(candidate_source)
    delta = new_tokens - orig_tokens
    # Reward for shrinking (up to 20% reward for halving size)
    compression_reward = max(-0.2, min(0.2, -delta / max(orig_tokens, 1) * 0.4))
    test_reward = 0.6 if tests_passed else -0.4
    # Weighted sum: tests dominate, model opinion is tiebreaker, compression nudges
    final = 0.55 * test_reward + 0.30 * model_grade + 0.15 * compression_reward
    return round(final, 3), delta, round(compression_reward, 3)


def detect_plateau(attempts: list[RewriteAttempt]) -> bool:
    """True if the last 3 attempts all within PLATEAU_DELTA of each other."""
    if len(attempts) < 3:
        return False
    recent = [a.final_grade for a in attempts[-3:]]
    return (max(recent) - min(recent)) < PLATEAU_DELTA


# ───────────────────────── scaffolding ─────────────────────────

def scaffold_test(job: IntentJob, model: ModelClient) -> str:
    """Produce a minimal pytest-style assertion that exercises the intent.

    For the MVP: if no test supplied, we generate a skeleton that checks the
    module loads and the target function (if any) is still callable.
    Copilot or operator is expected to replace this with a real test.
    """
    if job.test_code:
        return job.test_code
    fn = job.target_function
    if fn:
        return textwrap.dedent(f"""
            # auto-scaffolded test — replace with real behavior test
            assert hasattr(_mod, {fn!r}), 'function {fn} missing after rewrite'
            assert callable(getattr(_mod, {fn!r})), '{fn} not callable'
        """).strip()
    return "assert True  # no test scaffolded — rewrite will only be syntax-checked"


# ───────────────────────── persistence ─────────────────────────

def _append_log(obj: dict):
    LOGS.mkdir(exist_ok=True)
    with open(ORCH_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + '\n')


def write_candidate(job: IntentJob, attempt: RewriteAttempt) -> Path:
    ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    name = f'{job.target_file}__{attempt.model}_r{attempt.round_n}_{stamp}.py'
    path = ATTEMPTS_DIR / name
    path.write_text(attempt.candidate_source, 'utf-8')
    return path


def escalate(job: IntentJob, attempts: list[RewriteAttempt], reason: str):
    """Push an unfinished job to the operator backlog."""
    backlog = []
    if INTENT_BACKLOG.exists():
        try:
            backlog = json.loads(INTENT_BACKLOG.read_text('utf-8'))
            if not isinstance(backlog, list):
                backlog = []
        except Exception:
            backlog = []
    backlog.append({
        'ts': datetime.now(timezone.utc).isoformat(),
        'intent_text': job.intent_text,
        'target_file': job.target_file,
        'target_function': job.target_function,
        'escalation_reason': reason,
        'attempts': [asdict(a) for a in attempts],
    })
    INTENT_BACKLOG.write_text(json.dumps(backlog, indent=2, default=str), 'utf-8')


# ───────────────────────── pigeon commit ─────────────────────────

def commit_via_pigeon(job: IntentJob, final_source: str, *, dry_run: bool = True) -> dict:
    """Overwrite the target file with final_source, then let pigeon bump version.

    In dry_run: writes to logs/rewrite_attempts/ and returns what WOULD happen.
    Real: overwrites src file, stages change, commits; pigeon post-commit hook
    handles version bump + import rewrite.
    """
    path = find_file_path(job.target_file)
    if not path:
        return {'ok': False, 'reason': f'file not found: {job.target_file}'}
    if dry_run:
        shadow = ATTEMPTS_DIR / f'_FINAL_{path.name}'
        shadow.write_text(final_source, 'utf-8')
        return {'ok': True, 'dry_run': True, 'shadow': str(shadow),
                'would_overwrite': str(path)}
    # Real path: overwrite + git commit; post-commit hook takes over
    path.write_text(final_source, 'utf-8')
    try:
        subprocess.run(['git', 'add', str(path)], cwd=str(ROOT), check=True, timeout=10)
        msg = f"feat: self-rewrite {job.target_file} ({job.intent_code}) — {job.reason[:80]}"
        subprocess.run(['git', 'commit', '-m', msg], cwd=str(ROOT), check=True, timeout=30)
    except subprocess.CalledProcessError as e:
        return {'ok': False, 'reason': f'git failed: {e}', 'file': str(path)}
    return {'ok': True, 'file': str(path), 'committed': True}


# ───────────────────────── orchestrator ─────────────────────────

def orchestrate_job(job: IntentJob, *, models: Optional[list[ModelClient]] = None,
                    max_rounds: int = MAX_ROUNDS,
                    accept_threshold: float = ACCEPT_THRESHOLD,
                    dry_run: bool = True) -> dict:
    """Run the full rewrite loop for one intent_job.

    Returns a summary dict: {status, rounds, best_attempt, commit_info}.
    status ∈ {"accepted", "escalated", "no_source", "no_models"}
    """
    models = models or build_default_models()
    if not models:
        return {'status': 'no_models', 'job': asdict(job)}

    path = find_file_path(job.target_file)
    if not path:
        return {'status': 'no_source', 'reason': f'cannot find {job.target_file}',
                'job': asdict(job)}

    # Extract source (function or whole file)
    original_source = (extract_function_source(path, job.target_function)
                       if job.target_function else path.read_text('utf-8', errors='replace'))
    if not original_source:
        return {'status': 'no_source', 'reason': 'function not found in file',
                'job': asdict(job)}

    # Ensure we have a test
    job.test_code = scaffold_test(job, models[0])

    attempts: list[RewriteAttempt] = []
    print(f'\n[orchestrator] target={job.target_file}'
          f'{"::"+job.target_function if job.target_function else ""} '
          f'intent={job.intent_text[:60]!r}')
    print(f'[orchestrator] models={[m.name for m in models]} '
          f'max_rounds={max_rounds} dry_run={dry_run}')

    for round_n in range(max_rounds):
        # Adversarial rotation: writer[i] ↔ grader[(i+1) % len]
        writer = models[round_n % len(models)]
        grader = models[(round_n + 1) % len(models)]
        print(f'  round {round_n}: writer={writer.name} grader={grader.name}')

        try:
            candidate = writer.rewrite_function(
                intent=job.intent_text, file_stem=job.target_file,
                current_source=original_source, test_code=job.test_code,
                prev_attempts=attempts,
            )
        except Exception as e:
            attempts.append(RewriteAttempt(
                round_n=round_n, model=writer.name, candidate_source='',
                tests_passed=False, test_output='', self_score_delta=0.0,
                context_size_delta=0, final_grade=-1.0, error=str(e),
                ts=datetime.now(timezone.utc).isoformat()))
            continue

        passed, test_output = sandbox_run(candidate, job.test_code)
        model_grade, reason = grader.grade(
            intent=job.intent_text, candidate=candidate, test_output=test_output)
        final, ctx_delta, _ = compute_grade(
            tests_passed=passed, original_source=original_source,
            candidate_source=candidate, model_grade=model_grade)

        attempt = RewriteAttempt(
            round_n=round_n, model=writer.name, candidate_source=candidate,
            tests_passed=passed, test_output=test_output,
            self_score_delta=model_grade, context_size_delta=ctx_delta,
            final_grade=final, error=None if passed else reason,
            ts=datetime.now(timezone.utc).isoformat())
        attempts.append(attempt)

        candidate_path = write_candidate(job, attempt)
        _append_log({'event': 'attempt', 'round': round_n,
                     'writer': writer.name, 'grader': grader.name,
                     'passed': passed, 'final_grade': final,
                     'ctx_delta': ctx_delta, 'reason': reason,
                     'candidate_file': str(candidate_path),
                     'intent': job.intent_text[:120],
                     'target': job.target_file})
        print(f'    → passed={passed} grade={final:+.2f} ctx_delta={ctx_delta:+d}')

        if passed and final >= accept_threshold:
            commit = commit_via_pigeon(job, candidate, dry_run=dry_run)
            _append_log({'event': 'accept', 'round': round_n,
                         'final_grade': final, 'commit': commit,
                         'target': job.target_file})
            print(f'    ✓ ACCEPT grade={final:+.2f} commit={commit}')
            return {'status': 'accepted', 'rounds': round_n + 1,
                    'best_attempt': asdict(attempt), 'commit': commit}

        if detect_plateau(attempts):
            escalate(job, attempts, "grade plateau")
            _append_log({'event': 'escalate_plateau', 'rounds': round_n + 1,
                         'target': job.target_file})
            print('    ✗ PLATEAU → escalated to operator')
            return {'status': 'escalated', 'rounds': round_n + 1,
                    'reason': 'plateau',
                    'best_attempt': asdict(max(attempts, key=lambda a: a.final_grade))}

    # Max rounds reached without acceptance
    escalate(job, attempts, "max rounds reached")
    _append_log({'event': 'escalate_max_rounds', 'rounds': len(attempts),
                 'target': job.target_file})
    print('    ✗ MAX ROUNDS → escalated')
    return {'status': 'escalated', 'rounds': len(attempts),
            'reason': 'max_rounds',
            'best_attempt': asdict(max(attempts, key=lambda a: a.final_grade))}


def load_pending_intent_jobs(limit: int = 5) -> list[IntentJob]:
    """Pull recent 'simulated' jobs from intent_jobs.jsonl and expand to per-file."""
    if not INTENT_JOBS.exists():
        return []
    rows = []
    for line in INTENT_JOBS.read_text('utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if row.get('status') == 'simulated':
                rows.append(row)
        except Exception:
            continue
    out: list[IntentJob] = []
    for row in rows[-limit:]:
        out.extend(IntentJob.from_sim_job(row))
    return out


def run_pending(*, dry_run: bool = True, max_jobs: int = 3) -> list[dict]:
    jobs = load_pending_intent_jobs(limit=max_jobs)
    if not jobs:
        print('[orchestrator] no simulated intent jobs to process')
        return []
    models = build_default_models()
    results = []
    for job in jobs[:max_jobs]:
        results.append(orchestrate_job(job, models=models, dry_run=dry_run))
    return results


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Intent orchestrator — self-rewriting loop')
    p.add_argument('--apply', action='store_true',
                   help='Actually write + commit files (default: dry-run only)')
    p.add_argument('--max-jobs', type=int, default=3)
    p.add_argument('--max-rounds', type=int, default=MAX_ROUNDS)
    p.add_argument('--intent', type=str, default=None,
                   help='Override: run a single ad-hoc intent against --file')
    p.add_argument('--file', type=str, default=None,
                   help='Target file stem (for --intent mode)')
    p.add_argument('--function', type=str, default=None,
                   help='Target function name (for --intent mode)')
    args = p.parse_args()

    if args.intent and args.file:
        job = IntentJob(intent_text=args.intent, target_file=args.file,
                        target_function=args.function, reason='cli ad-hoc')
        res = orchestrate_job(job, max_rounds=args.max_rounds, dry_run=not args.apply)
        print(json.dumps(res, indent=2, default=str))
    else:
        results = run_pending(dry_run=not args.apply, max_jobs=args.max_jobs)
        for r in results:
            print(json.dumps({k: v for k, v in r.items() if k != 'best_attempt'},
                             indent=2, default=str))
