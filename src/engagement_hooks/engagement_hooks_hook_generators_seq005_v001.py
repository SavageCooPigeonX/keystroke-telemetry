"""engagement_hooks_hook_generators_seq005_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 191 lines | ~1,741 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from datetime import datetime, timezone
import random

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
def _rework_pattern(ctx):
    rw = ctx["rework"]
    if not rw:
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
