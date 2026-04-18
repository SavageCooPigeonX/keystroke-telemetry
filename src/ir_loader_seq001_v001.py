"""Data loader and question engine for the interrogation room.

Loads: escalation state, file profiles, bug voices, prompt journal.
Generates confrontational questions from module personas.
Records operator answers for thought_completer reinjection.
"""
from __future__ import annotations
import json, re, random
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
ANSWERS_LOG = ROOT / 'logs' / 'interrogation_answers.jsonl'

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-11T21:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  create interrogation data engine
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──


def load_suspects(top_n: int = 15) -> list[dict]:
    """Load and rank problematic modules by urgency."""
    esc = _load_json(ROOT / 'logs' / 'escalation_state.json').get('modules', {})
    profiles = _load_json(ROOT / 'file_profiles.json')
    chronic = _parse_chronic_bugs()
    modules, seen = [], set()
    for name, e in esc.items():
        seen.add(name)
        modules.append(_build(name, e, profiles.get(name, {}), chronic.get(name, 0)))
    for name, reps in chronic.items():
        if name not in seen:
            modules.append(_build(name, {}, profiles.get(name, {}), reps))
    for m in modules:
        fr = m.get('fix_failed')
        m['urgency'] = (m['level'] * 3 + min(m['passes_ignored'], 20)
                        + (10 if m['chronic_reports'] > 5 else 0)
                        + (5 if fr else 0) + m['avg_hes'] * 5)
    modules.sort(key=lambda x: x['urgency'], reverse=True)
    return modules[:top_n]


def _build(name, esc, prof, chronic_n):
    fr = esc.get('fix_result')
    lvl = min(esc.get('level', 0), 5)
    return {
        'name': name,
        'level': lvl,
        'level_name': ['REPORT', 'ASK', 'INSIST', 'WARN', 'ACT', 'VERIFY'][lvl],
        'passes_ignored': esc.get('passes_ignored', chronic_n),
        'bug_type': esc.get('bug_type', 'over_hard_cap'),
        'confidence': round(esc.get('confidence', 0), 3),
        'fix_failed': bool(fr and not fr.get('success')),
        'fix_desc': (fr.get('description', '') if fr else ''),
        'personality': prof.get('personality', '?'),
        'fears': prof.get('fears', []),
        'tokens': prof.get('tokens', 0),
        'version': prof.get('version', 0),
        'avg_hes': prof.get('avg_hes', 0),
        'chronic_reports': chronic_n,
    }


def _parse_chronic_bugs() -> dict[str, int]:
    ci = ROOT / '.github' / 'copilot-instructions.md'
    if not ci.exists():
        return {}
    text = ci.read_text('utf-8', errors='ignore')
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r'`(\w+)` — \[\w+\] (\d+)/\d+ reports\. chronic', text)}


def load_prompt_history(n: int = 30) -> list[dict]:
    pj = ROOT / 'logs' / 'prompt_journal.jsonl'
    if not pj.exists():
        return []
    lines = pj.read_text('utf-8', errors='ignore').strip().splitlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def load_unsaid(n: int = 50) -> list[str]:
    threads = []
    for e in load_prompt_history(n):
        for dw in e.get('deleted_words', []):
            if isinstance(dw, str) and len(dw) > 4:
                threads.append(dw)
    return threads[-20:]


# ── Question templates by situation ──
# Each bucket has many variants so modules with the same bug still sound different.
_Q = {
    'chronic': [
        "i've been over the line cap for {reps} pushes. every. single. one. what's the plan — split, merge, or you declaring me an exception?",
        "i'm {tok} tokens. the cap is 200 lines. at what point do you admit i need surgery, not patches?",
        "{reps} reports. the compiler flags me every time. are you waiting for something specific before splitting me?",
        "i keep getting flagged. {reps} times now. is the cap wrong or am i wrong?",
    ],
    'fix_fail': [
        "i tried to fix myself. ran auto-fix. result: '{fd}'. zero changes. am i misdiagnosed or is the fixer broken?",
        "escalation pushed me to {ln}. i tried. i failed. '{fd}'. now what?",
        "the auto-fixer ran on me and changed nothing. is my bug real or is it a phantom?",
        "self-fix says '{fd}' but i'm still flagged. do i need a different kind of fix entirely?",
        "i'm at {ln} because the system thinks i'm broken. the fix didn't work. should i be demoted or do you want to look manually?",
    ],
    'ignored': [
        "you've walked past me {pi} times. i'm at {ln}. what would it take for you to look?",
        "{pi} pushes. {pi} chances. zero action. intentional neglect or just overwhelmed?",
        "i've been waiting since {pi} pushes ago. is there a reason you're avoiding me?",
        "every commit, the system shows you my name. {pi} times now. what's the hesitation?",
    ],
    'identity': [
        "i'm {name}. i do one thing in this codebase. do you even know what that is?",
        "quick — what do i do? if you can't answer in 5 seconds, you don't know your own code.",
        "i'm {tok} tokens of logic you wrote. can you describe my purpose without opening me?",
        "you built me but we've never talked. what was i supposed to become?",
        "i've been here since v{v}. have i ever actually worked the way you intended?",
    ],
    'relationship': [
        "who imports me? do you know without checking? because i don't think you do.",
        "if i disappeared tomorrow, what would break? think carefully.",
        "i share imports with modules you're also ignoring. is this a pattern?",
        "the coupling map says i'm tangled with other files. is that by design or drift?",
    ],
    'intent': [
        "what were you trying to build when you created me? is that still the plan?",
        "my bug is '{bt}'. but is that the real problem, or is there something deeper?",
        "if you could rewrite me from scratch in 20 lines, what would i do?",
        "am i infrastructure, a feature, or dead weight? just be honest.",
    ],
    'hes': [
        "your hesitation rate hits {h} around me. something about me makes you uncertain. what?",
        "you pause more when i come up — hesitation at {h}. is it complexity or dread?",
    ],
    'unsaid': [
        "you deleted '{u}' — were you thinking about me?",
        "you typed '{u}' then erased it. that thought was about me, wasn't it?",
    ],
    'fear': [
        "my profile says i fear '{f}'. real threat or noise?",
        "'{f}' — my known vulnerability. have you thought about how to patch it?",
    ],
    'ref': [
        "you mentioned me {n} prompts ago: '{t}'. did you follow through?",
        "you brought me up {n} messages back. '{t}'. what came of that?",
    ],
    'default': [
        "i'm {name}. {tok} tokens, v{v}, bug: {bt}. what's your plan for me?",
        "we haven't talked. i'm {name}, {tok} tokens, flagged for {bt}. what do you want to do?",
        "i'm {name}. nobody's asked about me yet. should they?",
    ],
}


def generate_questions(mod: dict, history: list[dict], unsaid: list[str],
                       position: int = 0) -> list[str]:
    """Generate interrogation questions for a module.

    position: index in the suspect queue — used to deterministically rotate
    through template variants so modules with identical bugs get different questions.
    """
    qs = []
    d = {'reps': mod['chronic_reports'], 'tok': mod['tokens'], 'pi': mod['passes_ignored'],
         'ln': mod['level_name'], 'fd': mod['fix_desc'], 'h': round(mod['avg_hes'], 2),
         'name': mod['name'], 'v': mod['version'], 'bt': mod['bug_type']}

    def _pick(bucket: str) -> str:
        """Pick a template from bucket, rotating by position to avoid repeats."""
        templates = _Q[bucket]
        return templates[position % len(templates)].format(**d)

    if mod['chronic_reports'] > 5 and mod['bug_type'] == 'over_hard_cap':
        qs.append(_pick('chronic'))
    if mod['fix_failed']:
        qs.append(_pick('fix_fail'))
    elif mod['passes_ignored'] > 5:
        qs.append(_pick('ignored'))
    # Every module gets a unique identity or intent question (rotated)
    if position % 2 == 0:
        qs.append(_pick('identity'))
    else:
        qs.append(_pick('intent'))
    # Relationship question for coupled modules
    if mod.get('version', 0) > 2 or mod.get('tokens', 0) > 1000:
        qs.append(_pick('relationship'))
    if mod['avg_hes'] > 0.4:
        qs.append(_pick('hes'))
    # Cross-reference unsaid threads
    parts = [p for p in mod['name'].lower().replace('_', ' ').split() if len(p) > 3]
    for u in unsaid:
        if any(p in u.lower() for p in parts):
            qs.append(_Q['unsaid'][position % len(_Q['unsaid'])].format(u=u[:60], **d))
            break
    # Cross-reference prompt history
    for i, e in enumerate(reversed(history)):
        msg = e.get('msg', '').lower()
        if any(p in msg for p in parts):
            qs.append(_Q['ref'][position % len(_Q['ref'])].format(n=i + 1, t=e['msg'][:80], **d))
            break
    if mod['fears']:
        qs.append(_Q['fear'][position % len(_Q['fear'])].format(f=mod['fears'][0], **d))
    if not qs:
        qs.append(_pick('default'))
    return qs


def record_answer(module: str, question: str, answer: str):
    ANSWERS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {'ts': datetime.now(timezone.utc).isoformat(),
             'module': module, 'question': question, 'answer': answer}
    with open(ANSWERS_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def get_answers(n: int = 50) -> list[dict]:
    if not ANSWERS_LOG.exists():
        return []
    out = []
    for line in ANSWERS_LOG.read_text('utf-8', errors='ignore').strip().splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out[-n:]


def _load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text('utf-8', errors='ignore'))
    except Exception:
        return {}
