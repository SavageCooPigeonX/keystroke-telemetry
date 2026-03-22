"""prompt_enricher_seq024_v001.py — Pre-process every prompt via DeepSeek.

Assembles full operator context (file heat, rework history, past attempts,
deleted words, cognitive state) and calls DeepSeek to interpret what the
operator actually means. Writes a <!-- pigeon:current-query --> block into
copilot-instructions.md so Copilot reads the enriched context on the next turn.

Zero friction: called automatically from prompt_journal on every log_enriched_entry.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v001 | ~180 lines | ~1,800 tokens
# DESC:   deepseek_prompt_enricher_query_context
# INTENT: enrich_every_prompt
# LAST:   2026-03-22
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-22T20:20:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  canonicalize current-query block cleanup
# EDIT_STATE: harvested
# ── /pulse ──
from __future__ import annotations
import json
import re
import os
from pathlib import Path
from datetime import datetime, timezone

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

OUTPUT FORMAT — produce exactly this structure, no markdown fences, no extra text:
COPILOT_QUERY: <The full rephrased query Copilot should execute. Be specific: name exact files, exact functions, exact variables. Use developer English. Make it unambiguous. 2-4 sentences max.>
INTERPRETED INTENT: <1 sentence — what operator actually wants beneath the raw words>
KEY FILES: <comma-separated exact filenames>
PRIOR ATTEMPTS: <1 sentence — what was tried and why it wasn't enough, or "none">
WATCH OUT FOR: <1 sentence — the specific pitfall most likely to trip Copilot given the rework history>
OPERATOR SIGNAL: <1 sentence — what deleted words + hesitation + trajectory reveal about the real frustration>
"""


def enrich_prompt(root: Path, raw_query: str,
                  deleted_words: list | None = None,
                  cognitive_state: dict | None = None) -> str:
    """Call DeepSeek to enrich a raw prompt. Returns the enriched interpretation text."""
    root = Path(root)

    context = {
        'hot_files':          _hot_files(root),
        'rework_history':     _rework_for_query(root, raw_query),
        'past_attempts':      _recent_ai_attempts(root, raw_query),
        'deleted_words':      deleted_words or _deleted_words_from_journal(root),
        'cognitive_state':    cognitive_state or _cognitive_state(root),
        'registry_hits':      _registry_touches(root, raw_query),
        'journal_trajectory': _recent_journal_context(root),
    }

    ds_prompt = _build_deepseek_prompt(raw_query, context)

    try:
        import glob as _g, importlib.util as _ilu
        matches = sorted(Path(root).glob(
            'pigeon_compiler/integrations/deepseek_adapter_seq001*.py'))
        if not matches:
            return ''
        spec = _ilu.spec_from_file_location('_ds', matches[-1])
        if spec is None or spec.loader is None:
            return ''
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Load .env so API key is available
        env_path = root / '.env'
        if env_path.exists():
            for line in env_path.read_text('utf-8').splitlines():
                if '=' in line and not line.startswith('#'):
                    k, _, v = line.partition('=')
                    os.environ.setdefault(k.strip(), v.strip())

        result = mod.deepseek_query(
            ds_prompt,
            system="You are a concise developer context interpreter. Output only the structured block, no prose.",
            max_tokens=300,
            temperature=0.2,
        )
        return result.get('content', '').strip()
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
    """Insert before the first managed block that still exists in the file."""
    markers = (
        '<!-- pigeon:task-context -->',
        '<!-- pigeon:task-queue -->',
        '<!-- pigeon:operator-state -->',
        '<!-- pigeon:prompt-telemetry -->',
        '<!-- pigeon:auto-index -->',
    )
    hits = [text.find(marker) for marker in markers if text.find(marker) >= 0]
    return min(hits) if hits else -1


# ── block injection ───────────────────────────

def inject_query_block(root: Path, raw_query: str,
                       deleted_words: list | None = None,
                       cognitive_state: dict | None = None) -> bool:
    """Enrich the prompt and write the <!-- pigeon:current-query --> block."""
    root = Path(root)
    cp = root / COPILOT_PATH
    if not cp.exists():
        return False

    enriched = enrich_prompt(root, raw_query, deleted_words, cognitive_state)
    if not enriched:
        return False

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    # Extract COPILOT_QUERY line from enriched output to place it prominently
    copilot_query_line = ''
    rest_lines = []
    for line in enriched.splitlines():
        if line.startswith('COPILOT_QUERY:'):
            copilot_query_line = line
        else:
            rest_lines.append(line)
    rest = '\n'.join(rest_lines).strip()

    block = (
        f'{BLOCK_START}\n'
        f'## What You Actually Mean Right Now\n\n'
        f'*Enriched {now} · raw: "{raw_query[:80]}"*\n\n'
        + (f'**{copilot_query_line}**\n\n' if copilot_query_line else '')
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
