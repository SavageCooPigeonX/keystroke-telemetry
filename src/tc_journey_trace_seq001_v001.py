"""tc_journey_trace_seq001_v001 — trace full prompt journey through the pipeline.

Shows: prompt → composition binding → journal → thought_completer instance
       → context files → Copilot file edits → recon rewrites.

Usage:
    py -m src.tc_journey_trace_seq001_v001          # terminal report
    py -m src.tc_journey_trace_seq001_v001 --watch  # live refresh every 5s
"""
from __future__ import annotations
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _age(ts_str: str) -> str:
    try:
        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        delta = (datetime.now(timezone.utc) - ts).total_seconds()
        if delta < 60:
            return f'{delta:.0f}s ago'
        return f'{delta/60:.1f}min ago'
    except Exception:
        return '?'


def _read_jsonl_last(path: Path, n: int = 1) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text('utf-8', errors='ignore').strip().split('\n')
    out = []
    for ln in lines[-n:]:
        try:
            out.append(json.loads(ln))
        except Exception:
            pass
    return out


def trace(verbose: bool = False) -> str:
    lines = []
    w = lines.append

    w('=' * 72)
    w('  PROMPT JOURNEY TRACE')
    w('=' * 72)

    # ── 1. prompt telemetry ────────────────────────────────────────────────
    pt_path = ROOT / 'logs' / 'prompt_telemetry_latest.json'
    pt = json.loads(pt_path.read_text('utf-8', errors='ignore')) if pt_path.exists() else {}
    lp   = pt.get('latest_prompt', {})
    cb   = pt.get('composition_binding', {})
    sigs = pt.get('signals', {})
    dw   = pt.get('deleted_words', [])
    ts   = lp.get('ts', '')

    w(f'\n[1] PROMPT  {_age(ts)}')
    w(f'    text     : {str(lp.get("preview", "?"))[:100]}')
    w(f'    intent   : {lp.get("intent", "?")}')
    w(f'    state    : {lp.get("state", "?")}')
    w(f'    wpm      : {sigs.get("wpm", "?")}  '
      f'del={sigs.get("deletion_ratio", "?"):.1%}  '
      f'hes={sigs.get("hesitation_count", "?")}')
    w(f'    deleted  : {dw}')

    # ── 2. composition binding ────────────────────────────────────────────
    matched   = cb.get('matched', False)
    age_ms    = cb.get('age_ms', 0)
    mscore    = cb.get('match_score', 0)
    cb_source = cb.get('source', '?')
    cb_key    = str(cb.get('key', ''))[:90]

    w(f'\n[2] COMPOSITION BINDING')
    status = '✓ PAIRED' if matched else '✗ UNBOUND'
    w(f'    status   : {status}')
    w(f'    source   : {cb_source}')
    w(f'    age_ms   : {age_ms}  score={mscore}')
    if cb_key:
        w(f'    key      : {cb_key}')

    # ── 3. journal ────────────────────────────────────────────────────────
    j_entries = _read_jsonl_last(ROOT / 'logs' / 'prompt_journal.jsonl', 1)
    if j_entries:
        j = j_entries[0]
        w(f'\n[3] JOURNAL  session_n={j.get("session_n")}  {_age(j.get("ts",""))}')
        w(f'    msg      : {str(j.get("msg", ""))[:100]}')
        w(f'    intent   : {j.get("intent")}')
        w(f'    deleted  : {j.get("deleted_words")}')
        w(f'    rewrites : {j.get("rewrites", [])}')
        w(f'    mod_refs : {j.get("module_refs", [])}')
        w(f'    source   : {j.get("source")}')

    # ── 4. thought_completer instance ────────────────────────────────────
    tc_path = ROOT / 'logs' / 'thought_completions.jsonl'
    tc_entries = _read_jsonl_last(tc_path, 100)
    prompt_words = set(str(lp.get('preview', '')).lower().split()[:6])

    matched_comp = None
    for c in reversed(tc_entries):
        buf_words = set(c.get('buffer', '').lower().split())
        if len(prompt_words & buf_words) >= 3:
            matched_comp = c
            break
    comp = matched_comp or (tc_entries[-1] if tc_entries else {})
    label = 'prompt-matched' if matched_comp else 'latest'

    if comp:
        w(f'\n[4] THOUGHT COMPLETER  [{label}]  {_age(comp.get("ts",""))}')
        w(f'    buffer   : {str(comp.get("buffer", ""))[:80]}')
        w(f'    completion: {str(comp.get("completion", ""))[:80]}')
        w(f'    accepted : {comp.get("accepted")}')
        w(f'    latency  : {comp.get("latency_ms")}ms')
        w(f'    model    : {comp.get("model")}')
        w(f'    repo     : {comp.get("repo")}')
        ctx_files = comp.get('context_files', [])
        w(f'    ctx_files: {ctx_files}')

    # ── 5. files touched by Copilot ───────────────────────────────────────
    w(f'\n[5] FILES TOUCHED (Copilot edits — git diff)')
    try:
        r1 = subprocess.run(['git', 'diff', '--name-only', 'HEAD'],
                            capture_output=True, text=True, cwd=str(ROOT))
        r2 = subprocess.run(['git', 'diff', '--name-only'],
                            capture_output=True, text=True, cwd=str(ROOT))
        touched = sorted(set(
            (r1.stdout + r2.stdout).strip().split('\n')
        ))
        touched = [f for f in touched if f]
        if touched:
            for f in touched[:20]:
                w(f'    {f}')
        else:
            w('    (none — all committed or no changes)')
    except Exception as e:
        w(f'    git error: {e}')

    # ── 6. pulse blocks (prompt→file pairing) ─────────────────────────────
    w(f'\n[6] PULSE BLOCKS  (prompt→file edit pairing)')
    ph = ROOT / 'logs' / 'pulse_harvest_latest.json'
    if ph.exists():
        try:
            phd = json.loads(ph.read_text('utf-8', errors='ignore'))
            for entry in (phd if isinstance(phd, list) else [])[:5]:
                w(f'    {entry.get("file","")} | {entry.get("edit_why","")} | {entry.get("edit_ts","")}')
        except Exception:
            w('    (parse error)')
    else:
        w('    pulse_harvest_latest.json missing — pulse_harvest daemon may be down')

    # ── 7. composition recon ──────────────────────────────────────────────
    rcon_entries = _read_jsonl_last(
        ROOT / 'logs' / 'composition_recon_seq001_v001.jsonl', 1)
    if rcon_entries:
        rc = rcon_entries[0]
        w(f'\n[7] RECON  {_age(rc.get("ts",""))}')
        for res in rc.get('results', []):
            rtype = res.get('type', '?')
            rws = res.get('rewrites', [])
            w(f'    type={rtype}  rewrites={len(rws)}')
            for rw in rws[:2]:
                fr = str(rw.get('from_text', ''))[:55]
                to = str(rw.get('to_text',   ''))[:55]
                w(f'      {_age(rw.get("ts",""))}: {fr!r} → {to!r}')

    w('\n' + '=' * 72)
    return '\n'.join(lines)


def _watch():
    while True:
        print('\033[2J\033[H', end='')   # clear terminal
        print(trace())
        print('\n(refreshing every 5s — Ctrl+C to stop)')
        time.sleep(5)


if __name__ == '__main__':
    if '--watch' in sys.argv:
        try:
            _watch()
        except KeyboardInterrupt:
            pass
    else:
        print(trace())


def build_trace() -> list[tuple[str, list[tuple[str, str]]]]:
    """Return structured trace for observatory rendering.
    Returns list of (stage_name, [(tag, text), ...]).
    """
    raw = trace()
    stages = []
    current_name = 'INIT'
    current_lines: list[tuple[str, str]] = []

    for line in raw.split('\n'):
        if line.startswith('[') and ']' in line[:6]:
            if current_lines:
                stages.append((current_name, current_lines))
            current_name = line[1:line.index(']')]
            rest = line[line.index(']')+1:].strip()
            current_lines = [('val', rest)] if rest else []
        elif line.startswith('=') or not line.strip():
            pass
        else:
            stripped = line.strip()
            tag = ('ok' if '✓' in stripped else
                   'warn' if '✗' in stripped or '?' in stripped else
                   'dim' if stripped.startswith('(') else 'val')
            current_lines.append((tag, stripped))

    if current_lines:
        stages.append((current_name, current_lines))
    return stages
