"""file_overwriter_seq001_v001 — autonomous file patcher triggered by sim grades.

When run_sim grades a file as needs_change=True (conf >= threshold), this module:
  1. Reads the full file source
  2. Calls DeepSeek chat to generate a minimal, valid replacement
  3. Backs up original to logs/file_overwrite_backups/<stem>/<ts>.py.bak
  4. Applies overwrite atomically (write tmp → rename)
  5. Logs to logs/file_overwrites.jsonl
  6. Updates file_profiles.json cortex with self_fix_attempted event

Manual:
  py -c "
  from pathlib import Path; import importlib.util
  spec = importlib.util.spec_from_file_location('fo', sorted(Path('src').glob('file_overwriter*.py'))[-1])
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  r = m.overwrite_file('tc_gemini', 'fix rate limit retry logic', dry_run=True)
  print(r['diff'][:400])
  "
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | ~220 lines | ~2,400 tokens
# DESC:   autonomous_file_patcher
# INTENT: feat_file_cortex
# LAST:   2026-04-22
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-22T00:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  initial build - autonomous file patcher
# EDIT_AUTHOR: copilot
# EDIT_STATE: active
# ── /pulse ──

from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request as _ur
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
OVERWRITE_LOG = ROOT / 'logs' / 'file_overwrites.jsonl'
BACKUP_DIR = ROOT / 'logs' / 'file_overwrite_backups'

# Only auto-overwrite at this confidence — below this it stays dry_run
AUTO_OVERWRITE_THRESHOLD = 0.85

_DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'
_DEEPSEEK_MODEL = 'deepseek-chat'

_PATCH_SYSTEM = """You are an expert Python programmer performing surgical code patches.
You will be given a Python source file and a targeted intent.

Output ONLY a series of search-replace blocks in this exact format — nothing else:

<<<SEARCH
<exact lines from the original file to replace>
===
<new lines to substitute>
>>>REPLACE

Rules:
- Include 2-3 lines of surrounding context in each SEARCH block so matches are unambiguous.
- SEARCH text must match the original file character-for-character (spaces, indentation).
- Make MINIMAL changes — only touch what the intent requires.
- If nothing needs changing, output exactly: NO_CHANGES
- Do NOT output the full file. Do NOT explain. Only output the blocks."""


def _load_deepseek_key(root: Path) -> str | None:
    v = os.environ.get('DEEPSEEK_API_KEY', '')
    if v:
        return v
    env = root / '.env'
    if env.exists():
        for line in env.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith('DEEPSEEK_API_KEY='):
                v = line.split('=', 1)[1].strip()
                if v:
                    return v
    return None


def _call_deepseek(system: str, user: str, api_key: str, timeout: int = 60) -> str:
    """Call DeepSeek chat API. Returns raw response text."""
    body = json.dumps({
        'model': _DEEPSEEK_MODEL,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        'max_tokens': 2048,
        'temperature': 0.1,
    }).encode('utf-8')
    req = _ur.Request(
        _DEEPSEEK_URL, data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {api_key}'},
        method='POST',
    )
    with _ur.urlopen(req, timeout=timeout) as resp:
        d = json.loads(resp.read())
    return d['choices'][0]['message']['content'].strip()


def _parse_search_replace_blocks(text: str) -> list[tuple[str, str]]:
    """Parse <<<SEARCH ... === ... >>>REPLACE blocks from DeepSeek response.
    Returns list of (search_text, replace_text) pairs.
    """
    blocks: list[tuple[str, str]] = []
    pattern = re.compile(
        r'<<<SEARCH\s*\n(.*?)\n===\s*\n(.*?)\n>>>REPLACE',
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        blocks.append((m.group(1), m.group(2)))
    return blocks


def _apply_search_replace(original: str, blocks: list[tuple[str, str]]) -> tuple[str, list[str]]:
    """Apply search-replace blocks to source text.
    Returns (patched_source, list_of_errors).
    """
    result = original
    errors: list[str] = []
    for i, (search, replace) in enumerate(blocks):
        if search in result:
            result = result.replace(search, replace, 1)
        else:
            # try stripping trailing whitespace differences
            stripped_search = '\n'.join(l.rstrip() for l in search.splitlines())
            stripped_result = '\n'.join(l.rstrip() for l in result.splitlines())
            if stripped_search in stripped_result:
                # rebuild with stripped comparison — apply via line scan
                result_lines = result.splitlines(keepends=True)
                search_lines = search.splitlines()
                n = len(search_lines)
                applied = False
                for j in range(len(result_lines) - n + 1):
                    window = [l.rstrip() for l in result_lines[j:j + n]]
                    if window == search_lines:
                        indent = result_lines[j][: len(result_lines[j]) - len(result_lines[j].lstrip())]
                        result = (
                            ''.join(result_lines[:j])
                            + replace
                            + ('\n' if not replace.endswith('\n') else '')
                            + ''.join(result_lines[j + n:])
                        )
                        applied = True
                        break
                if not applied:
                    errors.append(f'block {i + 1}: SEARCH text not found')
            else:
                errors.append(f'block {i + 1}: SEARCH text not found (tried strip)')
    return result, errors


def _find_file(stem: str, root: Path) -> Path | None:
    """Find the Python file for a given stem. Returns first match."""
    for pattern in (
        f'src/{stem}.py', f'src/{stem}_seq*.py', f'src/**/{stem}.py', f'src/**/{stem}_seq*.py',
        f'client/{stem}.py', f'pigeon_compiler/**/{stem}.py', f'pigeon_brain/**/{stem}.py',
        f'{stem}.py',
    ):
        hits = list(root.glob(pattern))
        if hits:
            return hits[0]
    return None


def _make_diff(original: str, patched: str) -> str:
    """Simple line-level diff for display (not git diff)."""
    orig_lines = original.splitlines()
    new_lines = patched.splitlines()
    added = sum(1 for l in new_lines if l not in orig_lines)
    removed = sum(1 for l in orig_lines if l not in new_lines)
    changed = min(added, removed)
    net = len(new_lines) - len(orig_lines)
    return (f'+{added} lines added, -{removed} lines removed, '
            f'~{changed} changed, net {net:+d}')


def _backup_file(path: Path, root: Path) -> Path:
    """Copy file to logs/file_overwrite_backups/<stem>/<ts>.py.bak."""
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    bak_dir = root / 'logs' / 'file_overwrite_backups' / path.stem
    bak_dir.mkdir(parents=True, exist_ok=True)
    bak_path = bak_dir / f'{ts}.py.bak'
    shutil.copy2(path, bak_path)
    return bak_path


def _atomic_write(path: Path, content: str) -> None:
    """Write content to a tmp file in the same dir, then rename (atomic on same FS)."""
    tmp = path.with_suffix('.tmp_overwrite')
    tmp.write_text(content, encoding='utf-8')
    tmp.rename(path)


def _run_regression(stem: str, path: Path, bak_path: Path, root: Path) -> dict:
    """Run post-patch regression: py_compile syntax check, then matching test file.
    Restores backup if either step fails.
    Returns {passed, failed, error, test_file}.
    """
    out = {'passed': False, 'failed': False, 'error': '', 'test_file': ''}

    # 1. Syntax check
    r = subprocess.run(
        [sys.executable, '-m', 'py_compile', str(path)],
        capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0:
        shutil.copy2(bak_path, path)
        out['failed'] = True
        out['error'] = f'syntax: {(r.stderr or r.stdout)[:200]}'
        print(f'  [regression] ✗ syntax failed for {stem} — restored')
        return out

    # 2. Find matching test file in tests/interlink/
    test_dir = root / 'tests' / 'interlink'
    stem_short = stem.split('_seq')[0]  # e.g. tc_gemini
    test_file: Path | None = None
    for pattern in (
        f'test_{stem}.py',
        f'test_{stem_short}.py',
        f'test_{stem_short}_seq*.py',
    ):
        hits = sorted(test_dir.glob(pattern))
        if hits:
            test_file = hits[-1]  # newest version
            break

    if test_file is None:
        # No test file — syntax passed, that's the full check
        out['passed'] = True
        out['test_file'] = 'none (no matching test)'
        print(f'  [regression] ✓ syntax OK, no test file for {stem}')
        return out

    out['test_file'] = test_file.name
    r = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=True, text=True, timeout=30, cwd=str(root),
    )
    if r.returncode != 0:
        shutil.copy2(bak_path, path)
        out['failed'] = True
        snippet = (r.stdout + r.stderr)[:300]
        out['error'] = f'test {test_file.name}: {snippet}'
        print(f'  [regression] ✗ test failed for {stem} — restored')
        return out

    out['passed'] = True
    print(f'  [regression] ✓ {test_file.name} passed for {stem}')
    return out


def _update_cortex(stem: str, root: Path, fix: str, success: bool, trigger: str) -> None:
    """Fire update_file_cortex without hard-importing file_sim (avoids circular)."""
    try:
        import importlib.util
        matches = sorted((root / 'src').glob('file_sim*.py'), key=lambda p: len(p.name))
        if not matches:
            return
        spec = importlib.util.spec_from_file_location('file_sim', matches[-1])
        m = importlib.util.module_from_spec(spec)
        if spec and spec.loader:
            spec.loader.exec_module(m)
            m.update_file_cortex(stem, root, event={
                'type': 'self_fix_attempted',
                'fix': fix,
                'success': success,
                'trigger': trigger,
            })
    except Exception:
        pass


def overwrite_file(
        stem: str,
        intent_text: str,
        grade_result: dict | None = None,
        root: Path | None = None,
        dry_run: bool = True,
) -> dict:
    """Patch a file to fulfil an intent.

    Args:
        stem:          module stem (e.g. 'tc_gemini', 'w_gpmo')
        intent_text:   the operator intent driving the change
        grade_result:  dict from grade_file_for_intent (optional — used for context)
        root:          workspace root (default ROOT)
        dry_run:       if True, generates patch but does NOT write to disk

    Returns:
        {applied, diff, error, backup_path, patched_preview, dry_run}
    """
    root = root or ROOT
    out: dict = {'applied': False, 'diff': '', 'error': '',
                 'backup_path': '', 'patched_preview': '', 'dry_run': dry_run,
                 'regression': {}}

    api_key = _load_deepseek_key(root)
    if not api_key:
        out['error'] = 'no DEEPSEEK_API_KEY in .env'
        return out

    path = _find_file(stem, root)
    if path is None:
        out['error'] = f'{stem} — file not found'
        return out

    original = path.read_text('utf-8', errors='replace')
    grade_reason = (grade_result or {}).get('reason', '')
    confidence = (grade_result or {}).get('confidence', 0.0)

    user_prompt = (
        f'INTENT: {intent_text[:400]}\n\n'
        f'GRADE REASON: {grade_reason}\n\n'
        f'FILE PATH: {path.relative_to(root)}\n\n'
        f'FILE SOURCE (full):\n```python\n{original}\n```\n\n'
        f'Output search-replace blocks for the minimal change that fulfils the intent.'
    )

    print(f'  [overwriter] calling DeepSeek for {stem} (conf={confidence:.2f})…')
    t0 = time.perf_counter()
    try:
        raw = _call_deepseek(_PATCH_SYSTEM, user_prompt, api_key)
    except Exception as e:
        out['error'] = f'DeepSeek call failed: {e}'
        _log_overwrite(stem, intent_text, dry_run=dry_run, success=False,
                       error=out['error'], diff='', backup_path='', root=root)
        return out
    elapsed = time.perf_counter() - t0
    print(f'  [overwriter] DeepSeek responded in {elapsed:.1f}s')

    # Parse surgical blocks — if NO_CHANGES or empty, nothing to do
    if raw.strip().upper().startswith('NO_CHANGES') or not raw.strip():
        out['diff'] = 'no changes needed'
        out['error'] = ''
        print(f'  [overwriter] {stem}: DeepSeek says no changes needed')
        return out

    blocks = _parse_search_replace_blocks(raw)
    if not blocks:
        out['error'] = f'no search-replace blocks found in response — raw: {raw[:120]}'
        return out

    patched, apply_errors = _apply_search_replace(original, blocks)
    if apply_errors:
        out['error'] = '; '.join(apply_errors)
        # partial apply is fine — report errors but continue if patched differs
        if patched == original:
            return out

    if patched == original:
        out['diff'] = 'no changes (blocks matched but no diff)'
        return out

    diff = _make_diff(original, patched)
    out['diff'] = diff
    out['patched_preview'] = patched[:600]

    if dry_run:
        print(f'  [overwriter] DRY RUN — would apply: {diff}')
        out['dry_run'] = True
        _log_overwrite(stem, intent_text, dry_run=True, success=False,
                       error='', diff=diff, backup_path='', regression={}, root=root)
        return out

    # Live write — backup first
    bak_path = _backup_file(path, root)
    out['backup_path'] = str(bak_path)
    try:
        _atomic_write(path, patched)
    except Exception as e:
        shutil.copy2(bak_path, path)
        out['error'] = f'write failed (restored): {e}'
        _log_overwrite(stem, intent_text, dry_run=False, success=False,
                       error=out['error'], diff=diff,
                       backup_path=str(bak_path), regression={}, root=root)
        return out

    # Regression TDD — syntax check + matching test file
    reg = _run_regression(stem, path, bak_path, root)
    out['regression'] = reg
    if reg['failed']:
        # backup already restored by _run_regression
        out['applied'] = False
        out['error'] = f'regression failed — restored: {reg["error"][:120]}'
        print(f'  [overwriter] ✗ {stem}: regression rolled back patch')
    else:
        out['applied'] = True
        print(f'  [overwriter] ✓ applied {path.name} | {diff} | test: {reg["test_file"]}')

    _log_overwrite(stem, intent_text, dry_run=False, success=out['applied'],
                   error=out['error'], diff=diff,
                   backup_path=str(bak_path), regression=reg, root=root)
    _update_cortex(stem, root,
                   fix='file_overwriter',
                   success=out['applied'],
                   trigger=f'sim_grade conf={confidence:.2f}')
    return out


def _log_overwrite(stem: str, intent: str, dry_run: bool, success: bool,
                   error: str, diff: str, backup_path: str,
                   regression: dict, root: Path) -> None:
    OVERWRITE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'stem': stem,
        'intent_preview': intent[:80],
        'dry_run': dry_run,
        'applied': success,
        'diff': diff,
        'backup_path': backup_path,
        'error': error,
        'regression_passed': regression.get('passed', None),
        'regression_test': regression.get('test_file', ''),
        'regression_error': regression.get('error', ''),
    }
    with open(OVERWRITE_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def pending_overwrites(root: Path | None = None) -> list[dict]:
    """Return sim grades that are awaiting overwrite (needs_change=True, not yet overwritten)."""
    root = root or ROOT
    sim_log = root / 'logs' / 'sim_results.jsonl'
    if not sim_log.exists():
        return []

    # Build set of already-overwritten stems from overwrite log
    done: set[str] = set()
    if OVERWRITE_LOG.exists():
        for line in OVERWRITE_LOG.read_text('utf-8', errors='ignore').splitlines():
            try:
                e = json.loads(line)
                if e.get('applied'):
                    done.add(e['stem'])
            except Exception:
                pass

    pending = []
    for line in sim_log.read_text('utf-8', errors='ignore').splitlines():
        try:
            e = json.loads(line)
            if (e.get('needs_change') and not e.get('self_excluded')
                    and e.get('confidence', 0) >= AUTO_OVERWRITE_THRESHOLD
                    and e.get('file_stem') not in done):
                pending.append(e)
        except Exception:
            pass
    return pending
