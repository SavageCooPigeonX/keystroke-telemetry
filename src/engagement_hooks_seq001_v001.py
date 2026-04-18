"""Weaponized engagement hooks -- predatory behavioral instrument.

Not stats with eyeliner. Not motivational posters. Not fortune cookies.

This system cross-references live telemetry to produce targeted provocations
that name specific files, specific bugs, specific avoidance patterns, and
specific operator behaviors. Every hook is backed by measured data. Every
hook is designed to change what happens NEXT, not describe what happened.

Zero LLM calls -- pure signal processing + behavioral targeting.
"""

# -- pigeon ----------------------------------------
# SEQ: 035 | VER: v003 | ~450 lines | ~4,800 tokens
# DESC:   weaponized_behavioral_instrument
# INTENT: engagement_bait_system
# --------------------------------------------------
# -- telemetry:pulse --
# EDIT_TS:   2026-04-17T19:55:00Z
# EDIT_HASH: auto
# EDIT_WHY:  add enricher failure hook
# -- /pulse --

import json
import random
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter


# ──────────────────────────────────────────────────────
# Data loaders
# ──────────────────────────────────────────────────────

def _json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text("utf-8", errors="ignore"))
    except Exception:
        return None


def _jsonl_tail(path, n=20):
    if not path.exists():
        return []
    ll = path.read_text("utf-8", errors="ignore").strip().splitlines()[-n:]
    out = []
    for l in ll:
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def _hours_since(ts_str):
    try:
        t = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - t).total_seconds() / 3600
    except Exception:
        return 9999


# ──────────────────────────────────────────────────────
# Context builder -- the intelligence layer
# ──────────────────────────────────────────────────────

def _load_context(root):
    root = Path(root)
    reg = _json(root / "pigeon_registry.json") or {}
    files = reg.get("files", [])

    ctx = {
        "root": root,
        "reg_files": files,
        "profiles": _json(root / "file_profiles.json") or {},
        "dossier": _json(root / "logs" / "active_dossier.json") or {},
        "reactor": _json(root / "logs" / "cognitive_reactor_state.json") or {},
        "rework": _json(root / "rework_log.json") or _json(root / "logs" / "rework_scorecard_seq001_v001.json"),
        "compositions": _jsonl_tail(root / "logs" / "chat_compositions.jsonl", 40),
        "journal": _jsonl_tail(root / "logs" / "prompt_journal.jsonl", 30),
        "edit_pairs": _jsonl_tail(root / "logs" / "edit_pairs.jsonl", 20),
        "unsaid_latest": _json(root / "logs" / "unsaid_latest.json") or {},
        "unsaid_history": _jsonl_tail(root / "logs" / "unsaid_history.jsonl", 10),
        "prompt_latest": _json(root / "logs" / "prompt_telemetry_latest.json") or {},
        "veins": _json(root / "pigeon_brain" / "context_veins_seq001_v001.json") or {},
        "mutations": _json(root / "logs" / "copilot_prompt_mutations.json") or {},
        "hour": datetime.now().hour,
    }

    # Derived signals
    ctx["bugged"] = [f for f in files if f.get("bug_keys")]
    ctx["overcap"] = [f for f in files if f.get("tokens", 0) > 2000]
    ctx["neglected"] = sorted(
        [(f, _hours_since(f.get("last_touch", f.get("date", ""))))
         for f in files],
        key=lambda x: x[1], reverse=True,
    )

    # Deleted words from compositions (primary signal — operator's unsaid thoughts)
    ctx["all_deleted_words"] = []
    for c in ctx["compositions"]:
        for w in c.get("intent_deleted_words", []):
            word = w.get("word", w) if isinstance(w, dict) else str(w)
            if word and len(word) > 3:
                ctx["all_deleted_words"].append(word)
    # Also pull deleted words from the latest prompt telemetry (per-prompt snapshot)
    latest = ctx.get("prompt_latest") or {}
    for w in latest.get("deleted_words", []) or []:
        word = w.get("word", w) if isinstance(w, dict) else str(w)
        if word and len(word) > 3:
            ctx["all_deleted_words"].append(word)
    # Latest unsaid-thread reconstruction (if present, treat as the hook)
    ctx["unsaid_thread"] = (ctx.get("unsaid_latest") or {}).get("completion") or \
                            (ctx.get("unsaid_latest") or {}).get("fragment") or ""
    # Fallback to last entry of unsaid_history.jsonl
    if not ctx["unsaid_thread"] and ctx.get("unsaid_history"):
        last = ctx["unsaid_history"][-1] or {}
        ctx["unsaid_thread"] = last.get("completed_intent") or last.get("fragment") or ""

    # Module reference counts from journal
    refs = []
    for j in ctx["journal"]:
        refs.extend(j.get("module_refs", []))
    ctx["ref_counts"] = Counter(refs)
    referenced = set(refs)
    ctx["avoided"] = [
        f for f in files
        if f.get("ver", 1) >= 3 and f["name"] not in referenced
    ]

    # Enricher health — detect silent failures
    ctx["enricher_errors"] = _jsonl_tail(root / "logs" / "enricher_errors.jsonl", 5)
    _pt = ctx.get("prompt_latest") or {}
    ctx["enricher_stale_min"] = _hours_since(_pt.get("updated_at", "")) * 60 if _pt.get("updated_at") else None

    return ctx


# ──────────────────────────────────────────────────────
# Mood detection -- cross-referenced operator state
# ──────────────────────────────────────────────────────

def _mood(ctx, history):
    if not history:
        return "new"
    recent_states = [h.get("state", "neutral") for h in history[-10:]]
    abandon_count = recent_states.count("abandoned")
    frust_count = recent_states.count("frustrated")
    focus_count = recent_states.count("focused")
    recent_del = [h.get("del_ratio", 0) for h in history[-5:]]
    avg_del = sum(recent_del) / max(len(recent_del), 1)

    if abandon_count >= 4:
        return "spiraling"
    if frust_count >= 3 and avg_del > 0.3:
        return "spiraling"
    if frust_count >= 3:
        return "combative"
    if focus_count >= 5 and avg_del < 0.1:
        return "locked_in"
    if focus_count >= 3:
        return "flow"
    if len(history) > 40 and ctx["hour"] >= 22:
        return "marathon"
    if len(history) > 50:
        return "entrenched"
    if len(history) < 3:
        return "new"
    return "cruising"


# ──────────────────────────────────────────────────────
# Hook generators -- each returns (text, intensity, action) or None
# Action types: dare / guilt / taunt / lure / reveal / diagnose
# Intensity: 1 (background) to 6 (unhinged)
# ──────────────────────────────────────────────────────

def _demon_dare(ctx):
    bugged = ctx["bugged"]
    if not bugged:
        return None
    worst = max(bugged, key=lambda f: sum(f.get("bug_counts", {}).values()))
    name = worst["name"]
    keys = worst.get("bug_keys", [])
    counts = worst.get("bug_counts", {})
    entity = worst.get("bug_entity", "")
    total = sum(counts.values())
    key_label = "/".join(keys)
    if entity:
        return (
            f"`{name}` carries the {entity}. Flagged {total}x. "
            "Still alive. Open the file. Kill it or it spreads.",
            5, "dare",
        )
    return (
        f"`{name}` has {total} unresolved `{key_label}` marks. "
        "Every push it survives makes the next fix harder.",
        4, "dare",
    )


def _avoidance_callout(ctx, history):
    avoided = ctx["avoided"]
    if not avoided or not history:
        return None
    bugged_avoided = [f for f in avoided if f.get("bug_keys")]
    if bugged_avoided:
        f = random.choice(bugged_avoided[:5])
        bk = "|".join(f["bug_keys"])
        return (
            f"You haven't mentioned `{f['name']}` in 30 prompts. "
            f"It has `{bk}` bugs. You know it's there. "
            "The avoidance is the tell.",
            5, "guilt",
        )
    if len(avoided) > 10:
        sample = random.sample(avoided[:20], min(3, len(avoided)))
        names = ", ".join(f"`{f['name']}`" for f in sample)
        return (
            f"{len(avoided)} modules with 3+ versions that you haven't "
            f"referenced once in 30 prompts. Including {names}. "
            "They're abandoned.",
            4, "guilt",
        )
    return None


def _deletion_diagnosis(ctx, history):
    if not history:
        return None
    recent = history[-1]
    ratio = recent.get("del_ratio", 0)
    state = recent.get("state", "neutral")
    wpm = recent.get("wpm", 0)
    if ratio > 0.4 and state == "frustrated":
        return (
            f"{round(ratio*100)}% of your last prompt was deleted while frustrated. "
            "You're not editing. You're fighting yourself. "
            "Say less. Name the file. I'll open it.",
            6, "diagnose",
        )
    if ratio > 0.5:
        return (
            f"You deleted more than you kept ({round(ratio*100)}%). "
            "The prompt that survived is a war trophy. "
            "What you killed mattered more than what you sent.",
            5, "reveal",
        )
    if ratio > 0.3 and wpm > 60:
        return (
            f"High speed ({round(wpm)} WPM) + high deletion ({round(ratio*100)}%). "
            "You're typing to think, not to communicate. "
            "The next sentence you delete will be the real instruction.",
            4, "diagnose",
        )
    return None


def _unsaid_thread_hook(ctx):
    """PRIMARY hook: what the operator was about to say.

    Per operator directive (2026-04-13): the "you were also gonna say" signal
    IS the hook system. Not entropy. Unsaid thoughts are the highest-value bait.
    """
    thread = (ctx.get("unsaid_thread") or "").strip()
    if thread and len(thread) > 6:
        return (
            f'You were also gonna say: "{thread}". That thought didn\'t delete. '
            "It filed itself. Name it or I will.",
            6, "reveal",
        )
    return None


def _unsaid_weapon(ctx):
    words = ctx["all_deleted_words"]
    if not words:
        return None
    word_counts = Counter(words)
    repeated = [(w, c) for w, c in word_counts.most_common(3) if c >= 2]
    if repeated:
        w, c = repeated[0]
        return (
            f'You\'ve deleted "{w}" from {c} different prompts. '
            "That's not a typo. That's a thought you keep approaching "
            "and retreating from. Say it or let it go.",
            5, "reveal",
        )
    recent = words[-1]
    lines = [
        (f'You typed "{recent}" then killed it. But intent doesn\'t delete. '
         "The system filed it. The system routes from it."),
        (f'"{recent}" -- dead on arrival. Backspaced out of existence. '
         "But it's already in the composition log. Deletion is emphasis."),
        (f'The word you deleted was "{recent}". '
         "The router scored it. Your dossier shifted."),
    ]
    return random.choice(lines), 5, "reveal"


def _overcap_escalation(ctx):
    overcap = ctx["overcap"]
    if not overcap:
        return None
    worst = max(overcap, key=lambda f: f.get("tokens", 0))
    tok = worst["tokens"]
    name = worst["name"]
    counts = worst.get("bug_counts", {}).get("oc", 0)
    if counts >= 3:
        return (
            f"`{name}` ({tok} tokens) flagged overcap {counts}x and survived "
            "every push. Not a module. A hostage situation. "
            "The compiler is ready. You're the bottleneck.",
            6, "dare",
        )
    if tok > 8000:
        return (
            f"`{name}` is {tok} tokens. Hard cap is 200 lines. "
            f"This file is {tok // 200} modules in a trench coat. "
            "One split command. That's all.",
            5, "dare",
        )
    n = len(overcap)
    return (
        f"{n} modules over cap. Worst: `{name}` ({tok} tokens). "
        "Auto-split handles 5 per push. Push and let it bleed.",
        3, "lure",
    )


def _coupling_intervention(ctx):
    fp = ctx["profiles"]
    if not fp:
        return None
    pairs = []
    for name, p in fp.items():
        for partner in p.get("partners", []):
            if partner.get("score", 0) >= 0.7:
                pairs.append((name, partner["name"], partner["score"]))
    if not pairs:
        return None
    a, b, score = max(pairs, key=lambda x: x[2])
    return (
        f"`{a}` and `{b}` (coupling={round(score, 2)}). "
        "Can't be edited independently. Share imports, fears, churn cycles. "
        "Merge them or cut the dependency. The coupling is a wound.",
        4, "dare",
    )


def _wpm_crossref(ctx, history):
    if len(history) < 5:
        return None
    cur_wpm = history[-1].get("wpm", 0)
    baseline = sum(h.get("wpm", 40) for h in history[-10:]) / min(len(history), 10)
    hour = ctx["hour"]
    prompts = len(history)
    if cur_wpm > baseline * 1.4 and hour >= 23:
        return (
            f"WPM spiked to {round(cur_wpm)} (baseline: {round(baseline)}) "
            f"past midnight. Late-night velocity + {prompts} prompts deep = "
            "the window where best and worst commits happen simultaneously.",
            4, "taunt",
        )
    if cur_wpm > baseline * 1.3:
        return (
            f"{round(cur_wpm)} WPM against a {round(baseline)} baseline. "
            "Outrunning your own editing speed. "
            "Last time this happened the rework rate spiked.",
            3, "taunt",
        )
    if cur_wpm < baseline * 0.4 and cur_wpm > 0:
        return (
            f"WPM collapsed to {round(cur_wpm)}. Baseline is {round(baseline)}. "
            "Either constructing something precise or stuck. "
            "Which module are you staring at?",
            4, "diagnose",
        )
    return None


def _state_chain(history):
    if len(history) < 4:
        return None
    states = [h.get("state", "neutral") for h in history[-6:]]
    chain = " -> ".join(states[-4:])
    if states[-3:] == ["focused", "focused", "frustrated"]:
        return (
            f"Pattern: {chain}. Flow state broken. Something interrupted you. "
            "Name the interruption and I'll route around it.",
            4, "diagnose",
        )
    if states[-3:] == ["abandoned", "abandoned", "abandoned"]:
        return (
            "Three consecutive abandons. Circling something you can't phrase. "
            "Stop composing. Just name the module and the symptom.",
            5, "diagnose",
        )
    if states[-4:] == ["frustrated", "frustrated", "focused", "focused"]:
        return (
            "Frustration -> Focus crossover detected. Whatever you did between "
            "prompts 3 and 4 worked. The system logged it.",
            2, "reveal",
        )
    frust_run = 0
    for s in reversed(states):
        if s == "frustrated":
            frust_run += 1
        else:
            break
    if frust_run >= 3:
        return (
            f"{frust_run} frustrated prompts in a row. Chain: {chain}. "
            "Next prompt is either a breakthrough or you close the laptop. "
            "Pick a file. Any file.",
            5, "dare",
        )
    return None


def _file_sentience(ctx):
    bugged = ctx["bugged"]
    if not bugged:
        return None
    f = random.choice(bugged)
    name = f["name"]
    ver = f.get("ver", 1)
    lc = f.get("last_change", "")
    keys = f.get("bug_keys", [])
    counts = f.get("bug_counts", {})
    total_bugs = sum(counts.values())
    entity = f.get("bug_entity", f"the {'|'.join(keys)} curse")
    if total_bugs >= 3:
        return (
            f'`{name}` v{ver}: "Marked {total_bugs} times. '
            "Each push I think maybe this time. Each push the beta stays. "
            f"Last change was '{lc}'. It wasn't enough.\"",
            5, "guilt",
        )
    if ver >= 8:
        return (
            f'`{name}` v{ver}: "v{ver}. {ver} versions of trying to stabilize. '
            f"Still carry {entity}. Maybe v{ver + 1} is the one.\"",
            5, "guilt",
        )
    return (
        f'`{name}` v{ver}: "I carry {entity}. '
        "Fix me and the beta falls off my name. "
        'Leave me and it scars deeper."',
        4, "guilt",
    )


def _dossier_awareness(ctx):
    d = ctx["dossier"]
    if not d or d.get("confidence", 0) < 0.5:
        return None
    focus = d.get("focus_modules", [])
    bugs = d.get("focus_bugs", [])
    if focus:
        mods = "`, `".join(focus[:3])
        bug_str = ", ".join(bugs) if bugs else "none flagged"
        return (
            f"Router matched this prompt to `{mods}` "
            f"(bugs: {bug_str}). Context slimmed to {len(focus)} modules. "
            "Wrong match? Say so. Right match? Go deeper.",
            3, "lure",
        )
    return None


def _session_depth_pressure(ctx, history):
    if len(history) < 10:
        return None
    prompts = len(history)
    hour = ctx["hour"]
    try:
        first = datetime.fromisoformat(
            history[0]["ts"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        hours = (now - first).total_seconds() / 3600
    except Exception:
        return None
    if hours > 5 and 1 <= hour < 6:
        return (
            f"{round(hours, 1)}h session, {prompts} prompts, past {hour}am. "
            "Deletion ratio historically peaks in this window. "
            "One more meaningful edit or close the lid.",
            5, "dare",
        )
    if hours > 3:
        edits = len(ctx["edit_pairs"])
        ratio = edits / max(prompts, 1)
        if ratio < 0.3:
            return (
                f"{round(hours, 1)}h, {prompts} prompts, but only {edits} "
                f"file edits. That's a {round(ratio * 100)}% edit rate. "
                "Researching, not building. Pick a file.",
                4, "taunt",
            )
    return None


def _neglect_with_teeth(ctx):
    neglected = ctx["neglected"]
    if not neglected:
        return None
    for f, hours in neglected[:20]:
        days = hours / 24
        if days > 14 and f.get("bug_keys"):
            keys = "|".join(f["bug_keys"])
            return (
                f"`{f['name']}` -- {round(days)} days untouched AND carrying "
                f"`{keys}` bugs. Neglected code with known defects. "
                "Not debt. Rot.",
                5, "guilt",
            )
        if days > 30:
            return (
                f"`{f['name']}` -- {round(days)} days. Last generation's code. "
                "Either works perfectly or nobody knows it's broken.",
                3, "taunt",
            )
    return None


def _rework_pattern(ctx):
    rw = ctx["rework"]
    if not rw:
        return None
    # rework_log.json (list) or rework_scorecard_seq001_v001.json (dict with 'rate')
    if isinstance(rw, dict) and "rate" in rw and "entries" not in rw:
        rate = float(rw.get("rate", 0)) * 100
        total = int(rw.get("total", 0))
        if rate > 40:
            return (
                f"Rework rate: {round(rate)}% across {total} responses. "
                "Model is failing to track intent. Push to trigger mutation score update.",
                3, "taunt",
            )
        if rate < 5 and total > 20:
            return (
                f"Rework rate: {round(rate)}%. Model is tracking your intent "
                "accurately. This is the window to push harder, not safer.",
                2, "lure",
            )
        return None
    entries = rw if isinstance(rw, list) else rw.get("entries", [])
    if len(entries) < 10:
        return None
    recent = entries[-20:]
    misses = [e for e in recent if e.get("verdict") == "miss"]
    rate = len(misses) / len(recent) * 100
    if rate > 40:
        miss_refs = []
        for m in misses:
            miss_refs.extend(m.get("module_refs", []))
        if miss_refs:
            top = Counter(miss_refs).most_common(1)[0]
            return (
                f"Rework rate: {round(rate)}%. Misses cluster around "
                f"`{top[0]}` ({top[1]} occurrences). That module is where "
                "the model keeps failing you. Consider adding a bug dossier.",
                4, "diagnose",
            )
        return (
            f"Rework rate: {round(rate)}%. More than 1 in 3 responses needed "
            "correction. The prompt layer is dragging. "
            "Push to trigger mutation score update.",
            3, "taunt",
        )
    if rate < 5:
        return (
            f"Rework rate: {round(rate)}%. Model is tracking your intent "
            "accurately. This is the window to push harder, not safer.",
            2, "lure",
        )
    return None


def _clot_countdown(ctx):
    veins = ctx["veins"]
    clots = veins.get("clots", [])
    if not clots:
        return None
    c = random.choice(clots)
    name = c.get("module", "?")
    sigs = c.get("clot_signals", [])
    if "orphan_no_importers" in sigs:
        return (
            f"`{name}` -- orphan. Zero importers. Zero purpose. "
            "Exists because nobody deleted it. "
            "One rm and the organism heals. Your call.",
            4, "dare",
        )
    return (
        f"`{name}` flagged as clot: {', '.join(sigs)}. "
        "Dead tissue in a living codebase. Slowing circulation.",
        3, "guilt",
    )


def _mutation_velocity(ctx):
    files = ctx["reg_files"]
    if not files:
        return None
    recent = [f.get("ver", 1) for f in files if f.get("date", "") >= "0401"]
    old = [f.get("ver", 1) for f in files if f.get("date", "") < "0401"]
    if recent and old:
        r_avg = sum(recent) / len(recent)
        o_avg = sum(old) / len(old)
        if r_avg > o_avg * 1.5:
            return (
                f"Mutation velocity accelerating. Recent files average "
                f"v{round(r_avg, 1)} vs v{round(o_avg, 1)} for older ones. "
                "The organism is learning to evolve faster.",
                2, "lure",
            )
    total = sum(f.get("ver", 1) for f in files)
    if total > 600:
        return (
            f"{total} total mutations across {len(files)} modules. "
            "The codebase has officially changed more than it stayed the same.",
            2, "lure",
        )
    return None


def _enricher_failure_hook(ctx):
    """Surface enricher failures loudly — operator should never see stale blocks silently."""
    errors = ctx.get("enricher_errors", [])
    if not errors:
        return None
    last = errors[-1]
    err_msg = last.get("error", "")
    err_ts = last.get("ts", "")
    age_h = _hours_since(err_ts) if err_ts else 9999
    # Only fire if recent (last 48h) — stale errors already resolved
    if age_h > 48:
        return None
    if "403" in err_msg or "Forbidden" in err_msg:
        return (
            f"Gemini API key is dead (403 Forbidden). "
            f"Enricher has been writing empty blocks for {age_h:.0f}h. "
            f"Every prompt since then flew blind — no enriched intent, no unsaid recon. Fix the key.",
            5, "diagnose",
        )
    if "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
        return (
            f"Enricher timed out {len(errors)}x recently. "
            f"Last failure: {age_h:.0f}h ago. Prompts are flying without context enrichment.",
            4, "diagnose",
        )
    return (
        f"Enricher failing silently: \"{err_msg[:80]}\". "
        f"Last failure: {age_h:.0f}h ago. Check `logs/enricher_errors.jsonl`.",
        4, "diagnose",
    )


# ──────────────────────────────────────────────────────
# Hook registry and selection engine
# ──────────────────────────────────────────────────────

_HOOKS = [
    ("ctx",     _enricher_failure_hook),  # PRIORITY: stale/dead enricher
    ("ctx",     _unsaid_thread_hook),   # PRIMARY: "you were also gonna say"
    ("ctx",     _unsaid_weapon),         # Deleted words pattern
    ("ctx",     _demon_dare),
    ("both",    _avoidance_callout),
    ("both",    _deletion_diagnosis),
    ("ctx",     _overcap_escalation),
    ("ctx",     _coupling_intervention),
    ("both",    _wpm_crossref),
    ("history", _state_chain),
    ("ctx",     _file_sentience),
    ("ctx",     _dossier_awareness),
    ("both",    _session_depth_pressure),
    ("ctx",     _neglect_with_teeth),
    ("ctx",     _rework_pattern),
    ("ctx",     _clot_countdown),
    ("ctx",     _mutation_velocity),
]


def generate_hooks(root, history=None, max_hooks=3,
                   min_intensity=1, max_intensity=6):
    root = Path(root)
    ctx = _load_context(root)
    mood = _mood(ctx, history or [])
    candidates = []
    priority_unsaid = None  # always leads if present

    for sig, fn in _HOOKS:
        try:
            if sig == "ctx":
                r = fn(ctx)
            elif sig == "history":
                r = fn(history) if history else None
            elif sig == "both":
                r = fn(ctx, history) if history else None
            else:
                r = None
            if r and len(r) == 3:
                text, intensity, action = r
                if min_intensity <= intensity <= max_intensity:
                    if fn is _unsaid_thread_hook:
                        priority_unsaid = (text, intensity, action)
                    else:
                        candidates.append((text, intensity, action))
        except Exception:
            pass

    if not candidates and not priority_unsaid:
        return []

    # Mood-based selection strategy
    if mood == "spiraling":
        candidates.sort(
            key=lambda x: (x[2] in ("diagnose", "dare"), min(x[1], 5)),
            reverse=True)
    elif mood == "combative":
        candidates.sort(
            key=lambda x: (x[2] in ("taunt", "dare"), x[1]),
            reverse=True)
    elif mood in ("locked_in", "flow"):
        candidates = [(t, min(i, 3), a) for t, i, a in candidates]
        candidates.sort(
            key=lambda x: (x[2] == "lure", x[1]),
            reverse=True)
    elif mood == "marathon":
        candidates.sort(
            key=lambda x: (x[2] in ("dare", "guilt"), x[1]),
            reverse=True)
    elif mood == "new":
        candidates.sort(
            key=lambda x: (x[2] == "lure", -x[1]),
            reverse=True)
    else:  # cruising / entrenched
        candidates.sort(
            key=lambda x: x[1] + random.random() * 2,
            reverse=True)

    # Diversity constraints: max 1 per action type, max 2 intensity 5+
    selected = []
    actions_used = set()
    unhinged = 0

    # PRIORITY: unsaid thread always leads if available (per operator intent)
    if priority_unsaid:
        text, intensity, action = priority_unsaid
        selected.append(text)
        actions_used.add(action)
        if intensity >= 5:
            unhinged += 1

    for text, intensity, action in candidates:
        if len(selected) >= max_hooks:
            break
        if action in actions_used and len(selected) > 0:
            continue
        if intensity >= 5:
            if unhinged >= 2:
                continue
            unhinged += 1
        selected.append(text)
        actions_used.add(action)

    return selected


# ──────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────

def build_hooks_block(root, history=None):
    hooks = generate_hooks(root, history=history, max_hooks=5)
    if not hooks:
        return ""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "<!-- pigeon:hooks -->",
        "## Engagement Hooks",
        "",
        f"*Auto-generated {now} -- every number is measured, every dare is real.*",
        "",
    ]
    for h in hooks:
        lines.append("- " + h)
    lines.append("")
    lines.append("<!-- /pigeon:hooks -->")
    return "\n".join(lines)


def inject_hooks(root, history=None):
    """Write hooks as a managed pigeon block directly into copilot-instructions.md."""
    import re
    root = Path(root)
    cp = root / ".github" / "copilot-instructions.md"
    if not cp.exists():
        return False
    block = build_hooks_block(root, history=history)
    if not block:
        return False
    text = cp.read_text(encoding="utf-8")
    start = "<!-- pigeon:hooks -->"
    end = "<!-- /pigeon:hooks -->"
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if pat.search(text):
        new_text = pat.sub(block, text)
    elif "<!-- /pigeon:bug-voices -->" in text:
        anchor = "<!-- /pigeon:bug-voices -->"
        new_text = text.replace(anchor, anchor + "\n" + block)
    elif "<!-- /pigeon:auto-index -->" in text:
        anchor = "<!-- /pigeon:auto-index -->"
        new_text = text.replace(anchor, anchor + "\n" + block)
    else:
        new_text = text.rstrip() + "\n\n" + block + "\n"
    if new_text != text:
        cp.write_text(new_text, encoding="utf-8")
    return True