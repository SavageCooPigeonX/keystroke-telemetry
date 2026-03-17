"""Pulse harvest: pairs prompts to file edits with sub-second timing.

Each src/ file carries a structured comment block (the "pulse").
When an LLM edits a file it MUST update the pulse with its edit reason.
The extension's onDidSave watcher detects pulses, correlates them with
the most recent prompt_journal entry, and writes paired records to
logs/edit_pairs.jsonl.  Pigeon post-commit harvests any surviving pulses
as a failsafe.

Pulse block format (lives right after the pigeon prompt box):
    # ── telemetry:pulse ──
    # EDIT_TS:   None
    # EDIT_HASH: None
    # EDIT_WHY:  None
    # ── /pulse ──

Paired record schema (edit_pairs.jsonl):
    {
      "ts":          "<ISO-8601>",
      "prompt_ts":   "<ISO-8601 from journal>",
      "prompt_msg":  "<user message text>",
      "file":        "<relative path>",
      "edit_why":    "<LLM-stated reason or 'auto'>",
      "edit_hash":   "<first 8 of sha256 of new content>",
      "latency_ms":  <prompt_ts → save_ts>,
      "state":       "<cognitive state at time of edit>",
      "session_n":   <prompt journal session_n>
    }
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ── Pulse block regex ────────────────────────────────────────────────────────

PULSE_RE = re.compile(
    r'^# ── telemetry:pulse ──\n'
    r'# EDIT_TS:\s*(.*)\n'
    r'# EDIT_HASH:\s*(.*)\n'
    r'# EDIT_WHY:\s*(.*)\n'
    r'# ── /pulse ──$',
    re.MULTILINE,
)

PULSE_BLOCK = (
    '# ── telemetry:pulse ──\n'
    '# EDIT_TS:   None\n'
    '# EDIT_HASH: None\n'
    '# EDIT_WHY:  None\n'
    '# ── /pulse ──'
)


def make_pulse_block(edit_ts: str = 'None',
                     edit_hash: str = 'None',
                     edit_why: str = 'None') -> str:
    return (
        '# ── telemetry:pulse ──\n'
        f'# EDIT_TS:   {edit_ts}\n'
        f'# EDIT_HASH: {edit_hash}\n'
        f'# EDIT_WHY:  {edit_why}\n'
        '# ── /pulse ──'
    )


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:8]


# ── Read pulse from a file ───────────────────────────────────────────────────

def read_pulse(filepath: Path) -> dict | None:
    """Read pulse block from a file. Returns dict or None if no pulse."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None
    m = PULSE_RE.search(text)
    if not m:
        return None
    ts_val, hash_val, why_val = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    if ts_val == 'None' and hash_val == 'None':
        return None  # pulse is blank — no edit recorded
    return {'edit_ts': ts_val, 'edit_hash': hash_val, 'edit_why': why_val}


def clear_pulse(filepath: Path) -> bool:
    """Reset pulse block to None values. Returns True if changed."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    if not PULSE_RE.search(text):
        return False
    new_text = PULSE_RE.sub(PULSE_BLOCK, text)
    if new_text == text:
        return False
    filepath.write_text(new_text, encoding='utf-8')
    return True


def stamp_pulse(filepath: Path, edit_why: str = 'auto') -> bool:
    """Stamp the pulse block with current time + content hash."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    if not PULSE_RE.search(text):
        return False
    ts = datetime.now(timezone.utc).isoformat()
    h = content_hash(text)
    new_block = make_pulse_block(ts, h, edit_why)
    new_text = PULSE_RE.sub(new_block, text)
    filepath.write_text(new_text, encoding='utf-8')
    return True


# ── Inject pulse block into a file that doesn't have one ─────────────────────

def inject_pulse(filepath: Path) -> bool:
    """Add a blank pulse block after the pigeon prompt box (or after docstring)."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    if PULSE_RE.search(text):
        return False  # already has one
    # Insert after pigeon prompt box if present
    pigeon_box = re.search(
        r'^# ── pigeon ─[^\n]*\n(?:# [^\n]*\n)*# ─{10,}─*\n',
        text, re.MULTILINE,
    )
    if pigeon_box:
        pos = pigeon_box.end()
        new_text = text[:pos] + PULSE_BLOCK + '\n' + text[pos:]
    else:
        # Insert after module docstring
        ds = re.match(r'^("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\n', text)
        if ds:
            pos = ds.end()
            new_text = text[:pos] + PULSE_BLOCK + '\n' + text[pos:]
        else:
            new_text = PULSE_BLOCK + '\n' + text
    filepath.write_text(new_text, encoding='utf-8')
    return True


# ── Correlate pulse with latest prompt journal entry ─────────────────────────

def _load_latest_journal(root: Path) -> dict | None:
    """Read the most recent entry from prompt_journal.jsonl."""
    journal = root / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return None
    try:
        lines = journal.read_text(encoding='utf-8').strip().splitlines()
        if not lines:
            return None
        return json.loads(lines[-1])
    except (json.JSONDecodeError, OSError):
        return None


def pair_pulse_to_prompt(root: Path, filepath: Path,
                         cognitive_state: str = 'neutral') -> dict | None:
    """Read pulse from file, pair with latest journal entry, write to edit_pairs.
    Returns the paired record or None.
    """
    pulse = read_pulse(filepath)
    if not pulse:
        return None
    journal = _load_latest_journal(root)
    rel = filepath.relative_to(root).as_posix()
    now = datetime.now(timezone.utc)

    # Compute latency: prompt_ts → pulse edit_ts
    latency_ms = 0
    prompt_ts = ''
    prompt_msg = ''
    session_n = 0
    if journal:
        prompt_ts = journal.get('ts', '')
        prompt_msg = journal.get('msg', '')
        session_n = journal.get('session_n', 0)
        try:
            pt = datetime.fromisoformat(prompt_ts)
            et = datetime.fromisoformat(pulse['edit_ts'])
            latency_ms = int((et - pt).total_seconds() * 1000)
        except (ValueError, KeyError):
            pass

    record = {
        'ts': now.isoformat(),
        'prompt_ts': prompt_ts,
        'prompt_msg': prompt_msg[:200],  # truncate for storage
        'file': rel,
        'edit_why': pulse['edit_why'],
        'edit_hash': pulse['edit_hash'],
        'latency_ms': latency_ms,
        'state': cognitive_state,
        'session_n': session_n,
    }

    # Append to edit_pairs.jsonl
    pairs_path = root / 'logs' / 'edit_pairs.jsonl'
    pairs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(pairs_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')

    # Clear the pulse
    clear_pulse(filepath)
    return record


# ── Bulk harvest: post-commit failsafe ───────────────────────────────────────

def harvest_all_pulses(root: Path, state: str = 'neutral') -> list[dict]:
    """Walk all .py files under src/, harvest any stamped pulses.
    Called by pigeon post-commit hook as failsafe.
    """
    records = []
    src = root / 'src'
    if not src.is_dir():
        return records
    for py in src.glob('*.py'):
        if py.name.startswith('__'):
            continue
        rec = pair_pulse_to_prompt(root, py, state)
        if rec:
            records.append(rec)
    return records


# ── Inject pulse blocks into all src/ files ──────────────────────────────────

def inject_all_pulses(root: Path) -> int:
    """Add blank pulse blocks to all src/*.py files that lack one."""
    count = 0
    src = root / 'src'
    if not src.is_dir():
        return 0
    for py in src.glob('*.py'):
        if py.name.startswith('__'):
            continue
        if inject_pulse(py):
            count += 1
    return count
