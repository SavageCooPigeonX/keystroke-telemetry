"""
Narrative Glove — organism consciousness synthesizer.

Reads ALL live telemetry, profiles, bugs, escalation, entropy, engagement,
and cognitive state. Synthesizes into a single narrative paragraph that
reads like a briefing from the organism's prefrontal cortex.

Injected into copilot-instructions.md as the organism's inner monologue.
Zero LLM calls — pure signal weaving from measured data.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

import json
from pathlib import Path
from datetime import datetime, timezone

BLOCK_START = '<!-- pigeon:narrative-glove -->'
BLOCK_END = '<!-- /pigeon:narrative-glove -->'


def _json(fp):
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}


def _jsonl_tail(fp, n=10):
    if not fp.exists():
        return []
    try:
        lines = fp.read_text(encoding='utf-8').strip().split('\n')
        return [json.loads(l) for l in lines[-n:] if l.strip()]
    except Exception:
        return []


def _health_score(snapshot: dict) -> float:
    if not snapshot:
        return 0.0
    try:
        from src.push_snapshot_seq001_v001 import _compute_health_score
        return float(_compute_health_score(snapshot))
    except Exception:
        modules_snap = snapshot.get('modules', {})
        return float(modules_snap.get('compliance_pct', 0))


def synthesize(root: Path) -> str:
    """Read the room. Return a narrative paragraph — the organism's consciousness."""
    root = Path(root)
    now = datetime.now(timezone.utc)

    # ── gather signals ──
    telemetry = _json(root / 'logs' / 'prompt_telemetry_latest.json')
    escalation = _json(root / 'logs' / 'escalation_state.json')
    entropy = _json(root / 'logs' / 'entropy_map.json')
    dossier = _json(root / 'logs' / 'active_dossier.json')
    accuracy = _json(root / 'logs' / 'self_fix_accuracy.json')
    heat_map = _json(root / 'file_heat_map.json')
    snapshot = _json(root / 'logs' / 'push_snapshot_seq001_v001s' / '_latest.json')
    esc_log = _jsonl_tail(root / 'logs' / 'escalation_log.jsonl', 5)
    journal = _jsonl_tail(root / 'logs' / 'prompt_journal.jsonl', 5)
    operator = _json(root / 'operator_profile.md') if False else {}  # md not json

    # ── derive mood signals ──
    latest = telemetry.get('latest_prompt', {})
    state = latest.get('state', 'unknown')
    intent = latest.get('intent', 'unknown')
    wpm = telemetry.get('running_summary', {}).get('avg_wpm', 0)
    del_ratio = telemetry.get('running_summary', {}).get('avg_del_ratio', 0)

    # escalation stats
    esc_modules = escalation.get('modules', {})
    esc_total = escalation.get('total_autonomous_fixes', 0)
    esc_warned = sum(1 for m in esc_modules.values() if m.get('level', 0) >= 3)
    esc_acting = sum(1 for m in esc_modules.values() if m.get('level', 0) >= 4)

    # health — nested inside snapshot
    modules_snap = snapshot.get('modules', {})
    bugs_snap = snapshot.get('bugs', {})
    health = _health_score(snapshot)
    compliance = modules_snap.get('compliance_pct', 0)
    total_bugs = bugs_snap.get('total', 0)
    total_modules = modules_snap.get('total', 0)

    # entropy state
    global_entropy = entropy.get('global_avg_entropy', 0)
    high_entropy_pct = entropy.get('high_entropy_pct', 0)

    # self-fix state
    fix_rate = accuracy.get('avg_fix_rate', 0)
    chronic = accuracy.get('status_breakdown', {}).get('chronic', 0)
    resolved = accuracy.get('status_breakdown', {}).get('resolved', 0)

    # hot modules
    hot = telemetry.get('hot_modules', [])
    hot_names = [h.get('module', '') for h in hot[:3]]

    # recent escalation events
    recent_esc = []
    for e in reversed(esc_log):
        event = e.get('event', '')
        mod = e.get('module', '')
        if event in ('autonomous_fix', 'victory', 'failure', 'countdown'):
            recent_esc.append(f"{mod}({event})")
        if len(recent_esc) >= 3:
            break

    # ── weave narrative fragments ──
    fragments = []

    # organism health opening
    if health < 30:
        fragments.append(f"the organism is sick — health {health:.0f}/100")
    elif health < 60:
        fragments.append(f"the organism is recovering — health {health:.0f}/100")
    else:
        fragments.append(f"the organism is stable — health {health:.0f}/100")

    # compliance pressure
    if compliance < 20:
        fragments.append(f"only {compliance:.0f}% compliant, {total_bugs} bugs across {total_modules} modules")
    elif compliance < 50:
        fragments.append(f"{compliance:.0f}% compliant but {total_bugs} bugs still breathing")

    # chronic bugs narrative
    if chronic > 50:
        fragments.append(f"{chronic} chronic bugs refuse to die — fix rate is {fix_rate*100:.0f}%")
    elif chronic > 20:
        fragments.append(f"{chronic} chronic bugs, {resolved} killed — the ratio is shifting")

    # escalation state
    if esc_acting > 0:
        fragments.append(f"{esc_acting} module(s) took autonomous action — the organism is deciding for itself")
    elif esc_warned > 0:
        fragments.append(f"{esc_warned} module(s) counting down to self-fix — the countdown is visible")
    elif len(esc_modules) > 10:
        fragments.append(f"{len(esc_modules)} modules on the escalation ladder — patience is running out")

    # entropy state
    if global_entropy > 0.35:
        fragments.append(f"uncertainty is high (entropy {global_entropy:.2f}) — {high_entropy_pct:.0f}% of modules need confidence")
    elif global_entropy > 0.25:
        fragments.append(f"entropy at {global_entropy:.2f} — the codebase knows what it is, mostly")

    # hot modules
    if hot_names:
        fragments.append(f"cognitive heat on: {', '.join(f'`{n}`' for n in hot_names)}")

    # recent escalation drama
    if recent_esc:
        fragments.append(f"recent escalation: {', '.join(recent_esc)}")

    # operator state
    if state == 'frustrated':
        fragments.append("operator is frustrated — be precise, not verbose")
    elif state == 'abandoned':
        fragments.append("operator abandoned last message — re-anchor with context")
    elif state == 'focused':
        fragments.append("operator is focused — match the energy")

    # intent signal
    if intent == 'building':
        fragments.append("intent: building — generate, don't explain")
    elif intent == 'debugging':
        fragments.append("intent: debugging — diagnose, don't theorize")

    # ── compose ──
    if not fragments:
        return ""

    narrative = ". ".join(fragments) + "."

    return narrative


def inject_narrative(root: Path) -> bool:
    """Inject narrative glove into copilot-instructions.md."""
    root = Path(root)
    ci = root / '.github' / 'copilot-instructions.md'
    if not ci.exists():
        return False

    narrative = synthesize(root)
    if not narrative:
        return False

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    block = (
        f"{BLOCK_START}\n"
        f"## Organism Consciousness\n\n"
        f"*{now} — synthesized from all live signals, zero LLM calls*\n\n"
        f"> {narrative}\n\n"
        f"{BLOCK_END}"
    )

    text = ci.read_text(encoding='utf-8')

    import re
    if BLOCK_START in text:
        text = re.sub(
            rf'{re.escape(BLOCK_START)}.*?{re.escape(BLOCK_END)}',
            block, text, flags=re.DOTALL,
        )
    else:
        # insert before task context (right after escalation warnings or organism health)
        for marker in ['<!-- pigeon:task-context -->', '<!-- pigeon:organism-health -->', '<!-- pigeon:escalation-warnings -->']:
            if marker in text:
                text = text.replace(marker, block + '\n' + marker)
                break
        else:
            text = text.rstrip() + '\n\n' + block + '\n'

    ci.write_text(text, encoding='utf-8')
    return True


if __name__ == '__main__':
    root = Path('.')
    narrative = synthesize(root)
    print("── narrative glove ──")
    print(narrative)
    print()
    inject_narrative(root)
    print("✅ injected into copilot-instructions.md")
