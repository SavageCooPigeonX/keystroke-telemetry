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
# SEQ: 014 | VER: v003 | 416 lines | ~3,529 tokens
# DESC:   cognitive_reactor_autonomous_code_modification
# INTENT: implement_all_18
# LAST:   2026-03-21 @ 068687f
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-30T03:15:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  lower docstring patch threshold + track patches_applied
# EDIT_STATE: harvested
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
    defaults = {'file_streaks': {}, 'last_fire': {}, 'total_fires': 0}
    sp = root / STATE_FILE
    if sp.exists():
        try:
            data = json.loads(sp.read_text('utf-8'))
            if isinstance(data, dict):
                for k, v in defaults.items():
                    data.setdefault(k, v)
                return data
        except Exception:
            pass
    return defaults


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
    if result and result.get('patches_applied'):
        state['patches_applied'] = state.get('patches_applied', 0) + 1
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

    # ── Therapy data: gather rework + composition signals ────────────
    therapy = _gather_therapy_data(root, module_key)

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
        f'**Problems found**: {len(problems)}  \n'
        f'**Rework misses**: {therapy["miss_count"]}/{therapy["total_rework"]}  \n'
    )
    if therapy.get('recent_durations_ms'):
        avg_dur = round(sum(therapy['recent_durations_ms']) / len(therapy['recent_durations_ms']))
        header += f'**Prompt ms**: {", ".join(str(d) for d in therapy["recent_durations_ms"][:5])} (avg {avg_dur}ms)  \n'
    header += '\n---\n\n'
    body = patch or '_DeepSeek unavailable — raw problems listed below._\n'
    if not patch and problems:
        body += '\n'.join(
            f'- [{p["severity"]}] {p["type"]}: {p.get("file","")} — {p.get("fix","")}'
            for p in problems
        )
    # Append therapy notes
    if therapy['notes']:
        body += '\n\n## Therapy Notes\n\n' + '\n'.join(
            f'- {n}' for n in therapy['notes'])

    out_path.write_text(header + body + '\n', encoding='utf-8')

    # Auto-apply docstring patch — fires on every reactor activation now
    # (reactor already gates on FRUSTRATION_STREAK + HESITATION_THRESHOLD + cooldown)
    staged = None
    if target_file:
        staged = _apply_docstring_patch(root, target_file, module_key, avg_hes, dominant_state)

    # Inject therapy into copilot-instructions (always, not just severe)
    _inject_cognitive_hint(root, module_key, avg_hes, dominant_state, patch, therapy)

    return {
        'fired': True,
        'module': module_key,
        'avg_hes': avg_hes,
        'dominant_state': dominant_state,
        'problems': len(problems),
        'patch_path': str(out_path.relative_to(root)),
        'staged_docstring_patch': staged,
        'patches_applied': 1 if staged else 0,
        'therapy': therapy,
    }


def _gather_therapy_data(root: Path, module_key: str) -> dict:
    """Read rework log + composition + heat map for data-driven coaching."""
    therapy = {
        'miss_count': 0, 'total_rework': 0,
        'worst_queries': [], 'deleted_words': [],
        'recent_states': [], 'notes': [],
        'recent_durations_ms': [],
    }
    # Rework log — find misses related to this module
    try:
        rw_path = root / 'rework_log.json'
        if rw_path.exists():
            rw = json.loads(rw_path.read_text('utf-8'))
            entries = rw if isinstance(rw, list) else rw.get('entries', [])
            therapy['total_rework'] = len(entries)
            for e in entries[-50:]:
                if e.get('verdict') == 'miss':
                    therapy['miss_count'] += 1
                    q = e.get('query', '')[:80]
                    if q and module_key in q.lower():
                        therapy['worst_queries'].append(q)
            # Also collect recent misses regardless of module
            recent_misses = [e for e in entries[-20:] if e.get('verdict') == 'miss']
            for m in recent_misses[-3:]:
                therapy['worst_queries'].append(m.get('query', '')[:80])
    except Exception:
        pass
    # Chat compositions — deleted words (PRIMARY source, updated every flush)
    try:
        comp = root / 'logs' / 'chat_compositions.jsonl'
        if comp.exists():
            lines = comp.read_text('utf-8').strip().splitlines()[-30:]
            seen = set()
            cutoff = time.time() - 600  # only last 10 minutes
            for line in reversed(lines):  # most recent first
                try:
                    c = json.loads(line)
                    # Skip entries older than 10 minutes
                    ts_str = c.get('ts', '')
                    if ts_str:
                        from datetime import datetime as _dt, timezone as _tz
                        try:
                            entry_ts = _dt.fromisoformat(ts_str).timestamp()
                            if entry_ts < cutoff:
                                continue
                        except (ValueError, TypeError):
                            pass
                    # Skip entries with no deleted words
                    dws = c.get('deleted_words', [])
                    if not dws:
                        continue
                    for dw in dws:
                        w = dw.get('word', '') if isinstance(dw, dict) else str(dw)
                        if len(w) >= 2 and w not in seen:
                            seen.add(w)
                            therapy['deleted_words'].append(w)
                except Exception:
                    pass
            therapy['deleted_words'] = therapy['deleted_words'][:8]
    except Exception:
        pass
    # Composition durations (ms per prompt)
    try:
        comp = root / 'logs' / 'chat_compositions.jsonl'
        if comp.exists():
            dur_lines = comp.read_text('utf-8').strip().splitlines()[-10:]
            for line in reversed(dur_lines):
                try:
                    c = json.loads(line)
                    dur = c.get('duration_ms', 0)
                    if dur and dur > 0:
                        therapy['recent_durations_ms'].append(int(dur))
                except Exception:
                    pass
            therapy['recent_durations_ms'] = therapy['recent_durations_ms'][:5]
    except Exception:
        pass
    # Build therapy notes
    if therapy['miss_count'] > 0:
        rate = round(therapy['miss_count'] / max(therapy['total_rework'], 1) * 100)
        therapy['notes'].append(
            f'Rework miss rate: {rate}% ({therapy["miss_count"]}/{therapy["total_rework"]})')
    if therapy['worst_queries']:
        therapy['notes'].append(
            f'Worst queries: {"; ".join(therapy["worst_queries"][:3])}')
    if therapy['deleted_words']:
        therapy['notes'].append(
            f'Unsaid intent (deleted words): {", ".join(str(w) for w in therapy["deleted_words"][:5])}')
    if therapy['recent_durations_ms']:
        avg_dur = round(sum(therapy['recent_durations_ms']) / len(therapy['recent_durations_ms']))
        therapy['notes'].append(
            f'Prompt composition time: {" / ".join(str(d) + "ms" for d in therapy["recent_durations_ms"][:5])} (avg {avg_dur}ms)')
    return therapy


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
        f'{streak_count}+ high-load flushes '
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
    dominant_state: str, patch: str | None,
    therapy: dict | None = None,
):
    """Inject data-driven therapy block into copilot-instructions."""
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists():
        return
    try:
        text = cp.read_text('utf-8')
        marker = '<!-- /pigeon:operator-state -->'
        if marker not in text:
            return
        # Remove any previous reactor hints to keep it fresh
        import re as _re
        text = _re.sub(
            r'\n> \*\*Cognitive reactor fired.*?\n(?:> .*\n)*',
            '', text)
        # Build therapy block
        dur_str = ''
        if therapy and therapy.get('recent_durations_ms'):
            avg_dur = round(sum(therapy['recent_durations_ms']) / len(therapy['recent_durations_ms']))
            dur_str = f', avg_prompt={avg_dur}ms'
        lines = [
            f'\n> **Cognitive reactor fired on `{module_key}`** '
            f'(hes={avg_hes}, state={dominant_state}{dur_str})'
        ]
        if therapy:
            if therapy.get('notes'):
                for n in therapy['notes'][:4]:
                    lines.append(f'> - {n}')
            if therapy.get('deleted_words'):
                lines.append(
                    f'> - Operator unsaid: '
                    f'{", ".join(str(w) for w in therapy["deleted_words"][:4])}')
        lines.append(
            f'> **Directive**: When `{module_key}` appears in context, '
            f'provide complete code blocks (not snippets), '
            f'proactively explain cross-module dependencies, '
            f'and address the unsaid topics above without being asked.')
        hint = '\n'.join(lines) + '\n'
        text = text.replace(marker, marker + hint)
        cp.write_text(text, encoding='utf-8')
    except Exception:
        pass
