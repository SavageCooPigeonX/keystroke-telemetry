"""Conversation trajectory cache — per-prompt cognitive state snapshots.

Reads chat_compositions.jsonl (operator prompts) and ai_responses.jsonl (Copilot
responses) to build a rolling conversational context. Each prompt is a discrete
cognitive packet with its own state, intent, deleted words, and rewrites.

The trajectory is the PRIMARY context for thought completion — not keywords,
not file matching. The thought completer predicts what the operator will say
next based on where the conversation IS, not what modules exist.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

from .tc_constants_seq001_v001 import ROOT

_CACHE_PATH = ROOT / 'logs' / 'conversation_trajectory.json'
_trajectory_cache: dict | None = None
_trajectory_ts: float = 0
_last_comp_count: int = 0
_last_resp_count: int = 0


def _load_recent_compositions(n: int = 8) -> list[dict]:
    """Load last N chat compositions with cognitive signals."""
    path = ROOT / 'logs' / 'chat_compositions.jsonl'
    if not path.exists():
        return []
    try:
        lines = path.read_text('utf-8', errors='ignore').strip().splitlines()
        entries = []
        for line in lines[-n:]:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except Exception:
                continue
            cs = raw.get('chat_state', {})
            signals = cs.get('signals', {}) if isinstance(cs, dict) else {}
            entries.append({
                'ts': raw.get('ts', ''),
                'text': raw.get('final_text', '')[:500],
                'state': cs.get('state', 'unknown') if isinstance(cs, dict) else 'unknown',
                'wpm': signals.get('wpm', 0),
                'del_ratio': raw.get('deletion_ratio', 0),
                'deleted_words': [
                    d.get('word', '') if isinstance(d, dict) else str(d)
                    for d in raw.get('deleted_words', [])[-6:]
                ],
                'rewrites': [
                    f"{r.get('old', '')}→{r.get('new', '')}"[:80]
                    if isinstance(r, dict) else str(r)[:80]
                    for r in raw.get('rewrites', [])[-4:]
                ],
                'hesitations': len(raw.get('hesitation_windows', [])),
                'duration_ms': raw.get('duration_ms', 0),
            })
        return entries
    except Exception:
        return []


def _load_recent_responses(n: int = 8) -> list[dict]:
    """Load last N AI responses paired with prompts."""
    path = ROOT / 'logs' / 'ai_responses.jsonl'
    if not path.exists():
        return []
    try:
        lines = path.read_text('utf-8', errors='ignore').strip().splitlines()
        entries = []
        for line in lines[-n:]:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except Exception:
                continue
            entries.append({
                'ts': raw.get('ts', ''),
                'prompt': raw.get('prompt', '')[:300],
                'response': raw.get('response', '')[:600],
                'request_idx': raw.get('request_idx', 0),
            })
        return entries
    except Exception:
        return []


def _pair_prompt_response(comps: list[dict], resps: list[dict]) -> list[dict]:
    """Pair compositions with AI responses by matching prompt text.
    
    Both compositions and responses contain the operator's prompt text.
    Match them by comparing the first ~50 chars of the prompt.
    Response timestamps can be BEFORE composition timestamps (response
    is captured when Copilot finishes, composition when operator submits next).
    """
    paired = []
    # Build a lookup: normalize first 50 chars of response prompt → response text
    resp_lookup: list[tuple[str, str]] = []
    for r in resps:
        key = r.get('prompt', '').strip()[:50].lower()
        resp_lookup.append((key, r.get('response', '')[:600]))

    for comp in comps:
        turn = {
            'prompt': comp['text'],
            'state': comp['state'],
            'wpm': comp['wpm'],
            'del_ratio': comp['del_ratio'],
            'deleted_words': comp['deleted_words'],
            'rewrites': comp['rewrites'],
            'hesitations': comp['hesitations'],
            'duration_ms': comp['duration_ms'],
            'response': '',
        }
        # Match by first 50 chars of prompt text
        comp_key = comp['text'].strip()[:50].lower()
        if comp_key:
            best_score = 0
            best_resp = ''
            for rkey, rtext in resp_lookup:
                if not rkey:
                    continue
                # Count matching words in first ~50 chars
                comp_words = set(comp_key.split())
                resp_words = set(rkey.split())
                overlap = len(comp_words & resp_words)
                # Require at least 3 matching words or 60% overlap
                min_len = min(len(comp_words), len(resp_words))
                if overlap >= max(3, min_len * 0.6) and overlap > best_score:
                    best_score = overlap
                    best_resp = rtext
            turn['response'] = best_resp
        paired.append(turn)
    return paired


def _detect_state_transitions(turns: list[dict]) -> list[dict]:
    """Detect cognitive state transitions between prompts."""
    transitions = []
    prev_state = None
    for i, turn in enumerate(turns):
        state = turn.get('state', 'unknown')
        if prev_state and state != prev_state:
            transitions.append({
                'from': prev_state,
                'to': state,
                'at_turn': i,
                'trigger_prompt': turn['prompt'][:100],
            })
        prev_state = state
    return transitions


def build_trajectory() -> dict:
    """Build the conversation trajectory from live data.

    Returns a dict with: turns (paired prompt/response/state), transitions
    (cognitive shifts), suppressed_intent (accumulated deleted words),
    and conversation_phase (inferred from trajectory shape).
    """
    global _trajectory_cache, _trajectory_ts, _last_comp_count, _last_resp_count
    now = time.time()

    # Check if data has changed — avoid rebuilding on every call
    comp_path = ROOT / 'logs' / 'chat_compositions.jsonl'
    resp_path = ROOT / 'logs' / 'ai_responses.jsonl'
    comp_count = 0
    resp_count = 0
    try:
        if comp_path.exists():
            comp_count = comp_path.read_text('utf-8', errors='ignore').count('\n')
        if resp_path.exists():
            resp_count = resp_path.read_text('utf-8', errors='ignore').count('\n')
    except Exception:
        pass

    if (_trajectory_cache and
            comp_count == _last_comp_count and
            resp_count == _last_resp_count and
            (now - _trajectory_ts) < 30):
        return _trajectory_cache

    comps = _load_recent_compositions(8)
    resps = _load_recent_responses(12)  # more responses than comps to improve pairing
    turns = _pair_prompt_response(comps, resps)
    transitions = _detect_state_transitions(turns)

    # Accumulate suppressed intent — all deleted words across recent turns
    suppressed = []
    for t in turns:
        for w in t.get('deleted_words', []):
            if w and len(w) > 2:
                suppressed.append(w)

    # Infer conversation phase from trajectory shape
    phase = _infer_phase(turns, transitions)

    trajectory = {
        'turns': turns[-6:],  # last 6 prompt/response pairs
        'transitions': transitions,
        'suppressed_intent': suppressed[-10:],
        'phase': phase,
        'turn_count': len(comps),
    }

    _trajectory_cache = trajectory
    _trajectory_ts = now
    _last_comp_count = comp_count
    _last_resp_count = resp_count
    return trajectory


def _infer_phase(turns: list[dict], transitions: list[dict]) -> str:
    """Infer what phase of conversation the operator is in."""
    if not turns:
        return 'starting'
    recent = turns[-3:]
    # High deletion across recent turns → iterating/frustrated
    avg_del = sum(t.get('del_ratio', 0) for t in recent) / len(recent)
    avg_hes = sum(t.get('hesitations', 0) for t in recent) / len(recent)
    # Fast WPM + low deletion → flowing
    avg_wpm = sum(t.get('wpm', 0) for t in recent) / len(recent)

    if avg_del > 0.3:
        return 'iterating'  # heavy editing — refining approach
    if avg_hes > 2:
        return 'deliberating'  # lots of pauses — thinking hard
    if avg_wpm > 60 and avg_del < 0.1:
        return 'flowing'  # fast and confident
    if len(transitions) >= 2:
        return 'shifting'  # cognitive state keeps changing
    if len(recent) >= 2 and all(t.get('state') == 'focused' for t in recent):
        return 'deep_focus'  # locked in
    return 'exploring'


def format_trajectory_for_prompt(trajectory: dict) -> str:
    """Format the conversation trajectory for injection into Gemini prompt."""
    turns = trajectory.get('turns', [])
    if not turns:
        return ''

    parts = []

    # Conversation turns — this is the PRIMARY context
    parts.append('CONVERSATION (last prompt→response pairs — this is what they\'re reacting to):')
    for i, t in enumerate(turns):
        state_tag = f'[{t["state"]}]' if t.get('state', 'unknown') != 'unknown' else ''
        prompt = t.get('prompt', '')
        response = t.get('response', '')

        parts.append(f'  TURN {i+1} {state_tag}:')
        parts.append(f'    operator: {prompt[:300]}')
        if response:
            # Truncate response but keep enough to understand the trajectory
            parts.append(f'    copilot: {response[:400]}')
        if t.get('deleted_words'):
            parts.append(f'    [deleted: {", ".join(t["deleted_words"])}]')
        if t.get('rewrites'):
            parts.append(f'    [rewrote: {"; ".join(t["rewrites"][:2])}]')

    # State transitions — where the cognitive shifts happened
    transitions = trajectory.get('transitions', [])
    if transitions:
        trans_str = ' → '.join(
            f'{t["from"]}→{t["to"]}' for t in transitions[-3:]
        )
        parts.append(f'STATE SHIFTS: {trans_str}')

    # Suppressed intent — things they typed then deleted across conversation
    suppressed = trajectory.get('suppressed_intent', [])
    if suppressed:
        parts.append(f'SUPPRESSED INTENT (deleted across conversation): {", ".join(suppressed)}')

    # Conversation phase
    phase = trajectory.get('phase', 'unknown')
    if phase != 'unknown':
        parts.append(f'CONVERSATION PHASE: {phase}')

    return '\n'.join(parts)
