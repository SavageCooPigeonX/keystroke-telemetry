"""Context-select agent — picks relevant source files based on typing intent.

Reads the buffer + live signals to select relevant source files, then loads
compressed snippets so Gemini can see actual code — not just metadata.

Section-aware: uses the operator's behavioral section (from tc_profile_seq001_v001) to
boost modules they historically touch when in the same cognitive mode.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 706 lines | ~6,731 tokens
# DESC:   picks_relevant_source_files_based
# INTENT: fix_close_outcome_sim
# LAST:   2026-04-20 @ 6ae8700
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import re
import time
from pathlib import Path

from .tc_constants_seq001_v001 import ROOT

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
        _registry_cache = _augment_registry_with_fallback(data.get('files', []))
        _registry_ts = now
    except Exception:
        pass
    return _registry_cache


def _registry_canonical_keys(mod: dict) -> set[str]:
    """Canonical keys for matching numeric predictions back to registry entries."""
    try:
        from .intent_numeric_seq001_v002_d0420__word_number_file_mapping_for_lc_fix_close_outcome_sim import canonicalize_file_key
    except Exception:
        return set()

    keys = set()
    for raw in (mod.get('name', ''), mod.get('path', '')):
        if raw:
            canonical = canonicalize_file_key(raw)
            if canonical:
                keys.add(canonical)
    return keys


def _fallback_registry_entries() -> list[dict]:
    """Scan the repo for Python files when pigeon_registry.json is sparse."""
    entries = []
    seen_paths = set()
    patterns = (
        '*.py',
        'client/**/*.py',
        'src/**/*.py',
        'pigeon_compiler/**/*.py',
        'pigeon_brain/**/*.py',
    )
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if not path.is_file() or path.name.startswith('.'):
                continue
            if path.name == '__init__.py':
                continue
            if 'tests' in path.parts or 'build' in path.parts:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in seen_paths:
                continue
            seen_paths.add(rel)
            try:
                text = path.read_text('utf-8', errors='ignore')
            except Exception:
                text = ''
            entries.append({
                'path': rel,
                'name': path.stem,
                'tokens': len(text.split()),
                'desc': rel.replace('/', ' '),
            })
    return entries


def _augment_registry_with_fallback(registry: list[dict]) -> list[dict]:
    """Merge filesystem-discovered Python files into a sparse pigeon registry."""
    merged = list(registry)
    seen_keys = set()
    for mod in merged:
        seen_keys |= _registry_canonical_keys(mod)

    for mod in _fallback_registry_entries():
        mod_keys = _registry_canonical_keys(mod)
        if mod_keys & seen_keys:
            continue
        merged.append(mod)
        seen_keys |= mod_keys

    return merged


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
    'drift_watcher' matches '偏p_dw_s005_drift_watcher...' (pigeon English tail).
    Requires: exact match, or bounded by _ or start/end of name.
    """
    if mention == module_name:
        return True
    parts = module_name.split('_')
    # Match any single segment
    if mention in parts:
        return True
    # Match contiguous segments (e.g. 'context_agent' in 'tc_context_seq001_v001_agent_seq001_v001')
    if '_' in mention:
        if mention in module_name:
            return True
        # Also try matching with underscores in different positions
        # 'self_fix' should match in '..._run_self_fix_seq012...'
        mention_parts = mention.split('_')
        if len(mention_parts) >= 2:
            # check if all mention parts appear consecutively in module parts
            for i in range(len(parts) - len(mention_parts) + 1):
                if parts[i:i+len(mention_parts)] == mention_parts:
                    return True
    return False


def _score_module(mod: dict, mentions: list[tuple[str, float]],
                  hot_mods: list[str], heat_mods: list[str],
                  state: str = 'unknown') -> float:
    """Score a module's relevance to the current buffer.

    mentions: list of (word, weight) tuples. Buffer words get weight=1.0,
    context padding words get weight=0.3 to avoid drowning the signal.

    Also extracts English segments from pigeon-encoded names so that
    'drift_watcher' matches '偏p_dw_s005..._glyph_drift_decomposed...'
    """
    name = mod.get('name', '').lower()
    desc = mod.get('desc', '').lower()
    # Extract pure English segments from pigeon name for matching
    # e.g. '修f_sf_s013..._run_self_fix_seq012' → ['run', 'self', 'fix']
    english_parts = [p for p in name.split('_') if p.isascii() and p.isalpha() and len(p) > 2]
    score = 0.0
    for m, w in mentions:
        if _name_segment_match(m, name):
            score += 3.0 * w
        elif m in english_parts:
            # mention word appears as an English segment in pigeon name
            score += 2.0 * w
        elif '_' in m:
            # multi-word mention: check if all sub-parts appear in english_parts
            m_parts = m.split('_')
            if len(m_parts) >= 2 and all(mp in english_parts for mp in m_parts):
                score += 2.5 * w
            elif m in desc:
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


def select_context_numeric(buffer: str, ctx: dict, max_files: int = 3) -> list[dict]:
    """Select context files using the numeric word→file surface.
    
    This is a pure numeric alternative to LLM-based selection. Uses learned
    correlations between prompt words and file touches from push cycles.
    """
    try:
        from .intent_numeric_seq001_v002_d0420__word_number_file_mapping_for_lc_fix_close_outcome_sim import predict_files, get_stats, canonicalize_file_key
        stats = get_stats()
        if stats['total_touches'] < 10:
            return []  # Not enough data yet, fall back to heuristics
        
        # Combine buffer with any unsaid threads
        combined = buffer
        for thread in ctx.get('unsaid_threads', [])[-2:]:
            combined += ' ' + thread
        
        predictions = predict_files(combined, top_n=max_files * 2)
        if not predictions:
            return []
        
        # Map predictions back to registry entries
        registry = _load_registry()
        results = []
        for module_name, score in predictions:
            # Post-purge, clean learned scores top out ~0.04. Keep anything
            # predict_files returned (it already applied its own > 0.001 cut
            # and top_n ranking). Filtering again at 0.01 dropped everything.
            if score < 0.001:
                continue
            target_key = canonicalize_file_key(module_name)
            # Find matching registry entry
            for mod in registry:
                if target_key in _registry_canonical_keys(mod):
                    results.append({
                        'path': mod.get('path', ''),
                        'name': mod.get('name', ''),
                        'tokens': mod.get('tokens', 0),
                        # Was score*10 → *50 → *225. Numeric max ~1.39 × 225 = 313
                        # vs heuristic max ~6.0. Numeric can now win ensemble.
                        'score': score * 225,
                        'source': 'numeric',
                    })
                    break
        
        # Dedupe by stem
        seen = set()
        deduped = []
        for r in results:
            stem = r['name'].split('_seq')[0] if '_seq' in r['name'] else r['name']
            if stem not in seen:
                seen.add(stem)
                deduped.append(r)
        
        return deduped[:max_files]
    except Exception:
        return []


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

    # ── SECTION-AWARE BOOST ──
    # Load the operator's behavioral section data. If they're in "debugging"
    # and historically touch git_plugin when debugging, boost git_plugin.
    section_hot = {}
    section_style = {}
    try:
        from .tc_profile_seq001_v001 import classify_section, load_profile
        section = classify_section(buffer, state=op_state)
        if section != 'unknown':
            profile = load_profile()
            sec_data = profile.get('shards', {}).get('sections', {}).get(section, {})
            section_hot = sec_data.get('hot_modules', {})
            section_style = sec_data
    except Exception:
        pass

    scored = []
    for mod in registry:
        s = _score_module(mod, weighted, hot_mods, heat_mods, op_state)
        # Section boost: if this module appears in the section's hot_modules,
        # the operator historically touches it when in this cognitive mode.
        mod_name = mod.get('name', '').lower()
        for sec_mod, sec_count in section_hot.items():
            if sec_mod in mod_name or mod_name in sec_mod:
                s += min(1.5, sec_count * 0.3)
                break
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


def select_context_ensemble(buffer: str, ctx: dict, max_files: int = 3) -> list[dict]:
    """Ensemble selection: merge numeric surface + heuristic scoring.
    
    The numeric surface has learned correlations; the heuristics have
    explicit rules. Together they're more robust than either alone.
    """
    # Get numeric predictions first (learned correlations)
    numeric = select_context_numeric(buffer, ctx, max_files=max_files * 2)
    
    # Get heuristic predictions (rule-based)
    heuristic = select_context_files(buffer, ctx, max_files=max_files * 2)
    
    # Merge by stem, summing scores
    merged: dict[str, dict] = {}
    for r in numeric:
        stem = r['name'].split('_seq')[0] if '_seq' in r['name'] else r['name']
        if stem not in merged:
            merged[stem] = r.copy()
            merged[stem]['sources'] = ['numeric']
        else:
            merged[stem]['score'] += r['score']
            merged[stem]['sources'].append('numeric')
    
    for r in heuristic:
        stem = r['name'].split('_seq')[0] if '_seq' in r['name'] else r['name']
        if stem not in merged:
            merged[stem] = r.copy()
            merged[stem]['sources'] = ['heuristic']
        else:
            merged[stem]['score'] += r['score']
            if 'heuristic' not in merged[stem].get('sources', []):
                merged[stem]['sources'].append('heuristic')
    
    # Sort by merged score
    results = sorted(merged.values(), key=lambda x: x['score'], reverse=True)
    return results[:max_files]


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


# ══════════════════════════════════════════════════════════════════════════════
# TC MANIFEST INTEGRATION — profile matching, grading, weight adjustment
# ══════════════════════════════════════════════════════════════════════════════

def get_intelligent_context(buffer: str, ctx: dict | None = None) -> dict:
    """Get full intelligent context combining profile match + file selection + bug trajectories.
    
    This is the main entry point for TC-steered context selection.
    Returns a dict ready for injection into LLM prompts.
    """
    ctx = ctx or {}
    result = {
        'profile_match': None,
        'profile_confidence': 0.0,
        'template': '/build',
        'files': [],
        'bugs': [],
        'trajectories': [],
        'weights': {},
    }
    
    # ── Match intent profile ──
    try:
        from .tc_manifest_seq001_v001 import match_intent_profile, get_tc_context_seq001_v001
        tc_ctx = get_tc_context_seq001_v001()
        
        name, profile, score = match_intent_profile(buffer)
        if name and score > 0.3:
            result['profile_match'] = name
            result['profile_confidence'] = score
            result['template'] = profile.get('template', '/build')
            # Use profile's suggested files as boost
            profile_files = profile.get('files', [])
        else:
            profile_files = []
        
        # Get bug trajectories for chronic bugs
        result['bugs'] = [b for b in tc_ctx.get('bugs', []) 
                         if b.get('status') == 'chronic'][:3]
        
        # Get file trajectories for unstable files
        result['trajectories'] = [t for t in tc_ctx.get('trajectories', {}).values()
                                  if t.get('stability') == 'unstable'][:3]
        
        result['weights'] = tc_ctx.get('weights', {})
        
    except Exception:
        profile_files = []
    
    # ── Select context files ──
    selected = select_context_files(buffer, ctx)
    result['files'] = selected
    
    return result


def log_prediction(buffer: str, predicted_files: list[str], 
                   predicted_intent: str) -> str | None:
    """Log a prediction for later grading. Returns prediction ID."""
    try:
        from .tc_manifest_seq001_v001 import match_intent_profile
        name, profile, score = match_intent_profile(buffer)
        
        # Store prediction for later grading
        pred_file = ROOT / 'logs' / 'tc_predictions.jsonl'
        pred_file.parent.mkdir(parents=True, exist_ok=True)
        
        from datetime import datetime, timezone
        pred = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'profile_match': name,
            'profile_confidence': score,
            'predicted_intent': predicted_intent,
            'predicted_files': predicted_files[:5],
            'graded': False,
        }
        with open(pred_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(pred, ensure_ascii=False) + '\n')
        return pred['ts']
    except Exception:
        return None


def grade_prediction(prediction_ts: str, actual_intent: str, 
                     actual_files: list[str]) -> float:
    """Grade a prediction and update TC_MANIFEST weights.
    
    Returns score 0-1. Updates manifest with learning.
    """
    pred_file = ROOT / 'logs' / 'tc_predictions.jsonl'
    if not pred_file.exists():
        return 0.0
    
    # Find the prediction
    predictions = []
    target_pred = None
    for line in pred_file.read_text('utf-8', errors='ignore').strip().splitlines():
        try:
            p = json.loads(line)
            if p.get('ts') == prediction_ts and not p.get('graded'):
                target_pred = p
            predictions.append(p)
        except Exception:
            continue
    
    if not target_pred:
        return 0.0
    
    # Calculate score
    intent_match = target_pred.get('predicted_intent', '') == actual_intent
    pred_files = set(target_pred.get('predicted_files', []))
    actual_set = set(actual_files)
    file_overlap = len(pred_files & actual_set) / len(pred_files) if pred_files else 0
    
    score = (0.6 if intent_match else 0) + (file_overlap * 0.4)
    
    # Update TC_MANIFEST prediction log
    try:
        from .tc_manifest_seq001_v001 import log_prediction as manifest_log, adjust_weight
        manifest_log(
            target_pred.get('predicted_intent', 'unknown'),
            actual_intent,
            list(pred_files),
            actual_files
        )
        
        # Adjust weights based on score
        if score > 0.8:
            adjust_weight('intent_match', 0.02, f'high accuracy on {actual_intent}')
        elif score < 0.3:
            adjust_weight('intent_match', -0.02, f'missed {actual_intent}')
        
        # Mark as graded
        target_pred['graded'] = True
        target_pred['actual_intent'] = actual_intent
        target_pred['actual_files'] = actual_files
        target_pred['score'] = score
        
        # Rewrite predictions file
        with open(pred_file, 'w', encoding='utf-8') as f:
            for p in predictions:
                f.write(json.dumps(p, ensure_ascii=False) + '\n')
        
    except Exception:
        pass
    
    return score


def select_template(buffer: str, ctx: dict | None = None) -> str:
    """Select the best Copilot template based on profile + signals.
    
    Returns template name: '/debug', '/build', '/review'
    """
    intelligent_ctx = get_intelligent_context(buffer, ctx or {})
    
    # Profile template has priority if high confidence
    if intelligent_ctx['profile_confidence'] > 0.7:
        return intelligent_ctx['template']
    
    # Fall back to signal-based detection
    ctx = ctx or {}
    state = ctx.get('operator_state', {}).get('dominant', 'unknown')
    
    if state in ('frustrated', 'hesitant'):
        return '/debug'
    
    # Check for bug-related keywords
    buf_lower = buffer.lower()
    if any(k in buf_lower for k in ('bug', 'fix', 'broken', 'error', 'fail')):
        return '/debug'
    if any(k in buf_lower for k in ('review', 'audit', 'check', 'test')):
        return '/review'
    
    return '/build'


def grade_and_learn(buffer: str, completion: str, outcome: str,
                    files_touched: list[str] | None = None,
                    actual_intent: str | None = None) -> dict:
    """Full grading cycle: grade completion, update profiles, adjust weights.
    
    Call this when a completion outcome is known.
    Returns grading summary.
    """
    summary = {
        'outcome': outcome,
        'profile_updated': False,
        'weight_adjusted': False,
        'new_profile': None,
    }
    
    try:
        from .tc_manifest_seq001_v001 import update_intent_profile, match_intent_profile
        
        # Check if this matches an existing profile
        name, profile, score = match_intent_profile(buffer)
        
        if name and score > 0.3:
            # Existing profile — record hit and possibly boost confidence
            if outcome in ('accepted', 'rewarded'):
                new_conf = min(0.99, profile.get('confidence', 0.5) + 0.03)
                update_intent_profile(name, confidence=new_conf, hit=True)
                summary['profile_updated'] = True
            elif outcome in ('dismissed', 'rejected'):
                new_conf = max(0.1, profile.get('confidence', 0.5) - 0.05)
                update_intent_profile(name, confidence=new_conf)
                summary['profile_updated'] = True
        else:
            # No profile match — maybe we should create one?
            # Only create if this was a successful interaction
            if outcome in ('accepted', 'rewarded') and files_touched:
                # Extract triggers for new profile
                from .tc_profile_seq001_v001 import extract_session_triggers
                triggers = extract_session_triggers([{'msg': buffer}], min_count=1)[:5]
                if len(triggers) >= 3:
                    profile_name = '_'.join(triggers[:2])
                    update_intent_profile(
                        name=profile_name,
                        trigger=triggers,
                        files=files_touched[:5],
                        template=select_template(buffer),
                        confidence=0.5,
                        hit=True
                    )
                    summary['new_profile'] = profile_name
        
    except Exception:
        pass
    
    return summary
