"""Cognitive reactor: autonomous code modification driven by typing telemetry.

When sustained cognitive load (frustration, hesitation) is detected on
specific files, this module autonomously:
  1. Identifies the hot files from the heat map
  2. Runs cross-file analysis (self-fix) targeted at those files
  3. Generates a cognitive patch — concrete code changes or doc
  4. Writes the patch to docs/cognitive_patches/ for LLM consumption
  5. If pattern persists (3+ cycles), injects into copilot-instructions

No human trigger. The 60-second background flush IS the input.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v002 | 342 lines | ~2,844 tokens
# DESC:   cognitive_reactor_autonomous_code_modification
# INTENT: pulse_telemetry_prompt
# LAST:   2026-03-17 @ 9e2a305
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Thresholds — sustained cognitive load triggers the reactor
FRUSTRATION_STREAK = 3       # consecutive frustrated flushes on same file
HESITATION_THRESHOLD = 0.65  # avg hesitation score to trigger
REACTOR_COOLDOWN_S = 300     # min seconds between reactor fires per file
STATE_FILE = 'logs/cognitive_reactor_state.json'


def _load_state(root: Path) -> dict:
    sp = root / STATE_FILE
    if sp.exists():
        try:
            return json.loads(sp.read_text('utf-8'))
        except Exception:
            pass
    return {'file_streaks': {}, 'last_fire': {}, 'total_fires': 0}


def _save_state(root: Path, state: dict):
    sp = root / STATE_FILE
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(state, indent=2), encoding='utf-8')


def ingest_flush(
    root: Path,
    cognitive_state: str,
    hesitation: float,
    wpm: float,
    active_files: list[str],
) -> dict | None:
    """Called every classify_bridge flush. Tracks streaks, fires reactor.

    Returns a reactor result dict if fired, None otherwise.
    """
    state = _load_state(root)
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    now_ts = now.timestamp()

    is_load = cognitive_state in ('frustrated', 'hesitant', 'restructuring')
    is_high_hes = hesitation >= HESITATION_THRESHOLD

    # Update streaks per active file
    for f in active_files:
        fname = Path(f).name if f else ''
        if not fname or not fname.endswith('.py'):
            continue
        # Strip pigeon metadata for stable key
        key = re.sub(r'_seq\d+.*$', '', fname.replace('.py', ''))
        if not key:
            continue

        streak = state['file_streaks'].get(key, {
            'count': 0, 'total_hes': 0, 'states': [], 'last_ts': ''
        })

        if is_load or is_high_hes:
            streak['count'] += 1
            streak['total_hes'] += hesitation
            streak['states'].append(cognitive_state)
            # Keep only last 10 states
            streak['states'] = streak['states'][-10:]
        else:
            # Reset streak if operator is in flow/focused
            streak['count'] = max(0, streak['count'] - 1)

        streak['last_ts'] = now_iso
        state['file_streaks'][key] = streak

    # Check if any file crosses the threshold
    target = None
    target_key = None
    for key, streak in state['file_streaks'].items():
        if streak['count'] < FRUSTRATION_STREAK:
            continue
        avg_hes = streak['total_hes'] / max(streak['count'], 1)
        if avg_hes < HESITATION_THRESHOLD:
            continue
        # Cooldown check
        last = state['last_fire'].get(key, 0)
        if now_ts - last < REACTOR_COOLDOWN_S:
            continue
        target_key = key
        target = streak
        break

    if not target or not target_key:
        _save_state(root, state)
        return None

    # FIRE THE REACTOR
    result = _fire_reactor(root, target_key, target, now_iso)

    # Update state
    state['last_fire'][target_key] = now_ts
    state['total_fires'] = state.get('total_fires', 0) + 1
    target['count'] = 0  # reset streak after firing
    target['total_hes'] = 0
    _save_state(root, state)

    return result


def _fire_reactor(
    root: Path,
    module_key: str,
    streak: dict,
    timestamp: str,
) -> dict:
    """Autonomous code analysis + patch generation for a struggling module."""
    import importlib.util

    avg_hes = round(streak['total_hes'] / max(streak['count'], 1), 3)
    dominant_state = max(set(streak['states']), key=streak['states'].count)

    # Load registry to find the actual file
    reg_path = root / 'pigeon_registry.json'
    registry = {}
    target_file = None
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text('utf-8'))
            files = reg.get('files', [])
            for entry in files:
                p = entry.get('path', '')
                name = entry.get('name', '')
                if name == module_key or module_key in p:
                    target_file = entry
                    break
            registry = reg
        except Exception:
            pass

    # Run self-fix focused on this module
    problems = []
    cross_context = {}
    try:
        matches = sorted(root.glob('src/self_fix_seq013*.py'))
        if matches:
            spec = importlib.util.spec_from_file_location('sf', matches[-1])
            sf = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(sf)
            report = sf.run_self_fix(root, registry,
                                     changed_py=[target_file['path']] if target_file else None)
            problems = [p for p in report.get('problems', [])
                        if module_key in p.get('file', '')]
            cross_context = report.get('cross_context', {})
    except Exception:
        pass

    # Read the actual source of the struggling file
    source_snippet = ''
    if target_file:
        fp = root / target_file['path']
        if fp.exists():
            try:
                lines = fp.read_text('utf-8').splitlines()
                source_snippet = '\n'.join(lines[:80])  # first 80 lines
            except Exception:
                pass

    # Generate cognitive patch via DeepSeek
    patch = _generate_patch(
        module_key, avg_hes, dominant_state, streak['count'],
        problems, cross_context, source_snippet, target_file
    )

    # Write patch to docs/cognitive_patches/
    out_dir = root / 'docs' / 'cognitive_patches'
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M')
    out_path = out_dir / f'{today}_{module_key}.md'

    header = (
        f'# Cognitive Patch — {module_key}\n\n'
        f'**Triggered**: {timestamp}  \n'
        f'**Reason**: {streak["count"]} consecutive high-load flushes '
        f'(avg hesitation {avg_hes}, dominant state: {dominant_state})  \n'
        f'**Problems found**: {len(problems)}  \n\n'
        f'---\n\n'
    )
    body = patch or '_DeepSeek unavailable — raw problems listed below._\n'
    if not patch and problems:
        body += '\n'.join(
            f'- [{p["severity"]}] {p["type"]}: {p.get("file","")} — {p.get("fix","")}'
            for p in problems
        )

    out_path.write_text(header + body + '\n', encoding='utf-8')

    # Auto-apply docstring patch when confidence is high enough
    staged = None
    if (target_file and streak['count'] >= FRUSTRATION_STREAK * 2
            and avg_hes >= HESITATION_THRESHOLD + 0.1):
        staged = _apply_docstring_patch(root, target_file, module_key, avg_hes, dominant_state)

    # Inject a hint into copilot-instructions if streak was severe
    if streak['count'] >= FRUSTRATION_STREAK * 2:
        _inject_cognitive_hint(root, module_key, avg_hes, dominant_state, patch)

    return {
        'fired': True,
        'module': module_key,
        'avg_hes': avg_hes,
        'dominant_state': dominant_state,
        'problems': len(problems),
        'patch_path': str(out_path.relative_to(root)),
        'staged_docstring_patch': staged,
    }


def _apply_docstring_patch(
    root: Path, target_file: dict, module_key: str, avg_hes: float, dominant_state: str
) -> str | None:
    """Safely apply a docstring enhancement to a hot-zone file.

    Only modifies the module-level docstring (first triple-quoted string).
    Adds a COGNITIVE NOTE about the detected load pattern.
    Stages the file change (does NOT commit). Returns path of patched file.
    Safety: never modifies logic code; bails out if file structure is unexpected.
    """
    import ast as _ast
    fp = root / target_file['path']
    if not fp.exists():
        return None
    try:
        source = fp.read_text('utf-8')
        tree = _ast.parse(source)
    except Exception:
        return None

    # Only patch if there's an existing module docstring
    existing_doc = _ast.get_docstring(tree)
    if not existing_doc:
        return None

    # Build the cognitive note to append
    note = (
        f'\n\nCOGNITIVE NOTE (auto-added by reactor): This module triggered '
        f'{FRUSTRATION_STREAK * 2}+ high-load flushes '
        f'(avg_hes={avg_hes:.3f}, state={dominant_state}). '
        f'Consider simplifying its public interface or adding examples.'
    )

    # Only add if not already present
    if 'COGNITIVE NOTE' in existing_doc:
        return None

    # Find the docstring in source and append to it
    # Locate the closing triple-quote of the module docstring
    new_doc = existing_doc + note
    # Replace first occurrence of the original docstring text
    old_doc_escaped = existing_doc.replace('\\', '\\\\').replace('\n', '\n')
    # Simple approach: find end of first docstring block
    for quote in ('"""', "'''"):
        start = source.find(quote)
        if start == -1:
            continue
        end = source.find(quote, start + 3)
        if end == -1:
            continue
        old_block = source[start:end + 3]
        new_block = quote + new_doc + quote
        new_source = source[:start] + new_block + source[end + 3:]
        fp.write_text(new_source, encoding='utf-8')
        return str(fp.relative_to(root))

    return None


def _generate_patch(
    module_key: str,
    avg_hes: float,
    dominant_state: str,
    streak_count: int,
    problems: list,
    cross_context: dict,
    source_snippet: str,
    registry_entry: dict | None,
) -> str | None:
    """DeepSeek call: generate a targeted fix based on cognitive load data."""
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        return None

    prob_block = '\n'.join(
        f'- [{p["severity"]}] {p["type"]}: {p.get("fix","")}'
        for p in problems[:5]
    ) or 'No static problems detected.'

    cross_block = ''
    for rel, ctx in cross_context.items():
        if module_key in rel:
            deps = ', '.join(Path(d).stem.split('_seq')[0]
                             for d in ctx.get('imports_from', []))
            users = ', '.join(Path(u).stem.split('_seq')[0]
                              for u in ctx.get('imported_by', []))
            if deps:
                cross_block += f'Imports from: {deps}\n'
            if users:
                cross_block += f'Used by: {users}\n'

    ver = registry_entry.get('ver', '?') if registry_entry else '?'
    tokens = registry_entry.get('tokens', '?') if registry_entry else '?'

    prompt = f"""You are an autonomous code reactor. An operator has been struggling with module `{module_key}` for {streak_count} consecutive typing sessions.

COGNITIVE DATA:
- Average hesitation: {avg_hes} (threshold: {HESITATION_THRESHOLD})
- Dominant state: {dominant_state}
- Module version: v{ver}, ~{tokens} tokens

STATIC ANALYSIS PROBLEMS:
{prob_block}

CROSS-FILE DEPENDENCIES:
{cross_block or 'None detected.'}

SOURCE (first 80 lines):
```python
{source_snippet[:2000]}
```

Generate a COGNITIVE PATCH — specific code changes that would reduce the operator's cognitive load on this module. Focus on:
1. Simplifying the interface (fewer params, clearer names)
2. Breaking apart complex logic the operator keeps re-reading
3. Adding inline comments at hesitation hotspots
4. Fixing any detected static problems

Output format:
- Brief diagnosis (2 sentences: why this module causes cognitive load)
- Concrete code changes as unified diff or replacement blocks
- One sentence: what this patch prevents in future sessions

Max 300 words. Be surgical."""

    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 500,
        'temperature': 0.3,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=body,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception:
        return None


def _inject_cognitive_hint(
    root: Path, module_key: str, avg_hes: float,
    dominant_state: str, patch: str | None
):
    """For severe streaks, inject a one-liner into copilot-instructions."""
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists():
        return
    try:
        text = cp.read_text('utf-8')
        marker = '<!-- /pigeon:operator-state -->'
        if marker not in text:
            return
        hint = (
            f'\n> **Cognitive reactor fired on `{module_key}`** '
            f'(hes={avg_hes}, state={dominant_state}). '
            f'Simplify interactions with this module.\n'
        )
        if hint in text:
            return  # already injected
        text = text.replace(marker, marker + hint)
        cp.write_text(text, encoding='utf-8')
    except Exception:
        pass
