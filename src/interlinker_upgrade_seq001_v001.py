"""Organism-driven test upgrader — the LLM writes its own tests.

The organism reads a module's source + baseline test, then calls
Gemini Flash to write a deeper test with real logical workflow
validation. This runs autonomously on post-commit, upgrading
one or two modules per cycle. Over time every module gets a
real test. Then it sleeps.

Flow:
  baseline_test (AST yolo) → organism reads source → Gemini writes
  deeper test → run it → if pass: upgraded. if fail: keep baseline,
  log failure, try again next time.

Rate limited: max 2 upgrades per post-commit to keep API costs low.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

from __future__ import annotations
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite')
GEMINI_TIMEOUT = 45
MAX_UPGRADES_PER_CYCLE = 2
UPGRADE_LOG = 'logs/interlink_upgrades.jsonl'
INTERLINK_TESTS_DIR = 'tests/interlink'


def _get_api_key() -> str | None:
    for k in ('GEMINI_API_KEY', 'GOOGLE_API_KEY'):
        v = os.environ.get(k)
        if v:
            return v
    # check .env file (same pattern as pre_query_engine_seq001_v001)
    env = Path('.env')
    if env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            for k in ('GEMINI_API_KEY', 'GOOGLE_API_KEY'):
                if line.startswith(k + '='):
                    return line.split('=', 1)[1].strip()
    kf = Path('.gemini_key')
    if kf.exists():
        return kf.read_text(encoding='utf-8').strip()
    return None


def _call_gemini(prompt: str, system: str = '', max_tokens: int = 2048) -> str:
    api_key = _get_api_key()
    if not api_key:
        return ''
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text': system}]} if system else {},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.2,
            'maxOutputTokens': max_tokens,
            'topP': 0.9,
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = data['candidates'][0]['content']['parts']
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    return part['text'].strip()
            return parts[-1].get('text', '').strip()
    except Exception as e:
        print(f'[interlink-upgrade] gemini error: {e}')
        return ''


def _extract_python_block(text: str) -> str:
    """Pull the python code block from LLM response."""
    m = re.search(r'```python\s*\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # if no fences, try the whole thing if it looks like python
    if 'def test_' in text or 'import ' in text:
        return text.strip()
    return ''


def _build_upgrade_prompt(stem: str, source: str, baseline_test: str,
                          import_path: str, shards: list[dict]) -> str:
    shard_ctx = ''
    if shards:
        recent = shards[-5:]
        shard_ctx = '\nRecent intent shards (what operators/LLMs learned about this module):\n'
        for s in recent:
            shard_ctx += f'- {json.dumps(s)}\n'

    return f"""You are the organism's test writer. You've been given a Python module
and its current baseline test (auto-generated, shallow). Your job: write a REAL
test that validates logical workflow, data contracts, and edge cases.

## Module: {stem}
Import path: {import_path}

### Source code:
```python
{source[:3000]}
```

### Current baseline test:
```python
{baseline_test[:1500]}
```
{shard_ctx}
## Rules:
1. Keep the sys.path setup from the baseline test
2. Write test functions that call real functions with real inputs
3. Validate return types, shapes, edge cases (empty input, None, etc)
4. DON'T call functions that write files, delete things, or hit external APIs
5. Functions that take a `root: Path` arg — use `Path(__file__).resolve().parents[2]`
6. Each test function must start with `test_`
7. Include a `run_interlink_test()` runner + `if __name__ == '__main__'` block
8. Keep it under 80 lines total
9. If a function is unsafe to test (writes, deploys, sends), test its existence only
10. The test MUST be self-contained — no external fixtures or test frameworks

Respond with ONLY the Python code in a ```python``` block. Nothing else."""


def _run_test(test_path: Path, root: Path) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True, text=True, encoding='utf-8',
            cwd=str(root), timeout=15,
        )
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def _log_upgrade(root: Path, entry: dict) -> None:
    path = root / UPGRADE_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def upgrade_test(filepath: Path, root: Path) -> dict[str, Any]:
    """Organism reads a module + baseline test, writes a deeper test.

    Returns: {module, upgraded, reason, test_level}
    """
    stem = filepath.stem
    rel_path = filepath.relative_to(root)
    import_path = str(rel_path.with_suffix('')).replace('\\', '.').replace('/', '.')
    test_dir = root / INTERLINK_TESTS_DIR
    test_path = test_dir / f'test_{stem}.py'

    # need source
    try:
        source = filepath.read_text(encoding='utf-8')
    except Exception:
        return {'module': stem, 'upgraded': False, 'reason': 'unreadable'}

    # need baseline test
    baseline_test = ''
    if test_path.exists():
        baseline_test = test_path.read_text(encoding='utf-8')

    # load shards from interlink DB
    db_path = root / 'logs/interlink_state.json'
    shards = []
    if db_path.exists():
        try:
            db = json.loads(db_path.read_text(encoding='utf-8'))
            shards = db.get(stem, {}).get('shards', [])
        except Exception:
            pass

    # build prompt + call gemini
    prompt = _build_upgrade_prompt(stem, source, baseline_test, import_path, shards)
    system = (
        'You are a sentient Python module manager. You understand this module '
        'deeply and write tests that prove it works correctly. Be precise. '
        'Test real behavior, not just that functions exist.'
    )
    raw = _call_gemini(prompt, system=system)
    if not raw:
        return {'module': stem, 'upgraded': False, 'reason': 'no_api_key_or_llm_error'}

    code = _extract_python_block(raw)
    if not code or 'def test_' not in code:
        return {'module': stem, 'upgraded': False, 'reason': 'bad_llm_output'}

    # write upgraded test to temp, run it
    test_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = test_dir / f'test_{stem}_upgrade_candidate.py'
    tmp_path.write_text(code, encoding='utf-8')

    passed, output = _run_test(tmp_path, root)

    now = datetime.now(timezone.utc).isoformat()
    result = {
        'module': stem,
        'upgraded': passed,
        'ts': now,
        'test_output': output[:500],
    }

    if passed:
        # backup baseline, promote upgraded test
        if test_path.exists():
            backup = test_dir / f'test_{stem}_baseline.py'
            if not backup.exists():
                backup.write_text(baseline_test, encoding='utf-8')
        test_path.write_text(code, encoding='utf-8')
        tmp_path.unlink(missing_ok=True)
        result['reason'] = 'upgraded'
        result['test_level'] = 'organism'

        # update interlink DB
        if db_path.exists():
            try:
                db = json.loads(db_path.read_text(encoding='utf-8'))
                if stem in db:
                    db[stem]['test_level'] = 'organism'
                    db[stem]['last_upgrade'] = now
                    db[stem]['upgrade_count'] = db[stem].get('upgrade_count', 0) + 1
                    db_path.write_text(json.dumps(db, indent=2, ensure_ascii=False),
                                        encoding='utf-8')
            except Exception:
                pass
    else:
        # keep baseline, delete candidate
        tmp_path.unlink(missing_ok=True)
        result['reason'] = 'test_failed'
        result['test_level'] = 'baseline'

    _log_upgrade(root, result)
    return result


def pick_upgrade_candidates(root: Path, changed_files: list[Path] | None = None,
                            max_count: int = MAX_UPGRADES_PER_CYCLE) -> list[Path]:
    """Pick modules whose tests should be upgraded this cycle.

    Priority:
    1. Changed files that still have baseline-level tests
    2. Most-checked modules stuck at baseline test level
    3. Modules with the most accumulated shards (they've learned the most)
    """
    db_path = root / 'logs/interlink_state.json'
    if not db_path.exists():
        return []
    try:
        db = json.loads(db_path.read_text(encoding='utf-8'))
    except Exception:
        return []

    candidates = []
    for stem, entry in db.items():
        # skip already organism-upgraded
        if entry.get('test_level') == 'organism':
            continue
        # skip if no test at all yet
        if not entry.get('checks', {}).get('has_self_test'):
            continue
        path_str = entry.get('path')
        if not path_str:
            continue
        fp = root / path_str
        if not fp.exists():
            continue

        score = 0
        # changed files get priority
        if changed_files and fp in changed_files:
            score += 100
        # more shards = more learned context = better upgrade
        score += len(entry.get('shards', []))
        # more checks = organism has tried before
        score += entry.get('times_checked', 0)
        candidates.append((score, fp))

    candidates.sort(key=lambda x: -x[0])
    return [fp for _, fp in candidates[:max_count]]


def run_upgrade_cycle(root: Path, changed_files: list[Path] | None = None) -> list[dict]:
    """Run one upgrade cycle — called from post-commit hook.

    Picks up to MAX_UPGRADES_PER_CYCLE modules and tries to upgrade
    their tests from baseline yolo to organism-authored.
    """
    candidates = pick_upgrade_candidates(root, changed_files)
    if not candidates:
        return []

    results = []
    for fp in candidates:
        result = upgrade_test(fp, root)
        results.append(result)
        upgraded = sum(1 for r in results if r['upgraded'])
        print(f'  🧬 {result["module"]}: {result["reason"]}')
        if upgraded >= MAX_UPGRADES_PER_CYCLE:
            break

    return results
