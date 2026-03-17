"""git_plugin.py — Post-commit pigeon auto-rename daemon.

Fires after every git commit.  Renames touched pigeon files with
living metadata so `ls` shows what each file does and what last changed.

The filename IS the changelog:
  noise_filter_seq007_v004_d0315__filter_live_noise_lc_fixed_timeout.py
  ├─ filter_live_noise     = what this file DOES   (from docstring)
  └─ fixed_timeout         = what was LAST CHANGED (from commit message)

Pipeline:
  1. Skip [pigeon-auto] commits (prevent infinite loops)
  2. Parse commit message → intent slug (max 3 words)
  3. For each changed pigeon file:
     · Docstring → desc slug (what the file IS)
     · Bump version + update date
     · Build import_map (old_module → new_module)
  4. Rewrite all imports across codebase (BEFORE renaming files)
  5. Rename files on disk
  6. Inject prompt box headers + log sessions
  7. Update pigeon_registry.json
  8. Rebuild all MANIFEST.md files
  9. Refresh .github/copilot-instructions.md auto-index
 10. Call DeepSeek: changed files + registry churn + operator typing history
     → synthesize behavioral coaching prose → operator_coaching.md
 11. Refresh .github/copilot-instructions.md operator state (LLM prose if available)
 12. Auto-commit [pigeon-auto]

Install: .git/hooks/post-commit calls `python -m pigeon_compiler.git_plugin`
"""
import ast
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from pigeon_compiler.rename_engine import (
    extract_desc_slug,
    load_registry,
    save_registry,
    build_pigeon_filename,
    parse_pigeon_stem,
    bump_version,
    rewrite_all_imports,
    build_all_manifests,
    validate_imports,
)
from pigeon_compiler.pigeon_limits import is_excluded
from pigeon_compiler.session_logger import log_session, count_sessions

# ── Token estimation ─────────────────────────────────────
# GPT/Claude average ≈ 1 token per 4 chars.  We count the file
# content to give a rough cost estimate per file per mutation.
TOKEN_RATIO = 4  # chars per token


def _estimate_tokens(text: str) -> int:
    """Estimate LLM token count from raw text (1 tok ≈ 4 chars)."""
    return max(1, len(text) // TOKEN_RATIO)


# ── Prompt box regex ────────────────────────────────────
BOX_RE = re.compile(
    r'^# ── pigeon ─[^\n]*\n(?:# [^\n]*\n)*# ─{10,}─*\n',
    re.MULTILINE,
)
_AUTO_INDEX_RE = re.compile(
    r'<!-- pigeon:auto-index -->.*?<!-- /pigeon:auto-index -->',
    re.DOTALL,
)
_ROOT_DEBUG = re.compile(r'^_')


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _git(*args: str) -> str:
    r = subprocess.run(
        ['git', *args],
        capture_output=True, text=True, encoding='utf-8',
        cwd=str(_root()), timeout=30,
    )
    return r.stdout.strip()


def _load_glob_module(root: Path, folder: str, pattern: str):
    """Dynamically import a pigeon module by glob pattern (filenames mutate)."""
    import importlib.util
    matches = sorted((root / folder).glob(f'{pattern}.py'))
    if not matches:
        return None
    spec = importlib.util.spec_from_file_location(matches[-1].stem, matches[-1])
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Git helpers ─────────────────────────────────────────

def _commit_msg() -> str:
    return _git('log', '-1', '--format=%B')


def _commit_hash() -> str:
    return _git('log', '-1', '--format=%h')


def _changed_files() -> list[str]:
    try:
        raw = _git('diff', '--name-only', 'HEAD~1', 'HEAD')
        return [f for f in raw.splitlines() if f.strip()]
    except Exception:
        return []


def _file_diff_stat(rel: str) -> str:
    """Get compact diff stat for one file (e.g. '+12 -3')."""
    try:
        raw = _git('diff', '--numstat', 'HEAD~1', 'HEAD', '--', rel)
        if raw.strip():
            parts = raw.strip().split('\t')
            if len(parts) >= 2:
                return f'+{parts[0]} -{parts[1]}'
    except Exception:
        pass
    return ''


# ── Intent parsing ──────────────────────────────────────

def _parse_intent(msg: str) -> str:
    """Commit message → 3-word intent slug.

    'feat: Hush spy mode + hero image' → 'hush_spy_mode'
    'fix: apply directory hero image'  → 'fix_directory_hero'
    """
    line = msg.split('\n')[0].strip()
    m = re.match(
        r'^(?:feat|fix|chore|refactor|docs|test|ci)(?:\([^)]+\))?:\s*', line)
    if m:
        line = line[m.end():]
    slug = re.sub(r'[^a-z0-9]+', '_', line.lower()).strip('_')
    words = [w for w in slug.split('_') if w][:3]
    return '_'.join(words) or 'manual_edit'


# ── Prompt box ──────────────────────────────────────────

def _build_box(entry: dict, h: str, lines: int, tokens: int = 0,
               sessions: int = 0) -> str:
    return (
        f'# ── pigeon ────────────────────────────────────\n'
        f'# SEQ: {entry["seq"]:03d} | VER: v{entry["ver"]:03d} | {lines} lines | ~{tokens:,} tokens\n'
        f'# DESC:   {entry.get("desc") or "(none)"}\n'
        f'# INTENT: {entry.get("intent") or "(none)"}\n'
        f'# LAST:   {datetime.now(timezone.utc).strftime("%Y-%m-%d")} @ {h}\n'
        f'# SESSIONS: {sessions}\n'
        f'# ──────────────────────────────────────────────\n'
    )


def _inject_box(fp: Path, entry: dict, h: str, root: Path | None = None):
    try:
        text = fp.read_text(encoding='utf-8')
    except Exception:
        return
    tokens = _estimate_tokens(text)
    sessions = 0
    if root:
        sessions = count_sessions(root, entry.get('name', ''), entry.get('seq', 0))
    box = _build_box(entry, h, len(text.splitlines()), tokens, sessions)
    if '# ── pigeon ─' in text:
        text = BOX_RE.sub(box, text, count=1)
    else:
        end = _ds_end(text)
        if end >= 0:
            text = text[:end] + '\n' + box + text[end:]
        else:
            text = box + text
    fp.write_text(text, encoding='utf-8')


def _ds_end(text: str) -> int:
    """Character index right after the module docstring."""
    try:
        tree = ast.parse(text)
        if not tree.body:
            return -1
        n = tree.body[0]
        if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str)):
            return sum(len(l) + 1 for l in text.split('\n')[:n.end_lineno])
    except SyntaxError:
        pass
    return -1


# ── Copilot instructions auto-index ────────────────────

def _refresh_copilot_instructions(root: Path, registry: dict, processed: int) -> bool:
    """Rebuild the <!-- pigeon:auto-index --> block in .github/copilot-instructions.md.

    Only updates the auto-index section — everything hand-written is preserved.
    Fires on every commit that touches pigeon .py files so the index stays live.
    """
    cp_path = root / '.github' / 'copilot-instructions.md'
    if not cp_path.exists():
        return False

    # Group registry entries by folder
    groups: dict[str, list] = {}
    for path, entry in registry.items():
        folder = str(Path(path).parent).replace('\\', '/')
        groups.setdefault(folder, []).append({
            'name':   entry.get('name', ''),
            'seq':    entry.get('seq', 0),
            'desc':   (entry.get('desc') or '').replace('_', ' ')[:52],
            'tokens': entry.get('tokens', 0),
        })

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    block_lines = [
        '<!-- pigeon:auto-index -->',
        f'*Auto-updated {today} — {len(registry)} modules tracked | {processed} touched this commit*',
        '',
    ]
    for folder in sorted(groups.keys()):
        items = sorted(groups[folder], key=lambda e: (e['seq'], e['name']))
        block_lines.append(f'**{folder}/** — {len(items)} module(s)')
        block_lines.append('')
        block_lines.append('| Search pattern | Desc | Tokens |')
        block_lines.append('|---|---|---:|')
        for item in items:
            pat = f'`{item["name"]}_seq{item["seq"]:03d}*`'
            block_lines.append(f'| {pat} | {item["desc"]} | ~{item["tokens"]:,} |')
        block_lines.append('')
    block_lines.append('<!-- /pigeon:auto-index -->')
    block = '\n'.join(block_lines)

    try:
        text = cp_path.read_text(encoding='utf-8')
    except Exception:
        return False

    if _AUTO_INDEX_RE.search(text):
        new_text = _AUTO_INDEX_RE.sub(block, text)
    else:
        new_text = text.rstrip() + '\n\n---\n\n### Full Module Index\n\n' + block + '\n'

    cp_path.write_text(new_text, encoding='utf-8')
    return True


# ── Operator state injection ─────────────────────────────

_OPERATOR_STATE_RE = re.compile(
    r'<!-- pigeon:operator-state -->.*?<!-- /pigeon:operator-state -->',
    re.DOTALL,
)

_STATE_HINTS: dict[str, str] = {
    'frustrated':    'concise answers, 2-3 options max, bullets, lead with solution',
    'hesitant':      'warm tone, anticipate intent, ask one follow-up question',
    'flow':          'match energy — full technical depth, no hand-holding',
    'focused':       'thorough and structured, match effort level',
    'restructuring': 'precise, use headers/numbered lists to mirror their effort',
    'abandoned':     'welcoming, direct — they re-approached after backing off',
    'neutral':       'standard response style',
}


def _parse_operator_profile(root: Path) -> dict | None:
    """Parse operator_profile.md → metrics dict. Returns None if file missing."""
    prof_path = root / 'operator_profile.md'
    if not prof_path.exists():
        return None
    try:
        text = prof_path.read_text(encoding='utf-8')
    except Exception:
        return None

    def _re(pattern: str, default: str) -> str:
        m = re.search(pattern, text)
        return m.group(1) if m else default

    return {
        'messages':    int(_re(r'(\d+) messages ingested', '0') or '0'),
        'dominant':    _re(r'\*\*Dominant state:\s*(\w+)\*\*', 'neutral'),
        'submit_rate': int(_re(r'\*\*Submit rate:.*?\((\d+)%\)\*\*', '0') or '0'),
        'avg_wpm':     float(_re(r'\|\s*WPM\s*\|[^|]+\|[^|]+\|\s*([\d.]+)\s*\|', '0') or '0'),
        'avg_del':     float(_re(r'\|\s*Deletion\s*%\s*\|[^|]+\|[^|]+\|\s*([\d.]+)%', '0') or '0'),
        'avg_hes':     float(_re(r'\|\s*Hesitation\s*\|[^|]+\|[^|]+\|\s*([\d.]+)\s*\|', '0') or '0'),
        'active_hours': _re(r'\*\*Active hours:\*\*\s*(.+)', '').strip(),
    }


# ── Commit-time LLM coaching synthesis ──────────────────────────────────────

def _load_operator_history(root: Path) -> list:
    """Extract message history from operator_profile.md DATA block."""
    prof_path = root / 'operator_profile.md'
    if not prof_path.exists():
        return []
    try:
        text = prof_path.read_text(encoding='utf-8')
        m = re.search(r'<!--\s*DATA\s*(.*?)\s*DATA\s*-->', text, re.DOTALL)
        if m:
            data = json.loads(m.group(1).strip())
            return data.get('history', [])
    except Exception:
        pass
    return []


def _registry_churn(registry: dict, top_n: int = 8) -> list[dict]:
    """Return top_n most-versioned modules — these are the pain points."""
    entries = list(registry.values())
    entries.sort(key=lambda e: e.get('ver', 1), reverse=True)
    return [
        {'module': e['name'], 'seq': e.get('seq'), 'ver': e.get('ver', 1),
         'tokens': e.get('tokens', 0), 'desc': e.get('desc', ''), 'intent': e.get('intent', '')}
        for e in entries[:top_n]
    ]


def _build_commit_coaching_prompt(
    intent: str,
    renames: list,
    box_only: list,
    registry: dict,
    history: list,
    rework_stats: dict | None = None,
    query_mem: dict | None = None,
    heat_map: dict | None = None,
) -> str:
    """Build the DeepSeek prompt combining commit context + all deep operator signals."""
    from collections import Counter

    # Changed files summary
    file_lines = []
    for old_rel, new_rel, entry, tokens, _ in renames:
        ver = entry.get('ver', 1)
        file_lines.append(f'  RENAMED  v{ver} {tokens}tok  {Path(old_rel).name} → {Path(new_rel).name}')
    for abs_p, entry, old_rel, tokens, _ in box_only:
        ver = entry.get('ver', 1)
        file_lines.append(f'  UPDATED  v{ver} {tokens}tok  {Path(old_rel).name}')
    files_block = '\n'.join(file_lines) or '  (none parsed)'

    # Registry churn — top pain-point modules
    churn = _registry_churn(registry)
    churn_lines = '\n'.join(
        f'  {c["module"]} seq{c["seq"]} v{c["ver"]}  {c["tokens"]}tok  [{c["desc"]}] last: {c["intent"]}'
        for c in churn
    )

    # Operator profile summary
    n = len(history)
    submitted = sum(1 for h in history if h.get('submitted', True))
    states = [h.get('state', 'neutral') for h in history]
    state_dist = dict(Counter(states).most_common())
    wpms = [h['wpm'] for h in history if 'wpm' in h]
    hess = [h['hesitation'] for h in history if 'hesitation' in h]
    dels = [h['del_ratio'] for h in history if 'del_ratio' in h]
    slots = [h.get('slot', '') for h in history if h.get('slot')]
    avg_wpm = round(sum(wpms) / len(wpms), 1) if wpms else 0
    avg_hes = round(sum(hess) / len(hess), 3) if hess else 0
    avg_del = round(sum(dels) / len(dels) * 100, 1) if dels else 0
    slot_dist = dict(Counter(slots).most_common(3))
    recent = history[-8:]
    recent_block = '\n'.join(
        f'  msg{i+1}: {h.get("state","?")} wpm={h.get("wpm",0)} '
        f'del={round(h.get("del_ratio",0)*100)}% hes={h.get("hesitation",0)} '
        f'sub={h.get("submitted",True)} slot={h.get("slot","?")}'
        for i, h in enumerate(recent)
    )

    # Deep signal blocks (optional — populated after a few sessions)
    rework_block = ''
    if rework_stats:
        worst = rework_stats.get('worst_queries', [])
        rework_block = (
            f'\nAI RESPONSE QUALITY (post-response rework rate):\n'
            f'  miss_rate={rework_stats.get("miss_rate","?")}  '
            f'({rework_stats.get("miss_count","?")} misses / '
            f'{rework_stats.get("total_responses","?")} responses)\n'
            f'  worst queries: {worst[:3]}'
        )

    gaps_block = ''
    if query_mem and query_mem.get('persistent_gaps'):
        gaps = '\n'.join(
            f'  [{g["count"]}x] {g["query"]}'
            for g in query_mem['persistent_gaps']
        )
        abandon_lines = '\n'.join(
            f'  {a}' for a in query_mem.get('recent_abandons', [])[:3]
        ) or '  none'
        gaps_block = (
            f'\nPERSISTENT GAPS (operator keeps asking same thing → AI keeps failing):\n'
            f'{gaps}\n'
            f'ABANDONED/UNSAID recent:\n{abandon_lines}'
        )

    heat_block = ''
    if heat_map and heat_map.get('complex_files'):
        cf = '\n'.join(
            f'  {c["module"]} avg_hes={c["avg_hes"]} avg_wpm={c["avg_wpm"]} '
            f'misses={c["miss_count"]}/{c["samples"]}'
            for c in heat_map['complex_files'][:5]
        )
        mf = '\n'.join(
            f'  {m["module"]} miss_rate={m["miss_rate"]}'
            for m in heat_map.get('high_miss_files', [])[:3]
        ) or '  none'
        heat_block = (
            f'\nFILE COMPLEXITY DEBT (high hesitation when working on these):\n{cf}\n'
            f'HIGH AI-MISS FILES:\n{mf}'
        )

    return f"""You are a behavioral AI coach embedded in a VS Code extension.
Your output is injected DIRECTLY into a Copilot system prompt — write INSTRUCTIONS for the AI, not a report.

THIS COMMIT (intent: {intent}):
{files_block}

REGISTRY CHURN — most-mutated modules (recurring pain points the operator keeps revisiting):
{churn_lines}

OPERATOR TYPING HISTORY ({n} total messages, {submitted} submitted):
  state distribution: {state_dist}
  avg WPM: {avg_wpm} | avg hesitation: {avg_hes} | avg deletion rate: {avg_del}%
  active time slots: {slot_dist}
  recent 8 messages:
{recent_block}{rework_block}{gaps_block}{heat_block}

Write behavioral coaching instructions for Copilot. Requirements:
1. One sentence: what this operator just built + what their typing patterns reveal about HOW they work
2. 4-6 concrete bullets: exactly how Copilot should respond in the next session
3. Name specific modules from the churn list that keep getting touched — what should Copilot anticipate?
4. If rework/gap data present: prescribe explicit strategies for the failing areas
5. If typing shows frustration/hesitation on heavy-edit commits → call that out and prescribe a response
6. One sentence: what this operator is most likely building toward next

Be surgical and specific. Every word must change AI behavior. No generic advice. Max 250 words. Plain markdown bullets only."""


def _load_deep_signals(root: Path) -> dict:
    """Load rework, query memory, and heat map stores for narrative + coaching."""
    signals: dict = {}
    try:
        rw_path = root / 'rework_log.json'
        if rw_path.exists():
            raw = json.loads(rw_path.read_text('utf-8'))
            entries = raw if isinstance(raw, list) else raw.get('entries', [])
            total = len(entries)
            misses = [e for e in entries if e.get('verdict') == 'miss']
            miss_rate = round(len(misses) / max(total, 1), 3)
            worst = sorted(misses, key=lambda e: e.get('rework_score', 0), reverse=True)
            signals['rework'] = {
                'miss_rate': miss_rate, 'miss_count': len(misses),
                'total_responses': total,
                'worst_queries': [e.get('query_text', '')[:60] for e in worst[:3]],
            }
    except Exception:
        pass
    try:
        qm_path = root / 'query_memory.json'
        if qm_path.exists():
            raw = json.loads(qm_path.read_text('utf-8'))
            entries = raw.get('entries', raw.get('queries', []))
            if isinstance(entries, list):
                from collections import Counter
                fp_counts = Counter(e.get('fingerprint', '') for e in entries if e.get('fingerprint'))
                gaps = [
                    {'query': next(
                        (e.get('text', e.get('query_text', ''))[:80]
                         for e in entries if e.get('fingerprint') == fp), fp),
                     'count': c}
                    for fp, c in fp_counts.most_common(5) if c >= 3
                ]
                abandons = [
                    e.get('text', e.get('query_text', ''))[:80]
                    for e in reversed(entries) if not e.get('submitted', True)
                ][:5]
                signals['query'] = {'persistent_gaps': gaps, 'recent_abandons': abandons}
    except Exception:
        pass
    try:
        hm_path = root / 'file_heat_map.json'
        if hm_path.exists():
            raw = json.loads(hm_path.read_text('utf-8'))
            modules = {k: v for k, v in raw.items() if isinstance(v, dict)} if isinstance(raw, dict) else {}
            complex_files = sorted(
                [{'module': n,
                  'avg_hes': round(v.get('total_hes', 0) / max(v.get('samples', 1), 1), 3),
                  'avg_wpm': round(v.get('total_wpm', 0) / max(v.get('samples', 1), 1), 1),
                  'miss_count': v.get('miss_count', 0),
                  'samples': v.get('samples', 0)}
                 for n, v in modules.items()],
                key=lambda x: x['avg_hes'], reverse=True)
            high_hes = [c for c in complex_files if c['avg_hes'] >= 0.45]
            miss_files = [{'module': c['module'],
                           'miss_rate': round(c['miss_count'] / max(c['samples'], 1), 2)}
                          for c in complex_files if c['miss_count'] > 0]
            signals['heat'] = {'complex_files': high_hes[:6], 'high_miss_files': miss_files[:4]}
    except Exception:
        pass
    return signals


def _call_deepseek_sync(prompt: str, api_key: str, max_tokens: int = 350) -> str | None:
    """Synchronous DeepSeek call via stdlib urllib — no external deps."""
    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': max_tokens,
        'temperature': 0.35,
    }).encode('utf-8')
    req = urllib.request.Request(
        'https://api.deepseek.com/chat/completions',
        data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {api_key}'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception:
        return None


def _generate_commit_coaching(
    root: Path,
    intent: str,
    renames: list,
    box_only: list,
    registry: dict,
) -> bool:
    """Synthesize behavioral coaching at commit time using full codebase + operator context.

    Combines changed files, registry churn, operator typing biography, and deep
    signal stores (rework rate, persistent gaps, file complexity debt) into a
    single DeepSeek prompt. The resulting prose is written to operator_coaching.md
    and injected into copilot-instructions.md by _refresh_operator_state().
    """
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        return False
    history = _load_operator_history(root)
    if not history:
        return False

    # Load deep signal stores (optional — gracefully absent before first session)
    rework_stats: dict | None = None
    query_mem: dict | None = None
    heat_map: dict | None = None
    try:
        rw_path = root / 'rework_log.json'
        if rw_path.exists():
            raw = json.loads(rw_path.read_text('utf-8'))
            # rework_log.json is a plain JSON array
            entries = raw if isinstance(raw, list) else raw.get('entries', [])
            total = len(entries)
            misses = [e for e in entries if e.get('verdict') == 'miss']
            miss_rate = round(len(misses) / max(total, 1), 3)
            worst = sorted(misses, key=lambda e: e.get('rework_score', 0), reverse=True)
            rework_stats = {
                'miss_rate': miss_rate,
                'miss_count': len(misses),
                'total_responses': total,
                'worst_queries': [e.get('query_text', '')[:60] for e in worst[:3]],
            }
    except Exception:
        pass
    try:
        qm_path = root / 'query_memory.json'
        if qm_path.exists():
            raw = json.loads(qm_path.read_text('utf-8'))
            entries = raw.get('entries', []) if isinstance(raw, dict) else []
            from collections import Counter
            fp_counts = Counter(e.get('fingerprint', '') for e in entries if e.get('fingerprint'))
            RECUR = 3
            gaps = [
                {'query': next(
                    (e.get('query_text', '')[:80] for e in entries if e.get('fingerprint') == fp), fp
                ), 'count': c}
                for fp, c in fp_counts.most_common(5) if c >= RECUR
            ]
            abandons = [
                e.get('query_text', '')[:80]
                for e in reversed(entries) if not e.get('submitted', True)
            ][:5]
            query_mem = {'persistent_gaps': gaps, 'recent_abandons': abandons}
    except Exception:
        pass
    try:
        hm_path = root / 'file_heat_map.json'
        if hm_path.exists():
            raw = json.loads(hm_path.read_text('utf-8'))
            # file_heat_map.json is a flat {module_name: {samples,avg_hes,...}} dict
            modules = {k: v for k, v in raw.items() if isinstance(v, dict)} if isinstance(raw, dict) else {}
            HIGH_HES = 0.45
            complex_files = sorted(
                [
                    {
                        'module': name,
                        'avg_hes': round(v.get('total_hes', 0) / max(v.get('samples', 1), 1), 3),
                        'avg_wpm': round(v.get('total_wpm', 0) / max(v.get('samples', 1), 1), 1),
                        'miss_count': v.get('miss_count', 0),
                        'samples': v.get('samples', 0),
                    }
                    for name, v in modules.items()
                ],
                key=lambda x: x['avg_hes'], reverse=True
            )
            high_hes = [c for c in complex_files if c['avg_hes'] >= HIGH_HES]
            miss_files = [
                {'module': c['module'],
                 'miss_rate': round(c['miss_count'] / max(c['samples'], 1), 2)}
                for c in complex_files if c['miss_count'] > 0
            ]
            heat_map = {'complex_files': high_hes[:6], 'high_miss_files': miss_files[:4]}
    except Exception:
        pass

    prompt = _build_commit_coaching_prompt(
        intent, renames, box_only, registry, history,
        rework_stats, query_mem, heat_map,
    )
    prose = _call_deepseek_sync(prompt, api_key)
    if not prose:
        return False
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    submitted_count = sum(1 for h in history if h.get('submitted', True))
    content = (
        f'<!-- coaching:count={submitted_count} -->\n'
        f'<!-- Auto-generated by git_plugin at commit · {today} · intent: {intent} -->\n'
        f'{prose}\n'
        f'<!-- /coaching -->\n'
    )
    (root / 'operator_coaching.md').write_text(content, encoding='utf-8')
    return True



def _load_coaching_prose(root: Path) -> str | None:
    """Load LLM-generated coaching prose from operator_coaching.md if present."""
    coaching_path = root / 'operator_coaching.md'
    if not coaching_path.exists():
        return None
    try:
        text = coaching_path.read_text(encoding='utf-8')
        m = re.search(r'<!-- coaching:count=\d+ -->\n.*?\n(.*?)<!-- /coaching -->', text, re.DOTALL)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None


def _refresh_operator_state(root: Path) -> bool:
    """Rebuild <!-- pigeon:operator-state --> block in copilot-instructions.md.

    Priority:
      1. LLM-synthesized prose from operator_coaching.md (generated every 8 submitted msgs)
      2. Static template built from operator_profile.md metrics (always available)

    This lets the block evolve from raw stats → rich behavioral coaching over time
    as the operator accumulates enough history for the LLM to detect real patterns.
    """
    cp_path = root / '.github' / 'copilot-instructions.md'
    if not cp_path.exists():
        return False

    prof = _parse_operator_profile(root)
    if not prof or prof['messages'] == 0:
        return False

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    dominant = prof['dominant']

    # ── Try LLM-generated prose first ──────────────────────────────────────
    coaching_prose = _load_coaching_prose(root)
    if coaching_prose:
        lines = [
            '<!-- pigeon:operator-state -->',
            '## Live Operator State',
            '',
            f'*Auto-updated {today} · {prof["messages"]} message(s) · LLM-synthesized*',
            '',
            (f'**Dominant: `{dominant}`** '
             f'| Submit: {prof["submit_rate"]}% '
             f'| WPM: {prof["avg_wpm"]:.1f} '
             f'| Del: {prof["avg_del"]:.1f}% '
             f'| Hes: {prof["avg_hes"]:.3f}'),
            '',
            coaching_prose,
            '',
            '<!-- /pigeon:operator-state -->',
        ]
        block = '\n'.join(lines)
    else:
        # ── Static template fallback (first <8 messages) ────────────────────
        hint = _STATE_HINTS.get(dominant, _STATE_HINTS['neutral'])
        lines = [
            '<!-- pigeon:operator-state -->',
            '## Live Operator State',
            '',
            f'*Auto-updated {today} · {prof["messages"]} message(s) in profile*',
            '',
            (f'**Dominant: `{dominant}`** '
             f'| Submit: {prof["submit_rate"]}% '
             f'| WPM: {prof["avg_wpm"]:.1f} '
             f'| Del: {prof["avg_del"]:.1f}% '
             f'| Hes: {prof["avg_hes"]:.3f}'),
            '',
            '**Behavioral tunes for this session:**',
            f'- **{dominant}** → {hint}',
        ]
        if prof['avg_wpm'] < 45:
            lines.append('- WPM < 45 → prefer bullets and code blocks over dense prose')
        if prof['avg_del'] > 30:
            lines.append('- Deletion ratio > 30% → high rethinking; consider asking "what specifically do you need?"')
        if prof['submit_rate'] < 60:
            lines.append(
                f'- Submit rate {prof["submit_rate"]}% → messages often abandoned; '
                'check if previous answer landed before going deep'
            )
        if prof['avg_hes'] > 0.4:
            lines.append('- Hesitation > 0.4 → uncertain operator; proactively offer alternatives or examples')
        if prof['active_hours']:
            lines.append(f'- Active hours: {prof["active_hours"]}')
        lines.append('<!-- /pigeon:operator-state -->')
        block = '\n'.join(lines)

    try:
        text = cp_path.read_text(encoding='utf-8')
    except Exception:
        return False

    if not _OPERATOR_STATE_RE.search(text):
        return False  # Placeholder not present — don't auto-insert, location is hand-chosen

    cp_path.write_text(_OPERATOR_STATE_RE.sub(block, text), encoding='utf-8')
    return True


# ── Main pipeline ───────────────────────────────────────


def _run_post_commit_extras(root, intent, h, changed_files, registry, msg,
                            renames=None, box_only=None, cross_context=None):
    """Run narrative, coaching, operator-state for ANY commit."""
    renames = renames or []
    box_only = box_only or []

    # Auto-reconstruct prompt compositions from os_keystrokes before narrative
    try:
        recon_mod = _load_glob_module(root, 'src', 'prompt_recon_seq016*')
        if recon_mod:
            new_entries = recon_mod.reconstruct_all(root)
            if new_entries:
                print(f'  🔬 prompt recon: {len(new_entries)} new composition(s)')
            # Track copilot prompt mutations
            mutations = recon_mod.track_copilot_prompt_mutations(root)
            mc = mutations.get('total_mutations', 0)
            if mc:
                print(f'  🧬 copilot prompt: {mc} mutations tracked')
    except Exception as e:
        print(f'  ⚠️  prompt recon: {e}')

    # Push narrative — include ALL changed code files, not just pigeon
    try:
        narr_mod = _load_glob_module(root, 'src', 'push_narrative_seq012*')
        if narr_mod:
            deep = _load_deep_signals(root)
            narr_path = narr_mod.generate_push_narrative(
                root, intent, h, changed_files, registry,
                rework_stats=deep.get('rework'),
                query_mem=deep.get('query'),
                heat_map=deep.get('heat'),
                cross_context=cross_context or {},
            )
            if narr_path:
                print(f'  📖 push narrative → {narr_path.relative_to(root)}')
    except Exception as e:
        print(f'  ⚠️  push narrative: {e}')

    # Generate LLM coaching at commit time
    try:
        coaching_ok = _generate_commit_coaching(
            root, intent, renames, box_only, registry
        )
        if coaching_ok:
            print('  🧠 commit coaching synthesized → operator_coaching.md')
    except Exception as e:
        print(f'  ⚠️  commit coaching: {e}')

    try:
        if _refresh_operator_state(root):
            print('  🧠 operator-state section updated in copilot-instructions.md')
    except Exception as e:
        print(f'  ⚠️  operator-state refresh: {e}')

    # Dynamic task-context injection — steers Copilot's CoT reasoning
    try:
        dyn_mod = _load_glob_module(root, 'src', 'dynamic_prompt_seq017*')
        if dyn_mod and dyn_mod.inject_task_context(root):
            print('  🎯 task-context injected into copilot-instructions.md')
    except Exception as e:
        print(f'  ⚠️  task-context injection: {e}')


def run():
    root = _root()
    msg = _commit_msg()

    if '[pigeon-auto]' in msg:
        return

    h = _commit_hash()
    intent = _parse_intent(msg)
    changed = _changed_files()
    if not changed:
        return

    registry = load_registry(root)
    renames = []        # (old_rel, new_rel, entry, tokens_before, diff_stat)
    box_only = []       # (abs_path, entry, old_rel, tokens_before, diff_stat)
    import_map = {}     # old_module → new_module

    for rel in changed:
        p = Path(rel)
        if p.suffix != '.py' or is_excluded(p):
            continue
        # Root-level debug scripts — skip
        if '/' not in rel and '\\' not in rel and _ROOT_DEBUG.match(p.name):
            continue
        abs_p = root / rel
        if not abs_p.exists():
            continue

        parsed = parse_pigeon_stem(p.stem)
        if not parsed:
            continue

        desc = extract_desc_slug(abs_p) or parsed['desc']
        try:
            file_text = abs_p.read_text(encoding='utf-8')
        except Exception:
            file_text = ''
        tokens = _estimate_tokens(file_text)
        tokens_before = tokens  # snapshot before mutation
        diff_stat = _file_diff_stat(rel)

        entry = registry.get(rel)
        if entry:
            entry = bump_version(entry, new_desc=desc, new_intent=intent)
            entry['tokens'] = tokens
            entry['history'][-1]['tokens'] = tokens
        else:
            today = datetime.now(timezone.utc).strftime('%m%d')
            entry = {
                'path': rel, 'name': parsed['name'],
                'seq': parsed['seq'], 'ver': parsed['ver'] + 1,
                'date': today, 'desc': desc, 'intent': intent,
                'tokens': tokens,
                'history': [{'ver': parsed['ver'] + 1, 'date': today,
                             'desc': desc, 'intent': intent,
                             'tokens': tokens,
                             'action': 'registered'}],
            }

        new_name = build_pigeon_filename(
            parsed['name'], parsed['seq'], entry['ver'],
            entry['date'], desc, intent,
        )
        folder = str(p.parent).replace('\\', '/')
        new_rel = f'{folder}/{new_name}' if folder != '.' else new_name
        entry['path'] = new_rel

        if rel in registry and rel != new_rel:
            del registry[rel]
        registry[new_rel] = entry

        if p.stem != Path(new_name).stem:
            renames.append((rel, new_rel, entry, tokens_before, diff_stat))
            old_mod = str(Path(rel).with_suffix('')).replace('\\', '.').replace('/', '.')
            new_mod = str(Path(new_rel).with_suffix('')).replace('\\', '.').replace('/', '.')
            import_map[old_mod] = new_mod
        else:
            box_only.append((abs_p, entry, rel, tokens_before, diff_stat))

    if not renames and not box_only:
        # No pigeon-managed files changed — but still run narrative + coaching
        # for non-pigeon code (client/, vscode-extension/, etc.)
        all_changed_code = [f for f in changed
                            if f.endswith(('.py', '.ts', '.js'))]
        if all_changed_code:
            print(f'\n🐦 Pigeon Git Plugin: 0 rename(s), 0 update(s), '
                  f'{len(all_changed_code)} non-pigeon file(s)')
            _run_post_commit_extras(root, intent, h, all_changed_code,
                                    registry, msg)
        return

    print(f'\n🐦 Pigeon Git Plugin: {len(renames)} rename(s), '
          f'{len(box_only)} update(s)')

    # Rewrite imports BEFORE renaming files (safe order — old files still exist)
    if import_map:
        changes = rewrite_all_imports(root, import_map)
        if changes:
            files_hit = len({c['file'] for c in changes})
            print(f'  ↳ {len(changes)} import(s) rewritten in {files_hit} file(s)')

    # Execute renames (after imports are updated)
    for old_rel, new_rel, entry, _, _ in renames:
        old_abs, new_abs = root / old_rel, root / new_rel
        if old_abs.exists():
            new_abs.parent.mkdir(parents=True, exist_ok=True)
            old_abs.rename(new_abs)
            print(f'  📝 {Path(old_rel).name}')
            print(f'     → {Path(new_rel).name}')

    # Log sessions + inject prompt boxes
    for old_rel, new_rel, entry, tb, ds in renames:
        log_session(root, new_rel, entry, h, msg, ds, old_path=old_rel, tokens_before=tb)
        new_abs = root / new_rel
        if new_abs.exists():
            _inject_box(new_abs, entry, h, root)
    for abs_p, entry, old_rel, tb, ds in box_only:
        log_session(root, old_rel, entry, h, msg, ds, tokens_before=tb)
        _inject_box(abs_p, entry, h, root)

    # Save registry
    save_registry(root, registry)

    # Refresh copilot-instructions.md auto-index + operator state
    processed = len(renames) + len(box_only)
    try:
        if _refresh_copilot_instructions(root, registry, processed):
            print(f'  📋 copilot-instructions.md auto-index updated ({processed} file(s) touched)')
    except Exception as e:
        print(f'  ⚠️  copilot-instructions refresh: {e}')

    # ── Self-fix: one-shot cross-file problem scan ──
    changed_py = [nr for _, nr, _, _, _ in renames] + [r for _, _, r, _, _ in box_only]
    cross_context = {}
    try:
        fix_mod = _load_glob_module(root, 'src', 'self_fix_seq013*')
        if fix_mod:
            fix_report = fix_mod.run_self_fix(
                root, registry, changed_py=changed_py, intent=intent)
            cross_context = fix_report.get('cross_context', {})
            fix_path = fix_mod.write_self_fix_report(root, fix_report, h)
            n_probs = len(fix_report.get('problems', []))
            print(f'  🔧 self-fix → {fix_path.relative_to(root)} ({n_probs} problems)')
    except Exception as e:
        print(f'  ⚠️  self-fix: {e}')

    # ── Pulse harvest: failsafe for any un-cleared pulse blocks ──
    try:
        pulse_mod = _load_glob_module(root, 'src', 'pulse_harvest_seq015*')
        if pulse_mod:
            recs = pulse_mod.harvest_all_pulses(root)
            if recs:
                print(f'  📡 pulse harvest → {len(recs)} edit(s) paired to prompts')
            # Also inject pulse blocks into any new files
            n_injected = pulse_mod.inject_all_pulses(root)
            if n_injected:
                print(f'  📡 pulse inject → {n_injected} new pulse block(s)')
    except Exception as e:
        print(f'  ⚠️  pulse harvest: {e}')

    # ── Push narrative + coaching + operator state ──
    all_changed_code = changed_py + [f for f in changed
                                      if f.endswith(('.py', '.ts', '.js'))
                                      and f not in changed_py]
    _run_post_commit_extras(root, intent, h, all_changed_code, registry, msg,
                            renames=renames, box_only=box_only,
                            cross_context=cross_context)

    # Rebuild manifests
    try:
        build_all_manifests(root)
    except Exception as e:
        print(f'  ⚠️  Manifest rebuild: {e}')

    # Compute total token footprint for this commit
    total_tokens = sum(
        e.get('tokens', 0) for _, _, e, _, _ in renames
    ) + sum(
        _estimate_tokens(fp.read_text(encoding='utf-8'))
        for fp, _, _, _, _ in box_only if fp.exists()
    )

    # Validate imports before committing — catch broken state early
    if renames:
        val = validate_imports(root)
        if not val['valid']:
            broken = val['broken']
            print(f'  ⚠️  {len(broken)} broken import(s) detected after rename:')
            for b in broken[:10]:
                print(f"      {b['file']}:{b['line']}  {b['import']}")
            # Attempt a second rewrite pass with broader matching
            extra = rewrite_all_imports(root, import_map)
            if extra:
                print(f'  🔧 Second pass fixed {len(extra)} import(s)')

    # Auto-commit
    _git('add', '-A')
    if _git('status', '--porcelain').strip():
        n = len(renames)
        _git('commit', '-m',
             f'chore(pigeon): auto-rename {n} file(s) [pigeon-auto]\n\n'
             f'Intent: {intent}\n'
             f'Tokens: ~{total_tokens:,}\n'
             f'Triggered by: {msg.splitlines()[0]}')
        print(f'  ✅ Auto-committed [pigeon-auto] (~{total_tokens:,} tokens)\n')
    else:
        print(f'  ℹ️  No changes to auto-commit\n')


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        # Post-commit — never break the workflow
        print(f'  ⚠️  Pigeon plugin error: {e}')
