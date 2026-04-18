"""TC Manifest — read/write TC's self-modifying brain.

TC_MANIFEST.md is TC's own state file. Unlike copilot-instructions.md
(which TC reads but doesn't write), TC_MANIFEST.md is TC's scratchpad:
- prompt box: self-tasks
- bug trajectories: bug lifecycle over pushes
- intent profiles: learned from prompt clusters
- file trajectories: last 3 λ per file
- selection weights: auto-adjusted based on hit rate
- question queue: high-entropy moments surfaced to operator

The key: TC WRITES to this file. It learns by overwriting its own state.
"""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .tc_constants_seq001_v001 import ROOT

MANIFEST_PATH = ROOT / 'logs' / 'TC_MANIFEST.md'
_BLOCK_RE = re.compile(r'<!-- tc:([a-z-]+) -->\n(.*?)\n<!-- /tc:\1 -->', re.DOTALL)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def load_manifest() -> dict[str, str]:
    """Load all TC manifest blocks as raw strings."""
    if not MANIFEST_PATH.exists():
        return {}
    text = MANIFEST_PATH.read_text('utf-8', errors='ignore')
    blocks = {}
    for m in _BLOCK_RE.finditer(text):
        blocks[m.group(1)] = m.group(2).strip()
    return blocks


def save_block(block_name: str, content: str) -> bool:
    """Overwrite a single block in TC_MANIFEST.md.
    
    This is TC's write capability. It can modify its own state.
    """
    if not MANIFEST_PATH.exists():
        return False
    text = MANIFEST_PATH.read_text('utf-8', errors='ignore')
    pattern = f'<!-- tc:{block_name} -->\n.*?\n<!-- /tc:{block_name} -->'
    replacement = f'<!-- tc:{block_name} -->\n{content}\n<!-- /tc:{block_name} -->'
    new_text, count = re.subn(pattern, replacement, text, flags=re.DOTALL)
    if count == 0:
        return False
    MANIFEST_PATH.write_text(new_text, 'utf-8')
    return True


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT BOX — TC's self-tasks
# ══════════════════════════════════════════════════════════════════════════════

def parse_prompt_box() -> list[dict]:
    """Parse TC's self-tasks from prompt-box block."""
    blocks = load_manifest()
    box = blocks.get('prompt-box', '')
    tasks = []
    for line in box.splitlines():
        m = re.match(r'- (TC-\d+): \[(\w+)\] (.+)', line.strip())
        if m:
            tasks.append({
                'id': m.group(1),
                'status': m.group(2),
                'task': m.group(3),
            })
    return tasks


def add_task(task: str) -> str:
    """Add a new self-task. Returns task ID."""
    tasks = parse_prompt_box()
    max_id = max((int(t['id'].split('-')[1]) for t in tasks), default=0)
    new_id = f'TC-{max_id + 1:03d}'
    tasks.append({'id': new_id, 'status': 'pending', 'task': task})
    _write_prompt_box(tasks)
    return new_id


def update_task_status(task_id: str, status: str) -> bool:
    """Update a task's status (pending, in-progress, done)."""
    tasks = parse_prompt_box()
    for t in tasks:
        if t['id'] == task_id:
            t['status'] = status
            _write_prompt_box(tasks)
            return True
    return False


def _write_prompt_box(tasks: list[dict]):
    lines = ['## TC Self-Tasks', '', "*TC writes these for itself. Checked/updated on every cycle.*", '']
    for t in tasks:
        lines.append(f"- {t['id']}: [{t['status']}] {t['task']}")
    save_block('prompt-box', '\n'.join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# BUG TRAJECTORIES — bug lifecycle over pushes
# ══════════════════════════════════════════════════════════════════════════════

def parse_bug_trajectories() -> list[dict]:
    """Parse bug lifecycle data."""
    blocks = load_manifest()
    raw = blocks.get('bug-trajectories', '')
    bugs = []
    for line in raw.splitlines():
        if line.startswith('B') and '|' in line:
            parts = line.split('|')
            if len(parts) >= 7:
                bugs.append({
                    'id': parts[0],
                    'module': parts[1],
                    'type': parts[2],
                    'first_seen': parts[3],
                    'last_seen': parts[4],
                    'status': parts[5],
                    'frequency': parts[6],
                    'deduction': parts[7] if len(parts) > 7 else '',
                })
    return bugs


def update_bug(module: str, bug_type: str, status: str = None, 
               deduction: str = None) -> dict:
    """Update or create a bug trajectory. Returns the bug entry."""
    bugs = parse_bug_trajectories()
    today = _now()[:10]
    
    # Find existing
    existing = None
    for b in bugs:
        if b['module'] == module and b['type'] == bug_type:
            existing = b
            break
    
    if existing:
        existing['last_seen'] = today
        # Update frequency count
        if '/' in existing['frequency']:
            num, denom = existing['frequency'].split('/')
            existing['frequency'] = f"{int(num)+1}/{int(denom)+1}"
        if status:
            existing['status'] = status
        if deduction:
            existing['deduction'] = deduction
    else:
        # New bug
        max_id = max((int(b['id'][1:]) for b in bugs), default=0)
        existing = {
            'id': f'B{max_id + 1:03d}',
            'module': module,
            'type': bug_type,
            'first_seen': today,
            'last_seen': today,
            'status': 'new',
            'frequency': '1/1',
            'deduction': deduction or '',
        }
        bugs.append(existing)
    
    _write_bug_trajectories(bugs)
    return existing


def _write_bug_trajectories(bugs: list[dict]):
    lines = ['## Bug Lifecycle Trajectories', '',
             '*Format: BUG_ID|module|type|first_seen|last_seen|status|frequency|deduction*', '']
    for b in bugs:
        lines.append(f"{b['id']}|{b['module']}|{b['type']}|{b['first_seen']}|{b['last_seen']}|{b['status']}|{b['frequency']}|{b.get('deduction','')}")
    save_block('bug-trajectories', '\n'.join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# INTENT PROFILES — learned from prompt clusters
# ══════════════════════════════════════════════════════════════════════════════

def parse_intent_profiles() -> dict[str, dict]:
    """Parse intent profiles from YAML block."""
    blocks = load_manifest()
    raw = blocks.get('intent-profiles', '')
    # Extract YAML between ``` markers
    m = re.search(r'```yaml\n(.+?)```', raw, re.DOTALL)
    if not m:
        return {}
    yaml_text = m.group(1)
    
    # Simple YAML-like parse (no pyyaml dependency)
    profiles = {}
    current = None
    for line in yaml_text.splitlines():
        if not line.strip() or line.strip().startswith('#'):
            continue
        if not line.startswith(' ') and line.endswith(':'):
            current = line[:-1].strip()
            profiles[current] = {}
        elif current and ':' in line:
            key, val = line.strip().split(':', 1)
            val = val.strip()
            # Parse lists [...]
            if val.startswith('[') and val.endswith(']'):
                val = [v.strip().strip('"\'') for v in val[1:-1].split(',')]
            # Parse numbers
            elif val.replace('.', '').isdigit():
                val = float(val) if '.' in val else int(val)
            profiles[current][key] = val
    return profiles


def update_intent_profile(name: str, trigger: list[str] = None,
                          files: list[str] = None, template: str = None,
                          confidence: float = None, hit: bool = False) -> dict:
    """Update or create an intent profile. Returns the profile."""
    profiles = parse_intent_profiles()
    now = _now()
    
    if name in profiles:
        p = profiles[name]
        if trigger:
            p['trigger'] = trigger
        if files:
            p['files'] = files
        if template:
            p['template'] = template
        if confidence is not None:
            p['confidence'] = confidence
        if hit:
            p['last_match'] = now
            p['hit_count'] = p.get('hit_count', 0) + 1
    else:
        profiles[name] = {
            'trigger': trigger or [],
            'files': files or [],
            'template': template or '/build',
            'confidence': confidence or 0.5,
            'created': now,
            'last_match': now if hit else None,
            'hit_count': 1 if hit else 0,
        }
    
    _write_intent_profiles(profiles)
    return profiles[name]


def match_intent_profile(buffer: str) -> tuple[str | None, dict | None, float]:
    """Find the best matching intent profile for a buffer.
    
    Returns: (profile_name, profile_dict, match_score) or (None, None, 0)
    """
    profiles = parse_intent_profiles()
    if not profiles:
        return None, None, 0
    
    buffer_lower = buffer.lower()
    best_name, best_profile, best_score = None, None, 0
    
    for name, profile in profiles.items():
        triggers = profile.get('trigger', [])
        if not triggers:
            continue
        # Count trigger matches
        matches = sum(1 for t in triggers if t.lower() in buffer_lower)
        if matches == 0:
            continue
        # Score: % of triggers matched * profile confidence
        score = (matches / len(triggers)) * profile.get('confidence', 0.5)
        if score > best_score:
            best_name, best_profile, best_score = name, profile, score
    
    return best_name, best_profile, best_score


def _write_intent_profiles(profiles: dict[str, dict]):
    lines = ['## Intent Profiles (learned from prompt clusters)', '',
             "*Auto-generated when TC detects recurring intent patterns.*", '', '```yaml']
    for name, p in profiles.items():
        lines.append(f'{name}:')
        for key, val in p.items():
            if isinstance(val, list):
                lines.append(f'  {key}: [{", ".join(str(v) for v in val)}]')
            else:
                lines.append(f'  {key}: {val}')
        lines.append('')
    lines.append('```')
    save_block('intent-profiles', '\n'.join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# FILE TRAJECTORIES — last 3 λ mutations per file
# ══════════════════════════════════════════════════════════════════════════════

def parse_file_trajectories() -> dict[str, dict]:
    """Parse file trajectory data."""
    blocks = load_manifest()
    raw = blocks.get('file-trajectories', '')
    trajs = {}
    for line in raw.splitlines():
        if '|' in line and not line.startswith('*'):
            parts = line.split('|')
            if len(parts) >= 4:
                trajs[parts[0]] = {
                    'stem': parts[0],
                    'mutations': parts[1],
                    'days_span': int(parts[2]) if parts[2].isdigit() else 0,
                    'stability': parts[3],
                    'deduction': parts[4] if len(parts) > 4 else '',
                }
    return trajs


def update_file_trajectory(stem: str, new_lambda: str, 
                           deduction: str = None) -> dict:
    """Add a new λ mutation to a file's trajectory."""
    trajs = parse_file_trajectories()
    
    if stem in trajs:
        t = trajs[stem]
        # Parse existing mutations
        muts = t['mutations'].split('→') if t['mutations'] else []
        muts.append(new_lambda)
        # Keep last 3
        muts = muts[-3:]
        t['mutations'] = '→'.join(muts)
        t['days_span'] += 1  # rough
        # Determine stability
        unique = len(set(muts))
        if unique == 1:
            t['stability'] = 'stable'
        elif unique == len(muts):
            t['stability'] = 'unstable'
        else:
            t['stability'] = 'mixed'
        if deduction:
            t['deduction'] = deduction
    else:
        trajs[stem] = {
            'stem': stem,
            'mutations': new_lambda,
            'days_span': 0,
            'stability': 'new',
            'deduction': deduction or 'just created',
        }
    
    _write_file_trajectories(trajs)
    return trajs[stem]


def _write_file_trajectories(trajs: dict[str, dict]):
    lines = ['## File Trajectories (last 3 λ mutations per file)', '',
             '*Format: stem|v1→v2→v3|days_span|stability|deduction*', '']
    for stem, t in trajs.items():
        lines.append(f"{t['stem']}|{t['mutations']}|{t['days_span']}|{t['stability']}|{t.get('deduction','')}")
    save_block('file-trajectories', '\n'.join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# SELECTION WEIGHTS — auto-adjusted based on hit rate
# ══════════════════════════════════════════════════════════════════════════════

def parse_selection_weights() -> dict[str, float]:
    """Parse selection weights."""
    blocks = load_manifest()
    raw = blocks.get('selection-weights', '')
    weights = {}
    in_weights = False
    for line in raw.splitlines():
        if 'weights:' in line:
            in_weights = True
            continue
        if 'adjustments:' in line:
            break
        if in_weights and ':' in line:
            parts = line.strip().split(':')
            if len(parts) >= 2:
                key = parts[0].strip()
                val = parts[1].strip().split('#')[0].strip()
                try:
                    weights[key] = float(val)
                except ValueError:
                    pass
    return weights


def adjust_weight(key: str, delta: float, reason: str) -> float:
    """Adjust a selection weight. Returns new value."""
    weights = parse_selection_weights()
    old_val = weights.get(key, 0.5)
    new_val = max(0.0, min(1.0, old_val + delta))
    weights[key] = new_val
    _write_selection_weights(weights, reason)
    return new_val


def _write_selection_weights(weights: dict[str, float], reason: str = ''):
    lines = ['## Dynamic Context Weights', '',
             "*TC auto-adjusts based on what actually works.*", '', '```yaml', 'weights:']
    for key, val in weights.items():
        lines.append(f'  {key}: {val:.2f}')
    lines.extend(['', 'adjustments:',
                  f'  last_updated: {_now()}',
                  f'  reason: "{reason}"'])
    lines.append('```')
    save_block('selection-weights', '\n'.join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# PREDICTION LOG — TC learns from outcomes
# ══════════════════════════════════════════════════════════════════════════════

def log_prediction(predicted_intent: str, actual_intent: str,
                   predicted_files: list[str], touched_files: list[str]) -> float:
    """Log a prediction and its outcome. Returns score."""
    blocks = load_manifest()
    raw = blocks.get('prediction-log', '')
    
    # Calculate score
    intent_match = 1.0 if predicted_intent == actual_intent else 0.0
    if predicted_files and touched_files:
        file_overlap = len(set(predicted_files) & set(touched_files)) / len(set(predicted_files))
    else:
        file_overlap = 0.0
    score = (intent_match * 0.6) + (file_overlap * 0.4)
    
    # Append log entry
    now = _now()
    pred_files = ','.join(predicted_files[:3]) if predicted_files else 'none'
    touch_files = ','.join(touched_files[:3]) if touched_files else 'none'
    entry = f'{now}|{predicted_intent}|{actual_intent}|[{pred_files}]|[{touch_files}]|{score:.1f}'
    
    lines = raw.splitlines() if raw else []
    # Keep header lines
    header_lines = [l for l in lines if l.startswith('*') or l.startswith('##')]
    data_lines = [l for l in lines if l.startswith('202')]
    data_lines.append(entry)
    # Keep last 20 entries
    data_lines = data_lines[-20:]
    
    new_content = '\n'.join([
        '## Prediction Log (TC learns from outcomes)', '',
        '*Format: ts|predicted_intent|actual_intent|predicted_files|touched_files|score*', ''
    ] + data_lines)
    save_block('prediction-log', new_content)
    
    return score


# ══════════════════════════════════════════════════════════════════════════════
# QUESTION QUEUE — high-entropy moments surfaced to operator
# ══════════════════════════════════════════════════════════════════════════════

def parse_questions() -> list[dict]:
    """Parse question queue."""
    blocks = load_manifest()
    raw = blocks.get('question-queue', '')
    questions = []
    for line in raw.splitlines():
        m = re.match(r'- (Q-\d+): \[(\w+)\] "(.+?)"(?: → "(.+)")?', line.strip())
        if m:
            questions.append({
                'id': m.group(1),
                'status': m.group(2),
                'question': m.group(3),
                'answer': m.group(4),
            })
    return questions


def add_question(question: str) -> str:
    """Add a question to the queue. Returns question ID."""
    questions = parse_questions()
    max_id = max((int(q['id'].split('-')[1]) for q in questions), default=0)
    new_id = f'Q-{max_id + 1:03d}'
    questions.append({
        'id': new_id,
        'status': 'pending',
        'question': question,
        'answer': None,
    })
    _write_questions(questions)
    return new_id


def answer_question(question_id: str, answer: str) -> bool:
    """Mark a question as answered."""
    questions = parse_questions()
    for q in questions:
        if q['id'] == question_id:
            q['status'] = 'answered'
            q['answer'] = answer
            _write_questions(questions)
            return True
    return False


def _write_questions(questions: list[dict]):
    lines = ['## Question Queue (high-entropy moments surfaced to operator)', '',
             "*TC writes questions here when uncertain. Operator answers close the loop.*", '']
    for q in questions:
        if q.get('answer'):
            lines.append(f"- {q['id']}: [{q['status']}] \"{q['question']}\" → \"{q['answer']}\"")
        else:
            lines.append(f"- {q['id']}: [{q['status']}] \"{q['question']}\"")
    save_block('question-queue', '\n'.join(lines))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN API — unified access point
# ══════════════════════════════════════════════════════════════════════════════

def get_tc_context_seq001_v001() -> dict:
    """Get full TC context for injection into predictions.
    
    This is what TC reads when making decisions.
    """
    return {
        'tasks': parse_prompt_box(),
        'bugs': parse_bug_trajectories(),
        'profiles': parse_intent_profiles(),
        'trajectories': parse_file_trajectories(),
        'weights': parse_selection_weights(),
        'pending_questions': [q for q in parse_questions() if q['status'] == 'pending'],
    }


def tc_cycle_complete():
    """Called at end of each TC cycle to update timestamp."""
    if not MANIFEST_PATH.exists():
        return
    text = MANIFEST_PATH.read_text('utf-8', errors='ignore')
    now = _now()
    # Update last cycle timestamp at bottom of file
    new_text = re.sub(
        r'\*Last TC cycle: .+?\*',
        f'*Last TC cycle: {now}*',
        text
    )
    MANIFEST_PATH.write_text(new_text, 'utf-8')
