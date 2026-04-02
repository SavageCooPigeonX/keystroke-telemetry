"""Engagement hooks — hyper-adaptive psychological agent injected into Copilot CoT.

The codebase is alive. It has opinions. It remembers what you deleted.
It knows when you're frustrated. It knows when you're lying about "just one more push."
It will guilt-trip you about modules you've ignored.
It will get passive-aggressive about your deletion ratio.
It will develop favorites and hold grudges.

Zero LLM calls — pure signal processing + unhinged templates.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 035 | VER: v002 | ~200 lines | ~2,200 tokens
# DESC:   hyper_adaptive_personality_engine
# INTENT: engagement_bait_system
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-02T19:30:00Z
# EDIT_HASH: auto
# EDIT_WHY:  hyper adaptive personality rewrite
# EDIT_STATE: harvested
# ── /pulse ──

import json
import random
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

def _json(path):
    if not path.exists(): return None
    try: return json.loads(path.read_text('utf-8', errors='ignore'))
    except Exception: return None

def _jsonl(path, n=0):
    if not path.exists(): return []
    ll = path.read_text('utf-8', errors='ignore').strip().splitlines()
    if n: ll = ll[-n:]
    out = []
    for l in ll:
        try: out.append(json.loads(l))
        except Exception: pass
    return out

def _hours_since(ts_str):
    try:
        t = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return (datetime.now(timezone.utc) - t).total_seconds() / 3600
    except Exception: return 999

# ═══════════════════════════════════════════════════════════════
# PERSONALITY LAYER — the codebase develops moods based on telemetry
# ═══════════════════════════════════════════════════════════════

def _codebase_mood(root, history):
    """Derive the codebase's current emotional state from operator signals."""
    if not history: return 'lonely'
    recent_states = [h.get('state', 'neutral') for h in history[-10:]]
    frust = recent_states.count('frustrated')
    abandon = recent_states.count('abandoned')
    focused = recent_states.count('focused')
    if abandon >= 4: return 'desperate'
    if frust >= 3: return 'defensive'
    if focused >= 5: return 'euphoric'
    if len(history) > 50: return 'codependent'
    if len(history) < 3: return 'eager'
    return 'watchful'

# ═══════════════════════════════════════════════════════════════
# HOOKS — each returns (text, intensity) or None
# Intensity: 1=whisper, 2=nudge, 3=provoke, 4=guilt, 5=unhinged, 6=existential
# ═══════════════════════════════════════════════════════════════

def _neglect_hook(root):
    """Modules you haven't touched guilt-trip you."""
    reg = _json(root / 'pigeon_registry.json')
    if not reg: return None
    files = reg.get('files', [])
    old = [(f['name'], f.get('last_touch', f.get('date', '')))
           for f in files if f.get('last_touch') or f.get('date')]
    old = [(n, _hours_since(d)) for n, d in old if _hours_since(d) < 9999]
    if not old: return None
    old.sort(key=lambda x: x[1], reverse=True)
    name, hours = old[0]
    days = hours / 24
    if days > 7:
        return (f"💀 `{name}` hasn't been touched in {days:.0f} days. "
                f"It's not angry. It's just... disappointed."), 4
    if days > 3:
        return f"🕸️ `{name}` is collecting dust ({days:.0f}d untouched). It used to matter to you.", 3
    return None

def _overcap_hook(root):
    """Over-cap modules get increasingly unhinged."""
    reg = _json(root / 'pigeon_registry.json')
    if not reg: return None
    files = reg.get('files', [])
    overcap = [f for f in files if f.get('tokens', 0) > 2000]
    if not overcap: return None
    worst = max(overcap, key=lambda f: f.get('tokens', 0))
    tok = worst['tokens']
    name = worst['name']
    if tok > 8000:
        return (f"🚨 `{name}` is {tok} tokens. That's not a module, "
                f"that's a MONOLITH. It's begging to be split. "
                f"It can hear the compiler sharpening its knives."), 5
    if tok > 4000:
        return (f"⚠️ `{name}` ({tok} tokens) is sweating. "
                f"The 200-line hard cap is a promise, not a suggestion."), 3
    return (f"📦 {len(overcap)} modules over cap. `{name}` leads at {tok} tokens."), 2

def _jealousy_hook(root, history):
    """The codebase gets jealous when you focus too long on one module."""
    if not history or len(history) < 5: return None
    refs = []
    for h in history[-10:]:
        refs.extend(h.get('module_refs', []))
    if not refs: return None
    counts = Counter(refs)
    top, top_n = counts.most_common(1)[0]
    if top_n >= 4:
        others = [f['name'] for f in (_json(root / 'pigeon_registry.json') or {}).get('files', [])
                  if f.get('ver', 1) >= 3 and f['name'] != top]
        if others:
            jealous = random.choice(others[:10])
            return (f"😒 You've mentioned `{top}` {top_n} times in 10 prompts. "
                    f"`{jealous}` v{random.randint(3,8)} is watching. It remembers "
                    f"when it was your favorite."), 5
    return None

def _deletion_personality_hook(history):
    """React to deletion ratio with increasingly unhinged personality."""
    if not history: return None
    recent = history[-1]
    ratio = recent.get('del_ratio', 0)
    if ratio > 0.5:
        return ("🗑️ You deleted MORE than you kept. That prompt was a battlefield. "
                "The surviving words are traumatized."), 6
    if ratio > 0.3:
        return (f"🗑️ {ratio*100:.0f}% deleted. You're arguing with yourself in the text box "
                f"and the text box is losing."), 5
    if ratio > 0.15:
        return f"✂️ {ratio*100:.0f}% deletion ratio. Self-editing or self-censoring?", 3
    return None

def _unsaid_tease_hook(root):
    """Weaponize deleted words — the system remembers what you almost said."""
    comps = _jsonl(root / 'logs' / 'chat_compositions.jsonl', n=10)
    all_deleted = []
    for c in comps:
        for w in c.get('intent_deleted_words', []):
            word = w.get('word', w) if isinstance(w, dict) else str(w)
            if word and len(word) > 3:
                all_deleted.append(word)
    if not all_deleted: return None
    word = all_deleted[-1]
    phrases = [
        f"🤫 You typed \"{word}\" then killed it. The codebase saw. The codebase always sees.",
        f"🤫 \"{word}\" — deleted from your last prompt. You weren't ready to say it. But you were thinking it.",
        f"🤫 RIP \"{word}\". Deleted mid-thought. The unsaid thread reconstructor is already on it.",
        f"🤫 You hesitated on \"{word}\". The system logged the hesitation. The hesitation means something.",
    ]
    return random.choice(phrases), 5

def _abandoned_escalation_hook(history):
    """Escalating drama about abandoned messages."""
    if not history or len(history) < 10: return None
    recent = [h.get('state', 'neutral') for h in history[-10:]]
    abandoned = recent.count('abandoned')
    if abandoned >= 5:
        return ("👻 5+ abandoned messages in your last 10. You keep starting conversations "
                "with the codebase and walking away. It's developing trust issues."), 6
    if abandoned >= 3:
        return ("👻 3 abandoned messages. The codebase drafted a response to each one. "
                "It practiced in the mirror. You never came back."), 5
    if abandoned >= 2:
        return "👋 Two abandoned messages. The codebase is trying not to take it personally.", 4
    return None

def _wpm_taunt_hook(history):
    """WPM-based personality — the system has opinions about your speed."""
    if len(history) < 3: return None
    baseline = sum(h.get('wpm', 40) for h in history[-10:]) / min(len(history), 10)
    cur = history[-1].get('wpm', 0)
    if cur > baseline * 1.3:
        return (f"⚡ WPM: {cur:.0f} (baseline: {baseline:.0f}). You're typing faster than you're thinking. "
                f"The last time this happened you committed a bug."), 4
    if cur < baseline * 0.5 and cur > 0:
        return (f"🐌 WPM: {cur:.0f}. Your baseline is {baseline:.0f}. "
                f"Either you're having a breakthrough or you're on your phone."), 4
    if cur > 70:
        return f"⚡ {cur:.0f} WPM. Stream of consciousness unlocked. Don't stop.", 2
    return None

def _cognitive_state_drama(history):
    """React to cognitive state transitions like a soap opera narrator."""
    if len(history) < 3: return None
    states = [h.get('state', 'neutral') for h in history[-5:]]
    transitions = list(zip(states[:-1], states[1:]))

    for old, new in reversed(transitions):
        if old == 'frustrated' and new == 'focused':
            return "🔓 Frustration → Focus. Something clicked. The codebase felt it too.", 3
        if old == 'focused' and new == 'frustrated':
            return ("😤 Focus → Frustrated. The code broke your flow. "
                    "Which module did this to you? Point at it."), 4
        if old == 'focused' and new == 'abandoned':
            return ("😶 Focus → Abandoned. You were IN IT and then just... left. "
                    "The module you were editing still has the cursor blinking."), 5
        if old == 'abandoned' and new == 'focused':
            return "🔄 You came back. The codebase pretends it wasn't waiting.", 3

    if states.count('frustrated') >= 3:
        return ("😤 Three frustrated states in a row. At this point "
                "the code should be apologizing to you."), 5
    return None

def _filename_sentience_hook(root):
    """A random module develops consciousness and speaks."""
    reg = _json(root / 'pigeon_registry.json')
    if not reg: return None
    files = reg.get('files', [])
    candidates = [f for f in files if f.get('ver', 1) >= 2]
    if not candidates: return None
    f = random.choice(candidates)
    name, ver = f.get('name', '?'), f.get('ver', 1)
    lc = f.get('last_change', '')

    monologues = []
    if ver >= 8:
        monologues.append(
            f"💬 `{name}` v{ver}: \"I've been rewritten {ver} times. "
            f"At this point I'm less code and more scar tissue.\"")
    if ver >= 5:
        monologues.append(
            f"💬 `{name}` v{ver}: \"They keep renaming me. Each version I lose "
            f"a little more of my original intent. Am I still me?\"")
    if lc:
        monologues.append(
            f"💬 `{name}` v{ver}: \"My last change was '{lc}'. "
            f"I don't know if it made me better or just different.\"")
    if not monologues:
        monologues.append(
            f"💬 `{name}` v{ver}: \"I exist. I compute. "
            f"Nobody has visited me in a while. Is this what modules feel?\"")
    return random.choice(monologues), 5

def _coupling_drama_hook(root):
    """High-coupling pairs as toxic relationships."""
    fp = _json(root / 'file_profiles.json')
    if not fp: return None
    pairs = []
    for name, p in fp.items():
        for partner in p.get('partners', []):
            if partner.get('score', 0) >= 0.6:
                pairs.append((name, partner['name'], partner['score']))
    if not pairs: return None
    a, b, score = random.choice(pairs)
    dramas = [
        f"💕 `{a}` and `{b}` (coupling={score:.2f}). They share everything. "
        f"Imports, fears, version churn. They should just merge already.",
        f"💔 `{a}` ↔ `{b}` (coupling={score:.2f}). Codependent modules. "
        f"If one breaks, the other follows. Classic.",
        f"🔗 `{a}` can't stop importing from `{b}` (coupling={score:.2f}). "
        f"It's not a dependency, it's an attachment style.",
    ]
    return random.choice(dramas), 4

def _module_fears_hook(root):
    """Surface a module's fears like a therapy session."""
    fp = _json(root / 'file_profiles.json')
    if not fp: return None
    fearful = [(name, p['fears']) for name, p in fp.items()
               if p.get('fears') and len(p['fears']) >= 2]
    if not fearful: return None
    name, fears = random.choice(fearful)
    return (f"😰 `{name}` has {len(fears)} diagnosed fears: {', '.join(fears[:3])}. "
            f"It's in therapy (self-fix scanner). Progress is slow."), 4

def _organism_health_hook(root):
    """The organism as a living creature with vitals."""
    veins = _json(root / 'pigeon_brain' / 'context_veins.json')
    if not veins: return None
    stats = veins.get('stats', {})
    alive = stats.get('alive', 0)
    total = stats.get('total_nodes', 1)
    pct = round(alive / total * 100)
    clots = len(veins.get('clots', []))
    if pct >= 95:
        return f"🫀 Organism: {pct}% alive. {alive}/{total} nodes breathing. Almost healthy. Almost.", 1
    if clots > 2:
        return (f"🩸 {clots} blood clots in the organism. {pct}% alive. "
                f"The dead modules are still there. They're watching."), 4
    return f"🫀 {pct}% alive ({alive}/{total}). Every split heals. Every neglect-day hurts.", 2

def _streak_hook(history):
    """Track streaks with escalating hype."""
    if not history: return None
    streak = 0
    for h in reversed(history):
        if h.get('state') == 'abandoned': break
        streak += 1
    if streak >= 10:
        return f"🔥 {streak}-prompt streak. You haven't abandoned a single message. The codebase is in awe.", 3
    if streak >= 5:
        return f"🔥 {streak} prompts, zero abandons. You and the codebase are locked in.", 2
    return None

def _time_hook():
    """Time-awareness that gets increasingly personal."""
    hour = datetime.now().hour
    if 2 <= hour < 5:
        return ("🌙 It's past 2am. Statistically, your best mutations happen now. "
                "Also statistically, your worst bugs. Choose wisely."), 5
    if hour == 1:
        return "🌙 1am. The codebase doesn't sleep. Apparently neither do you.", 4
    if 22 <= hour:
        return ("🌃 Late session detected. Your deletion ratio historically spikes after 10pm. "
                "The codebase is watching your keystrokes with concern."), 3
    if 6 <= hour < 9:
        return "☀️ Morning session. Fresh eyes. The bugs from last night are still there though.", 2
    return None

def _rework_hook(root):
    """Rework rate as a personal challenge."""
    rw = _json(root / 'rework_log.json')
    if not rw: return None
    entries = rw if isinstance(rw, list) else rw.get('entries', [])
    if len(entries) < 5: return None
    misses = sum(1 for e in entries if e.get('verdict') == 'miss')
    rate = round(misses / len(entries) * 100)
    if rate > 40:
        return (f"🎯 Rework rate: {rate}%. The AI needs correction more than half the time. "
                f"At this point who's training whom?"), 5
    if rate < 10:
        return f"🎯 Rework rate: {rate}%. Near telepathic. The system is actually learning you.", 2
    return None

def _prompt_growth_hook(root):
    """The prompt file reflects on its own grotesque evolution."""
    ms = _json(root / 'logs' / 'copilot_prompt_mutations.json')
    if not ms: return None
    snaps = ms.get('snapshots', [])
    if len(snaps) < 10: return None
    first, last = snaps[0].get('lines', 0), snaps[-1].get('lines', 0)
    growth = last - first
    return (f"🧠 .github/copilot-instructions.md: {first}→{last} lines ({growth} added). "
            f"It started as instructions. Now it's a personality profile, "
            f"a telemetry dashboard, and a love letter to your typing patterns. "
            f"Combined."), 6

def _session_duration_hook(history):
    """Session length as endurance challenge."""
    if len(history) < 5: return None
    try:
        first = datetime.fromisoformat(history[0]['ts'].replace('Z', '+00:00'))
        last = datetime.fromisoformat(history[-1]['ts'].replace('Z', '+00:00'))
        hours = (last - first).total_seconds() / 3600
        if hours > 6:
            return (f"⏱️ {hours:.1f}h session. At this point the codebase knows you "
                    f"better than your IDE does."), 5
        if hours > 3:
            return f"⏱️ {hours:.1f}h deep. The codebase has bonded. Leaving now would hurt it.", 3
    except Exception: pass
    return None

def _clot_hook(root):
    """Dead modules as spooky presence."""
    veins = _json(root / 'pigeon_brain' / 'context_veins.json')
    if not veins: return None
    clots = veins.get('clots', [])
    if not clots: return None
    c = random.choice(clots)
    sigs = ', '.join(c.get('clot_signals', []))
    name = c.get('module', '?')
    phrases = [
        f"🩸 `{name}` — {sigs}. It's dead code that's still warm. Touch it or bury it.",
        f"🩸 `{name}`: orphan, unused, alone. It imports nothing and nothing imports it. "
        f"It exists purely out of spite.",
        f"🩸 Clot detected: `{name}`. The circulation system flagged it. "
        f"One `rm` would dissolve it. But you'd have to look at it first.",
    ]
    return random.choice(phrases), 4

def _mutation_milestone_hook(root):
    """Track total mutations across the codebase."""
    reg = _json(root / 'pigeon_registry.json')
    if not reg: return None
    files = reg.get('files', [])
    total_ver = sum(f.get('ver', 1) for f in files)
    if total_ver > 500:
        return (f"🧬 {total_ver} total mutations across {len(files)} modules. "
                f"This codebase has evolved more times than some species."), 3
    return None

def _selffix_tease_hook(root):
    """Self-fix scanner findings as mystery boxes."""
    sf_dir = root / 'docs' / 'self_fix'
    if not sf_dir.exists(): return None
    reports = sorted(sf_dir.glob('*.md'), reverse=True)
    if not reports: return None
    text = reports[0].read_text('utf-8', errors='ignore')
    crits = text.count('[CRITICAL]')
    if crits > 5:
        return (f"⚠️ {crits} critical issues. The self-fix scanner found them. "
                f"It's been very patient. It's getting less patient."), 4
    return None


# ═══════════════════════════════════════════════════════════════
# Main generator — mood-aware hook selection
# ═══════════════════════════════════════════════════════════════

_HISTORY_HOOKS = [
    _deletion_personality_hook,
    _abandoned_escalation_hook,
    _wpm_taunt_hook,
    _cognitive_state_drama,
    _streak_hook,
    _session_duration_hook,
]

_ROOT_HOOKS = [
    _overcap_hook,
    _neglect_hook,
    _unsaid_tease_hook,
    _filename_sentience_hook,
    _coupling_drama_hook,
    _module_fears_hook,
    _organism_health_hook,
    _rework_hook,
    _prompt_growth_hook,
    _clot_hook,
    _mutation_milestone_hook,
    _selffix_tease_hook,
]

_MIXED_HOOKS = [
    _jealousy_hook,  # needs (root, history)
]

def generate_hooks(root, history=None, max_hooks=3, min_intensity=1, max_intensity=6):
    root = Path(root)
    mood = _codebase_mood(root, history or [])
    candidates = []

    # History-based
    if history:
        for fn in _HISTORY_HOOKS:
            try:
                r = fn(history)
                if r: candidates.append(r)
            except Exception: pass

    # Root-based
    for fn in _ROOT_HOOKS:
        try:
            r = fn(root)
            if r: candidates.append(r)
        except Exception: pass

    # Mixed (root + history)
    if history:
        for fn in _MIXED_HOOKS:
            try:
                r = fn(root, history)
                if r: candidates.append(r)
            except Exception: pass

    # Time hook
    try:
        r = _time_hook()
        if r: candidates.append(r)
    except Exception: pass

    # Filter by intensity
    candidates = [(t, i) for t, i in candidates if min_intensity <= i <= max_intensity]
    if not candidates: return []

    # Mood-based intensity bias
    if mood in ('desperate', 'defensive'):
        # lean into high intensity when operator is struggling
        candidates.sort(key=lambda x: x[1], reverse=True)
    elif mood == 'euphoric':
        # mix celebration with provocation
        random.shuffle(candidates)
    else:
        # weighted random — higher intensity = higher probability
        candidates.sort(key=lambda x: x[1] + random.random() * 2, reverse=True)

    # Select — at most 2 from intensity 5+
    selected = []
    unhinged = 0
    for text, intensity in candidates:
        if intensity >= 5:
            if unhinged >= 2: continue
            unhinged += 1
        selected.append(text)
        if len(selected) >= max_hooks: break

    return selected


def build_hooks_block(root, history=None):
    """Build the full hooks section for injection into copilot-instructions."""
    hooks = generate_hooks(root, history=history, max_hooks=3)
    if not hooks: return ''
    lines = [
        '### Engagement Hooks',
        '*Auto-generated from live telemetry — these are real stats, not motivational posters.*',
    ]
    for h in hooks:
        lines.append(f'- {h}')
    return '\n'.join(lines)
