"""prompt_enricher_seq024_v001.py — Pre-process every prompt via Gemini Flash.

Assembles full operator context (file heat, rework history, past attempts,
deleted words, cognitive state) and calls Gemini 2.5 Flash to interpret what the
operator actually means. Writes a <!-- pigeon:current-query --> block into
copilot-instructions.md so Copilot reads the enriched context on the next turn.

Zero friction: called automatically from prompt_journal on every log_enriched_entry.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v004 | 530 lines | ~5,128 tokens
# DESC:   pre_process_every_prompt_via
# INTENT: p0_p3_attribution
# LAST:   2026-04-03 @ d7cbc14
# SESSIONS: 3
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-03T19:00:00Z
# EDIT_HASH: auto
# EDIT_WHY:  dossier scoring router
# EDIT_STATE: harvested
# ── /pulse ──
from __future__ import annotations
import json
import re
import os
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from src._resolve import src_import

GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_TIMEOUT = 12  # seconds — enricher prompt is bigger than unsaid recon

BLOCK_START = '<!-- pigeon:current-query -->'
BLOCK_END   = '<!-- /pigeon:current-query -->'
COPILOT_PATH = '.github/copilot-instructions.md'

MAX_REWORK_ENTRIES  = 5
MAX_AI_RESPONSES    = 4
MAX_JOURNAL_ENTRIES = 4
MAX_DELETED_WORDS   = 8


# ── data loaders ──────────────────────────────

def _jload(path: Path):
    if not path.exists(): return None
    try: return json.loads(path.read_text('utf-8', errors='ignore'))
    except Exception: return None

def _jsonl(path: Path, n: int = 0) -> list:
    if not path.exists(): return []
    lines = path.read_text('utf-8', errors='ignore').strip().splitlines()
    if n: lines = lines[-n:]
    out = []
    for l in lines:
        try: out.append(json.loads(l))
        except Exception: pass
    return out


def _hot_files(root: Path, top_n: int = 5) -> list[dict]:
    """Return top N files by hesitation score from file_heat_map."""
    raw = _jload(root / 'file_heat_map.json')
    if not raw or not isinstance(raw, dict): return []
    items = []
    for name, v in raw.items():
        if not isinstance(v, dict): continue
        hes = v.get('avg_hes', 0)
        touches = v.get('total', 0)
        if touches >= 2:
            items.append({'file': name, 'hes': round(hes, 3), 'touches': touches})
    return sorted(items, key=lambda x: x['hes'], reverse=True)[:top_n]


def _registry_touches(root: Path, query: str) -> list[dict]:
    """Find registry entries for modules mentioned in the query."""
    reg = _jload(root / 'pigeon_registry.json')
    if not reg: return []
    files = reg if isinstance(reg, list) else reg.get('files', [])
    query_lower = query.lower()
    hits = []
    for f in files:
        name = f.get('file', '') or f.get('desc', '')
        seq = f.get('seq', '')
        if any(part in query_lower for part in name.lower().split('_') if len(part) > 3):
            hits.append({
                'file': name,
                'ver': f.get('ver', '?'),
                'desc': f.get('desc', ''),
                'intent': f.get('intent', ''),
            })
    return hits[:4]


def _score_bug_dossiers(root: Path, query: str, open_files: list | None = None) -> list[dict]:
    """Multi-signal scorer: query text + editor files + hot modules + rework overlap."""
    reg = _jload(root / 'pigeon_registry.json')
    if not reg: return []
    files = reg if isinstance(reg, list) else reg.get('files', [])
    query_lower = query.lower()
    query_words = set(re.findall(r'\b\w{3,}\b', query_lower))
    bug_signals = {'bug', 'fix', 'broke', 'broken', 'error', 'fail', 'crash',
                   'import', 'stale', 'wrong', 'missing', 'dead', 'overcap',
                   'split', 'cap', 'rename', 'fallout', 'demon', 'hurt'}
    is_bug_prompt = bool(query_words & bug_signals)
    # Signal 2: open editor files
    open_stems = set()
    for f in (open_files or []):
        open_stems.add(Path(f).stem.split('_seq')[0].split('_s0')[0].split('_s1')[0])
    # Signal 3: hot modules
    hot_names = set()
    hot_data = _hot_files(root, top_n=8)
    for h in hot_data:
        hot_names.add(h['file'].split('_seq')[0].split('_s0')[0].split('_s1')[0])
    scored = []
    for f in files:
        bugs = f.get('bug_keys') or []
        if not bugs: continue
        name = f.get('file', '') or f.get('desc', '')
        name_lower = name.lower()
        name_parts = set(name_lower.split('_'))
        name_stem = name_lower.split('_seq')[0].split('_s0')[0].split('_s1')[0]
        score = 0.0
        # Signal 1: query word overlap with module name
        name_overlap = sum(1 for p in name_parts if len(p) > 3 and p in query_lower)
        score += name_overlap * 0.3
        if is_bug_prompt: score += 0.15
        # Signal 2: file is open in editor
        if name_stem in open_stems: score += 0.35
        # Signal 3: file is cognitively hot
        if name_stem in hot_names: score += 0.2
        # Signal 4: bug recurrence (persistent demons score higher)
        counts = f.get('bug_counts', {})
        recur = sum(counts.values()) if counts else 0
        if recur >= 3: score += 0.15
        elif recur >= 2: score += 0.1
        # Signal 5: rework feedback from registry
        dossier_score = f.get('dossier_score', 0)
        score += dossier_score * 0.2
        if score > 0:
            scored.append({
                'file': name, 'bugs': bugs, 'score': round(score, 3),
                'entity': f.get('bug_entity', ''), 'recur': recur,
                'counts': counts, 'last_mark': f.get('last_bug_mark', ''),
                'last_change': f.get('last_change', ''),
            })
    scored.sort(key=lambda x: -x['score'])
    return scored


def _write_routing_signal(root: Path, dossiers: list[dict]):
    """Write active dossier selection so task-context + auto-index can slim."""
    signal = {'ts': datetime.now(timezone.utc).isoformat(), 'dossiers': [], 'confidence': 0.0}
    if dossiers:
        top = dossiers[0]
        signal['confidence'] = top['score']
        signal['focus_modules'] = [d['file'] for d in dossiers[:5]]
        signal['focus_bugs'] = list(set(b for d in dossiers[:5] for b in d['bugs']))
        signal['dossiers'] = dossiers[:5]
    try:
        (root / 'logs' / 'active_dossier.json').write_text(
            json.dumps(signal, indent=2, default=str), 'utf-8')
    except Exception:
        pass


def _active_bug_dossier(root: Path, query: str, open_files: list | None = None) -> str:
    """Score, route, and format bug dossiers for the enricher prompt."""
    scored = _score_bug_dossiers(root, query, open_files)
    _write_routing_signal(root, scored)
    if not scored: return ''
    entries = []
    for d in scored[:6]:
        bug_str = ','.join(d['bugs'])
        line = f"  • {d['file']} [{bug_str}] score={d['score']} recur={d['recur']}"
        if d['entity']: line += f" demon=\"{d['entity']}\""
        if d['last_mark']: line += f" last_mark={d['last_mark']}"
        if d['last_change']: line += f" last_change=\"{d['last_change']}\""
        entries.append(line)
    return 'ACTIVE BUG DOSSIER (scored by: query+editor+hot_modules+recurrence):\n' + '\n'.join(entries)


def _rework_for_query(root: Path, query: str) -> list[dict]:
    """Find rework log entries related to the current query topic."""
    entries = _jsonl(root / 'rework_log.json', n=50)
    query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
    scored = []
    for e in entries:
        hint = (e.get('query_hint') or '').lower()
        overlap = len(query_words & set(re.findall(r'\b\w{4,}\b', hint)))
        if overlap >= 1:
            scored.append((overlap, e))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:MAX_REWORK_ENTRIES]]


def _recent_ai_attempts(root: Path, query: str) -> list[dict]:
    """Find the most recent AI responses relevant to this query topic."""
    entries = _jsonl(root / 'logs' / 'ai_responses.jsonl', n=30)
    query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
    scored = []
    for e in entries:
        prompt = (e.get('prompt') or '').lower()
        overlap = len(query_words & set(re.findall(r'\b\w{4,}\b', prompt)))
        if overlap >= 2:
            scored.append((overlap, e))
    scored.sort(key=lambda x: -x[0])
    hits = []
    for _, e in scored[:MAX_AI_RESPONSES]:
        hits.append({
            'prompt_preview': (e.get('prompt') or '')[:80],
            'response_preview': (e.get('response') or '')[:120],
            'ts': e.get('ts', ''),
        })
    return hits


def _deleted_words_from_journal(root: Path, n: int = 3) -> list[str]:
    """Pull deleted words from the last N journal entries."""
    entries = _jsonl(root / 'logs' / 'prompt_journal.jsonl', n=n)
    words = []
    for e in entries:
        for w in (e.get('deleted_words') or []):
            word = w.get('word', w) if isinstance(w, dict) else str(w)
            if word and len(word) > 2:
                words.append(word)
    return words[-MAX_DELETED_WORDS:]


def _cognitive_state(root: Path) -> dict:
    snap = _jload(root / 'logs' / 'prompt_telemetry_latest.json')
    if not snap: return {}
    signals = snap.get('signals', {})
    summary = snap.get('running_summary', {})
    return {
        'state': summary.get('dominant_state', 'unknown'),
        'wpm': signals.get('wpm', 0),
        'del_ratio': signals.get('deletion_ratio', 0),
        'hes': signals.get('hesitation_count', 0),
    }


def _recent_journal_context(root: Path, n: int = 6) -> list[dict]:
    """Pull last N journal entries as prompt trajectory — what operator was building toward."""
    entries = _jsonl(root / 'logs' / 'prompt_journal.jsonl', n=n)
    out = []
    for e in entries:
        deleted = [
            w.get('word', w) if isinstance(w, dict) else str(w)
            for w in (e.get('deleted_words') or [])
        ]
        rewrites = [
            f"{r.get('old','')} → {r.get('new','')}" if isinstance(r, dict) else str(r)
            for r in (e.get('rewrites') or [])
        ]
        out.append({
            'msg': (e.get('msg') or '')[:120],
            'intent': e.get('intent', 'unknown'),
            'state': e.get('state', 'unknown'),
            'deleted': deleted,
            'rewrites': rewrites,
        })
    return out


# ── DeepSeek enrichment ───────────────────────

def _build_deepseek_prompt(raw_query: str, context: dict) -> str:
    hot = context.get('hot_files', [])
    rework = context.get('rework_history', [])
    past = context.get('past_attempts', [])
    deleted = context.get('deleted_words', [])
    state = context.get('cognitive_state', {})
    registry = context.get('registry_hits', [])
    journal = context.get('journal_trajectory', [])
    shard_context = context.get('shard_context', '')
    bug_dossier = context.get('bug_dossier', '')

    hot_str = '\n'.join(
        f"  • {h['file']} (hes={h['hes']}, touched {h['touches']}x)" for h in hot
    ) or '  (none)'

    rework_str = '\n'.join(
        f"  • [{e.get('verdict','?')}] \"{e.get('query_hint','')[:80]}\"" for e in rework
    ) or '  (no rework history for this topic)'

    past_str = '\n'.join(
        f"  • Prompt: \"{h['prompt_preview']}\"\n    Copilot: \"{h['response_preview']}\"" for h in past
    ) or '  (no past attempts found)'

    deleted_str = ', '.join(f'"{w}"' for w in deleted) or 'none'

    reg_str = '\n'.join(
        f"  • {r['file']} v{r['ver']} — {r['desc']} (intent: {r['intent']})" for r in registry
    ) or '  (no registry matches)'

    journal_str = '\n'.join(
        f"  [{i+1}] \"{e['msg']}\" (intent={e['intent']}, state={e['state']}"
        + (f", deleted: {', '.join(e['deleted'])}" if e['deleted'] else '')
        + (f", rewrote: {', '.join(e['rewrites'][:2])}" if e['rewrites'] else '')
        + ')'
        for i, e in enumerate(journal)
    ) or '  (no journal history)'

    return f"""You are the Pigeon Prompt Steerer. You DO NOT summarize. You rewrite.

Your job: given a raw developer prompt and full codebase context, produce the BEST POSSIBLE prompt Copilot should act on. The operator's raw words are a starting point — you have more context than they wrote. Use it.

RAW PROMPT: "{raw_query}"

PROMPT TRAJECTORY (last 6 prompts — what they've been building toward):
{journal_str}

OPERATOR STATE:
  Cognitive state: {state.get('state', 'unknown')}
  WPM: {state.get('wpm', 0)} | Deletion ratio: {state.get('del_ratio', 0):.1%} | Hesitation count: {state.get('hes', 0)}
  Words deleted before submitting: {deleted_str}

HIGH-PAIN FILES (operator cognitively struggles with these — be extra precise):
{hot_str}

REGISTRY HITS (files this query most likely touches):
{reg_str}

REWORK HISTORY (what failed before on similar queries):
{rework_str}

PAST COPILOT ATTEMPTS:
{past_str}

{bug_dossier}
{shard_context}
OUTPUT FORMAT — produce exactly this structure, no markdown fences, no extra text:
COPILOT_QUERY: <The full rephrased query Copilot should execute. Be specific: name exact files, exact functions, exact variables. Use developer English. Make it unambiguous. 2-4 sentences max.>
INTERPRETED INTENT: <1 sentence — what operator actually wants beneath the raw words>
KEY FILES: <comma-separated exact filenames>
PRIOR ATTEMPTS: <1 sentence — what was tried and why it wasn't enough, or "none">
WATCH OUT FOR: <1 sentence — the specific pitfall most likely to trip Copilot given the rework history>
OPERATOR SIGNAL: <1 sentence — what deleted words + hesitation + trajectory reveal about the real frustration>
UNSAID_RECONSTRUCTION: <If deleted words exist: reconstruct the full sentence the operator STARTED typing before they changed their mind. Combine submitted text + deleted fragments into what they originally intended. If no deleted words: "none">
"""


def enrich_prompt(root: Path, raw_query: str,
                  deleted_words: list | None = None,
                  cognitive_state: dict | None = None,
                  open_files: list | None = None) -> str:
    """Call DeepSeek to enrich a raw prompt. Returns the enriched interpretation text."""
    root = Path(root)

    # Route memory shards
    shard_text = ''
    try:
        route_context, format_shard_context = src_import("context_router_seq027", "route_context", "format_shard_context")
        routed = route_context(root, raw_query)
        shard_text = format_shard_context(routed, root=root)
    except Exception:
        pass

    context = {
        'hot_files':          _hot_files(root),
        'rework_history':     _rework_for_query(root, raw_query),
        'past_attempts':      _recent_ai_attempts(root, raw_query),
        'deleted_words':      deleted_words or _deleted_words_from_journal(root),
        'cognitive_state':    cognitive_state or _cognitive_state(root),
        'registry_hits':      _registry_touches(root, raw_query),
        'journal_trajectory': _recent_journal_context(root),
        'shard_context':      shard_text,
        'bug_dossier':        _active_bug_dossier(root, raw_query, open_files),
    }

    ds_prompt = _build_deepseek_prompt(raw_query, context)

    # Load API key from .env
    api_key = None
    env_path = root / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8').splitlines():
            if line.startswith('GEMINI_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    if not api_key:
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return ''

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text':
            'You are a concise developer context interpreter. Output only the structured block, no prose.'}]},
        'contents': [{'parts': [{'text': ds_prompt}]}],
        'generationConfig': {
            'temperature': 0.2,
            'maxOutputTokens': 2048,
            'thinkingConfig': {'thinkingBudget': 256},
        },
    }).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        return f'(enrichment unavailable: {e})'


def _strip_query_blocks(text: str) -> tuple[str, bool]:
    """Remove all managed current-query blocks, even if duplicates exist."""
    lines = text.splitlines()
    kept = []
    in_block = False
    removed = False

    for line in lines:
        stripped = line.strip()
        if stripped == BLOCK_START:
            in_block = True
            removed = True
            continue
        if in_block:
            if stripped == BLOCK_END:
                in_block = False
            continue
        kept.append(line)

    cleaned = '\n'.join(kept).rstrip()
    legacy_pat = re.compile(
        r'(?ms)^## What You Actually Mean Right Now\s*\n.*?^\s*'
        + re.escape(BLOCK_END)
        + r'\s*$\n?'
    )
    cleaned, legacy_n = legacy_pat.subn('', cleaned)
    removed = removed or legacy_n > 0
    if text.endswith('\n'):
        cleaned += '\n'
    return cleaned, removed


def _find_insert_anchor(text: str) -> int:
    """Insert before the first real managed block line, not inline examples."""
    markers = (
        '<!-- pigeon:task-context -->',
        '<!-- pigeon:task-queue -->',
        '<!-- pigeon:operator-state -->',
        '<!-- pigeon:prompt-telemetry -->',
        '<!-- pigeon:auto-index -->',
    )
    hits = []
    for marker in markers:
        m = re.search(rf'(?m)^\s*{re.escape(marker)}\s*$', text)
        if m:
            hits.append(m.start())
    return min(hits) if hits else -1


# ── block injection ───────────────────────────

def inject_query_block(root: Path, raw_query: str,
                       deleted_words: list | None = None,
                       cognitive_state: dict | None = None,
                       open_files: list | None = None) -> bool:
    """Enrich the prompt and write the <!-- pigeon:current-query --> block."""
    root = Path(root)
    cp = root / COPILOT_PATH
    if not cp.exists():
        return False

    enriched = enrich_prompt(root, raw_query, deleted_words, cognitive_state, open_files)
    if not enriched:
        return False

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # Extract COPILOT_QUERY line from enriched output to place it prominently
    copilot_query_line = ''
    unsaid_recon_line = ''
    rest_lines = []
    for line in enriched.splitlines():
        if line.startswith('COPILOT_QUERY:'):
            copilot_query_line = line
        elif line.startswith('UNSAID_RECONSTRUCTION:'):
            unsaid_recon_line = line.split(':', 1)[1].strip()
        else:
            rest_lines.append(line)
    rest = '\n'.join(rest_lines).strip()

    block = (
        f'{BLOCK_START}\n'
        f'## What You Actually Mean Right Now\n\n'
        f'*Enriched {now} · raw: "{raw_query[:80]}"*\n\n'
        + (f'**{copilot_query_line}**\n\n' if copilot_query_line else '')
        + (f'UNSAID_RECONSTRUCTION: {unsaid_recon_line}\n\n'
           if unsaid_recon_line and unsaid_recon_line.lower() != 'none'
           else '')
        + f'{rest}\n'
        f'{BLOCK_END}'
    )

    text = cp.read_text('utf-8')
    text, had_block = _strip_query_blocks(text)
    if had_block:
        idx = _find_insert_anchor(text)
        if idx >= 0:
            text = text[:idx] + block + '\n\n' + text[idx:]
        else:
            text = text.rstrip() + '\n\n' + block + '\n'
    else:
        idx = _find_insert_anchor(text)
        if idx >= 0:
            text = text[:idx] + block + '\n\n' + text[idx:]
        else:
            text = text.rstrip() + '\n\n---\n\n' + block + '\n'

    cp.write_text(text, 'utf-8')
    return True


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'fix the wpm thing'
    print(f'Enriching: "{query}"')
    ok = inject_query_block(root, query)
    print(f'Injected: {ok}')
