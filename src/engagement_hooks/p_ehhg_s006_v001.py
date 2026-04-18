"""engagement_hooks_seq001_v001_hook_generators_seq006_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 190 lines | ~1,739 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
import random

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
