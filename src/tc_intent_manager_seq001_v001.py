"""Intent job block reader for thought completer.

Reads from intent_backlog_latest.json — compiled per push by the push cycle.
Each entry is a verified/unverified job: partial prompt intent that may not
have been acted on. Copilot can only clear a job once work is confirmed done.

TC injects these open jobs into Gemini so completions steer toward unfinished
work rather than completing words in a vacuum.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

from .tc_constants_seq001_v001 import ROOT

_JOURNAL_PATH = ROOT / 'logs' / 'prompt_journal.jsonl'
_RECENT_N = 30  # prompts to use for session signal


def _load_recent_prompts() -> list[dict]:
    if not _JOURNAL_PATH.exists():
        return []
    try:
        lines = _JOURNAL_PATH.read_text('utf-8', errors='ignore').splitlines()
        entries = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
            if len(entries) >= _RECENT_N:
                break
        return entries
    except Exception:
        return []


def _score_job_relevance(job: dict, triggers: set[str], files: set[str]) -> float:
    """Score how relevant a job is to the current session signals."""
    score = 0.0
    job_text = (job.get('msg', '') + ' ' + ' '.join(job.get('module_refs', []))).lower()
    for t in triggers:
        if t in job_text:
            score += 1.0
    for f in files:
        if f in job_text:
            score += 1.5  # files are stronger signal
    return score

_CACHE: dict | None = None
_CACHE_TS: float = 0
_CACHE_TTL = 60  # seconds — backlog rebuilds per push, not per keystroke


def _load_backlog() -> list[dict]:
    path = ROOT / 'logs' / 'intent_backlog_latest.json'
    if not path.exists():
        return []
    try:
        d = json.loads(path.read_text('utf-8', errors='ignore'))
        return d.get('intents', [])
    except Exception:
        return []


def get_active_intent_block() -> str:
    """Build the OPEN JOBS block for the Gemini prompt.

    Lists unresolved intent jobs from the per-push compiler.
    Jobs are sorted: partial first (furthest along), then cold (untouched).
    Capped at 5 to stay prompt-budget friendly.
    """
    global _CACHE, _CACHE_TS
    now = time.time()
    if _CACHE is not None and (now - _CACHE_TS) < _CACHE_TTL:
        return _CACHE.get('block', '')

    intents = _load_backlog()
    # Only unresolved jobs
    open_jobs = [i for i in intents if i.get('status') not in ('verified', 'done', 'resolved')]
    if not open_jobs:
        _CACHE = {'block': ''}
        _CACHE_TS = now
        return ''

    # Build session signal from recent prompts
    try:
        from .tc_profile_seq001_v001.tc_profile_seq001_v001_intent_extractors_seq039_v001 import (
            extract_session_triggers, extract_session_files
        )
        recent = _load_recent_prompts()
        session_triggers = set(extract_session_triggers(recent, min_count=1))
        session_files = set(extract_session_files(recent))
    except Exception:
        session_triggers, session_files = set(), set()

    # Sort: session relevance first, then partial > cold, then confidence
    def _sort_key(j: dict) -> tuple:
        relevance = _score_job_relevance(j, session_triggers, session_files)
        status_rank = {'partial': 0, 'cold': 1}.get(j.get('status', 'cold'), 2)
        return (-relevance, status_rank, -(j.get('confidence', 0)))

    open_jobs.sort(key=_sort_key)
    top = open_jobs[:5]

    lines = [f'OPEN INTENT JOBS ({len(open_jobs)} unresolved — compiled from prompt history):']
    lines.append('These are operator goals that have NOT been completed/verified yet.')
    lines.append('Steer completions toward closing the most relevant open job.')
    for job in top:
        status = job.get('status', '?')
        conf = job.get('confidence', 0)
        msg = job.get('msg', job.get('msg_preview', ''))[:120]
        reason = job.get('verification_reason', '')
        mods = ', '.join(job.get('module_refs', [])[:3])
        entry = f'  [{status}|conf={conf:.2f}] {msg}'
        if reason:
            entry += f' — why_open: {reason[:60]}'
        if mods:
            entry += f' — refs: {mods}'
        lines.append(entry)
    lines.append(
        'DIRECTIVE: When buffer relates to any open job, complete toward CLOSING it. '
        'Be specific — name files, actions, and verification steps.'
    )

    block = '\n'.join(lines)
    _CACHE = {'block': block}
    _CACHE_TS = now
    return block
