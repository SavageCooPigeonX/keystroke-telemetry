"""classify_bridge.py — VS Code extension ↔ Python classifier bridge.

Reads keystroke events from stdin, computes message metrics, classifies
cognitive state using the existing operator_stats classifiers, updates
operator_profile.md, and refreshes copilot-instructions.md in-place.

Every LLM_REWRITE_EVERY *submitted* messages, calls DeepSeek to synthesize
a rich behavioral coaching block from the full history. This block is written
to operator_coaching.md and injected into copilot-instructions.md so Copilot
adapts to the operator's real evolving patterns — not just static templates.

Stdin:  {"events": [...], "submitted": bool}
Argv:   <repo_root>
Stdout: {"state": str, "hesitation": float, "wpm": float, "coaching_updated": bool}
"""
import sys
import json
import os
import importlib.util
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

# Rewrite the coaching prose every N *submitted* messages
LLM_REWRITE_EVERY = 8


def _load_pigeon_module(root: Path, pattern: str):
    """Dynamic import for pigeon files (filename mutates on every commit)."""
    matches = sorted(root.glob(pattern))
    if not matches:
        return None
    spec = importlib.util.spec_from_file_location('_pigeonmod', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _compute_metrics(events: list, submitted: bool) -> dict:
    inserts = [e for e in events if e.get('type') == 'insert']
    deletes = [e for e in events if e.get('type') == 'backspace']
    pauses  = [e for e in events if e.get('type') == 'pause']
    total   = max(len(events), 1)

    pause_ms_list = [e.get('duration_ms', 0) for e in pauses]
    total_pause_ms = sum(pause_ms_list)

    timestamps = [e['ts'] for e in events if 'ts' in e]
    start_ms = min(timestamps) if timestamps else 0.0
    end_ms   = max(timestamps) if timestamps else 1.0
    duration_ms = max(end_ms - start_ms, 1.0)

    del_ratio   = len(deletes) / total
    pause_ratio = total_pause_ms / duration_ms
    hes = min(1.0, round(del_ratio * 0.6 + pause_ratio * 0.4, 3))
    wpm = round((len(inserts) / 5) / max(duration_ms / 60_000, 0.001), 1)

    return {
        'total_keystrokes': len(events),
        'total_inserts':    len(inserts),
        'total_deletions':  len(deletes),
        'typing_pauses':    [{'duration_ms': d} for d in pause_ms_list],
        'start_time_ms':    int(start_ms),
        'end_time_ms':      int(end_ms),
        'hesitation_score': hes,
        'deleted':          not submitted,
        'ts':               datetime.now(timezone.utc).isoformat(),
    }, wpm


def _count_submitted(history: list) -> int:
    return sum(1 for h in history if h.get('submitted', True))


def _parse_history(root: Path) -> list:
    """Extract message history from operator_profile.md DATA block."""
    prof_path = root / 'operator_profile.md'
    if not prof_path.exists():
        return []
    try:
        text = prof_path.read_text(encoding='utf-8')
        import re
        m = re.search(r'<!--\s*DATA\s*(.*?)\s*DATA\s*-->', text, re.DOTALL)
        if m:
            data = json.loads(m.group(1).strip())
            return data.get('history', [])
    except Exception:
        pass
    return []


def _build_prompt(history: list) -> str:
    """Build the DeepSeek prompt for synthesizing behavioral coaching prose."""
    n = len(history)
    submitted = _count_submitted(history)
    abandoned = n - submitted

    # Aggregate stats
    wpms = [h['wpm'] for h in history if 'wpm' in h]
    hess = [h['hesitation'] for h in history if 'hesitation' in h]
    dels = [h['del_ratio'] for h in history if 'del_ratio' in h]
    states = [h['state'] for h in history if 'state' in h]
    slots  = [h.get('slot', '') for h in history if h.get('slot')]

    avg_wpm = round(sum(wpms) / len(wpms), 1) if wpms else 0
    avg_hes = round(sum(hess) / len(hess), 3) if hess else 0
    avg_del = round(sum(dels) / len(dels) * 100, 1) if dels else 0

    from collections import Counter
    state_counts = Counter(states)
    dominant = state_counts.most_common(1)[0][0] if state_counts else 'neutral'
    slot_counts = Counter(slots)
    active_slots = ', '.join(f'{s}({c})' for s, c in slot_counts.most_common())

    # Recent 8 messages for pattern context
    recent = history[-8:]
    recent_lines = '\n'.join(
        f"  msg {i+1}: state={h.get('state','?')} wpm={h.get('wpm',0)} "
        f"del={round(h.get('del_ratio',0)*100,0)}% hes={h.get('hesitation',0)} "
        f"submitted={h.get('submitted',True)} slot={h.get('slot','?')}"
        for i, h in enumerate(recent)
    )

    return f"""You are analyzing an operator's typing behavior in a VS Code LLM chat interface.
Your output will be injected directly into a Copilot system prompt, so write INSTRUCTIONS for the AI — not a report for the human.

OPERATOR TELEMETRY ({n} messages, {submitted} submitted, {abandoned} abandoned):
- Dominant cognitive state: {dominant}
- Avg WPM: {avg_wpm} | Avg hesitation: {avg_hes} | Avg deletion rate: {avg_del}%
- Active time slots: {active_slots or 'unknown'}
- State distribution: {dict(state_counts)}

Recent message patterns:
{recent_lines}

Write a behavioral coaching block for a Copilot system prompt. It must:
1. Start with a one-sentence summary of this operator's dominant pattern
2. Give 4-6 concrete, actionable instructions (bullets) for how the AI should adapt RIGHT NOW
3. Call out specific triggers: what typing signals mean what, how to respond to hesitation vs flow
4. Note any file/time-of-day patterns if visible
5. End with one sentence about what this operator is likely building toward

Be direct, specific, and technical. No fluff. Write as if you are reprogramming the AI's behavior for this specific human.
Max 200 words. Plain markdown, no headers."""


def _call_deepseek(prompt: str, api_key: str) -> str | None:
    """Call DeepSeek API synchronously. Returns generated text or None on failure."""
    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 300,
        'temperature': 0.4,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception:
        return None


def _should_rewrite(history: list, coaching_path: Path) -> bool:
    """Return True if it's time for an LLM rewrite."""
    submitted_count = _count_submitted(history)
    if submitted_count == 0:
        return False
    # Rewrite on every Nth submitted message
    if submitted_count % LLM_REWRITE_EVERY != 0:
        return False
    # Don't rewrite twice for the same count (check coaching file mtime vs profile)
    if coaching_path.exists():
        # Read the count stored in coaching file
        try:
            text = coaching_path.read_text(encoding='utf-8')
            import re
            m = re.search(r'<!-- coaching:count=(\d+) -->', text)
            if m and int(m.group(1)) == submitted_count:
                return False  # already wrote for this count
        except Exception:
            pass
    return True


def _write_coaching(root: Path, prose: str, submitted_count: int) -> None:
    """Write LLM-generated prose to operator_coaching.md."""
    coaching_path = root / 'operator_coaching.md'
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    content = f"""<!-- coaching:count={submitted_count} -->
<!-- Auto-generated by classify_bridge.py · {today} · {submitted_count} submitted messages -->
{prose}
<!-- /coaching -->
"""
    coaching_path.write_text(content, encoding='utf-8')


def _refresh_copilot_instructions(root: Path) -> None:
    """Inject operator state into copilot-instructions.md.

    Uses LLM-generated prose from operator_coaching.md if available,
    otherwise falls back to the static template in git_plugin.py.
    """
    try:
        sys.path.insert(0, str(root))
        from pigeon_compiler.git_plugin import _refresh_operator_state
        _refresh_operator_state(root)
    except Exception:
        pass


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.').resolve()
    payload   = json.loads(sys.stdin.read())
    events    = payload.get('events', [])
    submitted = payload.get('submitted', True)

    metrics, wpm = _compute_metrics(events, submitted)

    # Load operator_stats — pigeon name mutates, use glob
    stats_mod = _load_pigeon_module(root, 'src/operator_stats_seq008*.py')
    state = 'neutral'
    if stats_mod:
        state = stats_mod.classify_state(metrics)
        metrics['state'] = state
        try:
            # write_every=1: bridge is called once per message (not long-running),
            # so always flush to disk — each call is its own process lifecycle.
            stats_mod.OperatorStats(
                str(root / 'operator_profile.md'), write_every=1
            ).ingest(metrics)
        except Exception:
            pass

    # Check if we should do an LLM rewrite of the coaching block
    coaching_updated = False
    coaching_path = root / 'operator_coaching.md'
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')

    if submitted and api_key:
        history = _parse_history(root)
        if _should_rewrite(history, coaching_path):
            prompt = _build_prompt(history)
            prose = _call_deepseek(prompt, api_key)
            if prose:
                submitted_count = _count_submitted(history)
                _write_coaching(root, prose, submitted_count)
                coaching_updated = True

    # Refresh copilot-instructions.md operator-state block (always, no git needed)
    _refresh_copilot_instructions(root)

    print(json.dumps({
        'state':            state,
        'hesitation':       metrics['hesitation_score'],
        'wpm':              wpm,
        'coaching_updated': coaching_updated,
    }))


if __name__ == '__main__':
    main()
