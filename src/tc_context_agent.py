"""Context-select agent — picks relevant source files based on typing intent.

Reads the buffer + live signals to select relevant source files, then loads
compressed snippets so Gemini can see actual code — not just metadata.
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

from .tc_constants import ROOT

_registry_cache: list[dict] = []
_registry_ts: float = 0


def _load_registry() -> list[dict]:
    """Load pigeon_registry.json with caching."""
    global _registry_cache, _registry_ts
    now = time.time()
    if _registry_cache and (now - _registry_ts) < 300:
        return _registry_cache
    reg = ROOT / 'pigeon_registry.json'
    if not reg.exists():
        return []
    try:
        data = json.loads(reg.read_text('utf-8', errors='ignore'))
        _registry_cache = data.get('files', [])
        _registry_ts = now
    except Exception:
        pass
    return _registry_cache


_STOPWORDS = frozenset(
    # common english
    'this that with from have what when where then than they their '
    'will would could should about been into some also just like '
    'more need want make does dont here were each which '
    'still really pretty super actually kinda right think '
    'look looking know know going gonna doing done getting '
    'much very even only most many such well back over '
    'being said says yeah okay sure thing things '
    'being good better best worst kind sort type types way ways '
    'because before after while until since '
    # dev/meta words that match everything
    'file files code module modules function functions class method '
    'build builds building built '
    'proper properly work works working '
    'text data output input system state states status '
    'check checking test testing debug debugging '
    'read write load save update create delete run running '
    'slow fast poll polling quick '
    'error errors issue issues problem problems fix fixes '
    'import imports export exports path paths name names '
    'help helps model models query queries '
    'config configure current active recent last first next'.split()
)

# Words that ARE meaningful in this codebase despite looking generic.
# These override _STOPWORDS — the sim engine proved "thought" and "context"
# were getting filtered, causing the context agent to fall back to static files.
_CODEBASE_TERMS = frozenset(
    'thought completer completion context select selection agent '
    'profile prompt entropy drift reactor pulse harvest '
    'pigeon compiler rename registry manifest '
    'buffer keyboard keystroke typing pause popup '
    'narrative organism consciousness shard memory '
    'natural naturally complete completing thoughts '
    'sim simulation replay transcript'.split()
)


def _extract_mentions(buffer: str) -> list[str]:
    """Extract module/file names mentioned in the buffer text.
    
    Strongly prefers underscore_names (likely module refs) over single words.
    """
    mentions = []
    seen = set()
    # Multi-word underscore names first (highest signal — likely module refs)
    underscored = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+(?:_[a-zA-Z0-9_]+)+', buffer.lower())
    for u in underscored:
        if u not in seen:
            mentions.append(u)
            seen.add(u)
    # Then single words, heavily filtered
    words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', buffer.lower())
    for w in words:
        if len(w) > 4 and (w in _CODEBASE_TERMS or w not in _STOPWORDS) and w not in seen:
            mentions.append(w)
            seen.add(w)
    return mentions


def _name_segment_match(mention: str, module_name: str) -> bool:
    """Check if mention matches a meaningful segment of the module name.

    'completer' matches 'thought_completer' (segment boundary).
    'select' should NOT match 'context_selector' via substring.
    Requires: exact match, or bounded by _ or start/end of name.
    """
    if mention == module_name:
        return True
    parts = module_name.split('_')
    # Match any single segment
    if mention in parts:
        return True
    # Match contiguous segments (e.g. 'context_agent' in 'tc_context_agent')
    if '_' in mention:
        return mention in module_name
    return False


def _score_module(mod: dict, mentions: list[tuple[str, float]],
                  hot_mods: list[str], heat_mods: list[str],
                  state: str = 'unknown') -> float:
    """Score a module's relevance to the current buffer.

    mentions: list of (word, weight) tuples. Buffer words get weight=1.0,
    context padding words get weight=0.3 to avoid drowning the signal.
    """
    name = mod.get('name', '').lower()
    desc = mod.get('desc', '').lower()
    score = 0.0
    for m, w in mentions:
        if _name_segment_match(m, name):
            score += 3.0 * w
        elif '_' in m and m in desc:
            score += 1.0 * w
        elif m in desc:
            score += 0.3 * w
    if name in hot_mods:
        score += 0.5
    if name in heat_mods:
        score += 0.3
        if state in ('frustrated', 'hesitant'):
            score += 0.3
    if mod.get('bug_keys'):
        if any(m in str(mod.get('bug_keys', '')) for m, _ in mentions):
            score += 0.5
    return score


def select_context_files(buffer: str, ctx: dict, max_files: int = 3) -> list[dict]:
    """Select the most relevant source files based on buffer intent.

    Uses: buffer text, unsaid threads, recent prompts, hot modules, heat map,
    and operator cognitive state to build a composite intent signal.
    """
    registry = _load_registry()
    if not registry:
        return []
    # Buffer mentions get full weight — this is the PRIMARY signal.
    # Context padding (unsaid, recent prompts, session) gets reduced weight
    # to avoid drowning buffer-specific intent with recurring meta-words.
    buffer_mentions = _extract_mentions(buffer)
    weighted: list[tuple[str, float]] = [(m, 1.0) for m in buffer_mentions]
    # Context padding at 0.3 weight
    ctx_text = ''
    for thread in ctx.get('unsaid_threads', [])[-3:]:
        ctx_text += ' ' + thread
    for p in ctx.get('recent_prompts', [])[-2:]:
        ctx_text += ' ' + p.get('msg', '')
    for sm in ctx.get('session_messages', [])[-3:]:
        ctx_text += ' ' + sm.get('text', '')
    seen = set(buffer_mentions)
    for m in _extract_mentions(ctx_text):
        if m not in seen:
            weighted.append((m, 0.3))
            seen.add(m)
    hot_mods = [m.get('module', '').lower() for m in ctx.get('hot_modules', [])]
    heat_mods = [h.get('mod', '').lower() for h in ctx.get('heat_map', []) if h.get('heat', 0) > 0.1]
    op_state = ctx.get('operator_state', {}).get('dominant', 'unknown')

    scored = []
    for mod in registry:
        s = _score_module(mod, weighted, hot_mods, heat_mods, op_state)
        if s >= 1.5:  # minimum threshold — don't inject weak matches
            scored.append({
                'path': mod.get('path', ''),
                'name': mod.get('name', ''),
                'tokens': mod.get('tokens', 0),
                'score': s,
            })
    scored.sort(key=lambda x: x['score'], reverse=True)
    # Deduplicate by stem name — registry has multiple entries per module
    seen_names = set()
    deduped = []
    for s in scored:
        stem = s['name'].split('_seq')[0] if '_seq' in s['name'] else s['name']
        if stem not in seen_names:
            seen_names.add(stem)
            deduped.append(s)
    return deduped[:max_files]


def _load_file_snippet(filepath: str, max_lines: int = 40) -> str:
    """Load a compressed snippet from a source file."""
    stem = Path(filepath).stem
    candidates = [
        ROOT / filepath,
        ROOT / 'src' / filepath,
    ]
    if not filepath.endswith('.py'):
        candidates.append(ROOT / f'{filepath}.py')
        candidates.append(ROOT / 'src' / f'{filepath}.py')
    # try pigeon-named files in src/ and pigeon_compiler/ without expensive glob
    for d in [ROOT / 'src', ROOT / 'pigeon_compiler', ROOT / 'pigeon_brain']:
        if d.is_dir():
            for f in d.iterdir():
                if f.suffix == '.py' and stem in f.stem:
                    candidates.append(f)
                    break
    for p in candidates:
        if p.exists() and p.is_file():
            try:
                lines = p.read_text('utf-8', errors='ignore').splitlines()
                content = []
                skip = False
                for line in lines[:max_lines * 2]:
                    if '# ── telemetry:pulse' in line:
                        skip = True
                    elif '# ── /pulse' in line:
                        skip = False
                        continue
                    if not skip:
                        content.append(line)
                    if len(content) >= max_lines:
                        break
                return '\n'.join(content)
            except Exception:
                continue
    return ''


def build_code_context(buffer: str, ctx: dict) -> str:
    """Build the code context injection for the LLM prompt."""
    selected = select_context_files(buffer, ctx)
    if not selected:
        return ''
    parts = ['RELEVANT SOURCE FILES (selected by intent from your buffer):']
    for f in selected:
        snippet = _load_file_snippet(f['path'])
        if snippet:
            parts.append(f"── {f['name']} (score={f['score']:.1f}, {f['tokens']}tok) ──")
            parts.append(snippet[:1500])
    if len(parts) <= 1:
        return ''
    return '\n'.join(parts)
