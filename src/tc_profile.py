"""Operator profile — 8 memory shards that learn who you are.

Mines prompt_compositions.jsonl, prompt_journal.jsonl, thought_completions.jsonl,
and os_keystrokes.jsonl to build a persistent, scary-accurate operator model.
Updated incrementally on every completion cycle.

Shards:
  1. voice       — vocabulary, sentence patterns, word frequencies, catchphrases
  2. rhythm      — typing speed distributions, pause patterns, time-of-day energy
  3. deletions   — what they delete, rewrite, abandon — the unsaid mind
  4. topics      — recurring subjects, module obsessions, concept clusters
  5. decisions   — accept/reject patterns, what completions land vs miss
  6. code_style  — naming conventions, indentation, import patterns, language quirks
  7. emotions    — cognitive state transitions, frustration triggers, flow triggers
  8. predictions — learned completion patterns that worked, operator-specific templates
"""
from __future__ import annotations
import ast
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .tc_constants import ROOT

PROFILE_PATH = ROOT / 'logs' / 'operator_profile_tc.json'
_profile_cache: dict | None = None
_profile_ts: float = 0


def _empty_profile() -> dict:
    return {
        'version': 1,
        'created': datetime.now(timezone.utc).isoformat(),
        'updated': None,
        'samples': 0,
        'shards': {
            'voice': {
                'top_words': {},       # word -> count (top 50)
                'bigrams': {},         # "w1 w2" -> count (top 30)
                'avg_words_per_msg': 0,
                'uses_caps': False,
                'punct_rate': 0.0,     # how often they use punctuation
                'catchphrases': [],    # recurring 3+ word phrases
                'filler_words': {},    # "like", "also", "just" etc
            },
            'rhythm': {
                'avg_wpm': 0,
                'wpm_p25': 0,
                'wpm_p75': 0,
                'avg_del_ratio': 0,
                'peak_hours_utc': [],
                'session_lengths': [], # recent session durations in minutes
                'avg_pause_before_send_ms': 0,
            },
            'deletions': {
                'deleted_words': {},   # word fragment -> count
                'rewrite_patterns': [], # (before_pattern, after_pattern)
                'abandon_rate': 0,     # % of started messages never sent
                'top_unsaid': [],      # most deleted complete words
            },
            'topics': {
                'module_mentions': {}, # module_name -> mention_count
                'concept_clusters': [],# groups of co-occurring words
                'recent_focus': [],    # last 5 dominant topics
                'recurring_themes': {},# theme -> count
            },
            'decisions': {
                'accept_rate': 0,
                'reward_rate': 0,
                'total_completions': 0,
                'accepted_patterns': [],  # buffer patterns that led to accepts
                'rejected_patterns': [],  # buffer patterns that led to rejects
                'sweet_spot_len': 0,      # buffer length most likely to accept
            },
            'code_style': {
                'preferred_quotes': 'single',
                'uses_type_hints': False,
                'import_style': 'from_x',  # from_x | import_x | mixed
                'naming_convention': 'snake_case',
                'avg_func_length': 0,
                'common_patterns': [],     # recurring code structures
            },
            'emotions': {
                'state_distribution': {},  # state -> percentage
                'frustration_triggers': [],# modules/topics that cause frustration
                'flow_triggers': [],       # what puts them in flow
                'state_transitions': {},   # "focused->frustrated" -> count
                'avg_hesitation': 0,
            },
            'predictions': {
                'working_templates': [],   # completion patterns that got accepted
                'dead_templates': [],      # patterns that always get rejected
                'topic_to_completion': {}, # topic -> successful completion style
                'operator_phrases': [],    # exact phrases they tend to type
            },
        },
    }


def _mine_code_style(root: Path | None = None) -> dict:
    """Scan .py files to learn operator's coding style. Zero LLM calls."""
    r = root or ROOT
    style: dict = {
        'preferred_quotes': 'single',
        'uses_type_hints': False,
        'import_style': 'from_x',
        'naming_convention': 'snake_case',
        'avg_func_length': 0,
        'common_patterns': [],
        'top_imports': [],
        'top_decorators': [],
        'top_exceptions': [],
        'var_name_samples': [],
        'func_name_samples': [],
        'error_handling_style': 'bare_except',
        'docstring_rate': 0.0,
        'list_comp_rate': 0.0,
        'fstring_rate': 0.0,
    }
    single_q = 0
    double_q = 0
    type_hint_count = 0
    from_imports = 0
    plain_imports = 0
    func_lengths: list[int] = []
    all_imports: Counter = Counter()
    decorators: Counter = Counter()
    exceptions: Counter = Counter()
    var_names: list[str] = []
    func_names: list[str] = []
    has_doc = 0
    total_funcs = 0
    list_comps = 0
    total_exprs = 0
    fstring_count = 0
    string_count = 0

    # scan src/ files (operator's code, not pigeon_brain/pigeon_compiler infra)
    scan_dirs = [r / 'src', r / 'client']
    py_files = []
    for d in scan_dirs:
        if d.is_dir():
            py_files.extend(f for f in d.iterdir() if f.suffix == '.py' and f.stat().st_size < 20000)
    # also recently modified files at root
    for f in r.iterdir():
        if f.suffix == '.py' and f.stat().st_size < 15000 and f.name.startswith(('test_', '_tmp_')):
            py_files.append(f)
    py_files = py_files[:40]  # cap

    for pf in py_files:
        try:
            src = pf.read_text('utf-8', errors='ignore')
        except Exception:
            continue
        # quote style
        single_q += src.count("'") - src.count("\\'")
        double_q += src.count('"') - src.count('\\"')
        # string patterns
        string_count += len(re.findall(r'["\']', src))
        fstring_count += len(re.findall(r'f["\']', src))
        # list comprehensions
        list_comps += len(re.findall(r'\[.+\bfor\b.+\bin\b', src))
        total_exprs += src.count('\n')
        # parse AST
        try:
            tree = ast.parse(src, filename=str(pf))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                plain_imports += 1
                for alias in node.names:
                    all_imports[alias.name.split('.')[0]] += 1
            elif isinstance(node, ast.ImportFrom):
                from_imports += 1
                if node.module:
                    all_imports[node.module.split('.')[0]] += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_funcs += 1
                func_names.append(node.name)
                # type hints
                if node.returns:
                    type_hint_count += 1
                for arg in node.args.args:
                    if arg.annotation:
                        type_hint_count += 1
                # func length
                if node.body:
                    lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 5
                    func_lengths.append(lines)
                # docstring
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                    has_doc += 1
            elif isinstance(node, ast.ExceptHandler):
                if node.type:
                    if isinstance(node.type, ast.Name):
                        exceptions[node.type.id] += 1
                    elif isinstance(node.type, ast.Attribute):
                        exceptions[node.type.attr] += 1
                else:
                    exceptions['bare'] += 1
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                var_names.append(node.id)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_names.append(target.id)

        # decorators
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators[dec.id] += 1
                    elif isinstance(dec, ast.Attribute):
                        decorators[dec.attr] += 1

    # compile results
    style['preferred_quotes'] = 'double' if double_q > single_q else 'single'
    style['uses_type_hints'] = type_hint_count > total_funcs * 0.3 if total_funcs else False
    if from_imports + plain_imports > 0:
        ratio = from_imports / (from_imports + plain_imports)
        style['import_style'] = 'from_x' if ratio > 0.6 else 'import_x' if ratio < 0.3 else 'mixed'
    # naming convention — check if func_names use camelCase or snake_case
    camel = sum(1 for n in func_names if re.search(r'[a-z][A-Z]', n))
    snake = sum(1 for n in func_names if '_' in n)
    style['naming_convention'] = 'camelCase' if camel > snake else 'snake_case'
    style['avg_func_length'] = round(sum(func_lengths) / len(func_lengths), 1) if func_lengths else 0
    style['top_imports'] = [m for m, _ in all_imports.most_common(10)]
    style['top_decorators'] = [d for d, _ in decorators.most_common(5)]
    style['top_exceptions'] = [e for e, _ in exceptions.most_common(5)]
    style['var_name_samples'] = list(set(var_names))[:20]
    style['func_name_samples'] = list(set(func_names))[:20]
    if exceptions:
        most_exc = exceptions.most_common(1)[0][0]
        style['error_handling_style'] = 'bare_except' if most_exc == 'bare' else f'specific({most_exc})'
    style['docstring_rate'] = round(has_doc / total_funcs, 2) if total_funcs else 0
    style['list_comp_rate'] = round(list_comps / max(total_exprs, 1), 4)
    style['fstring_rate'] = round(fstring_count / max(string_count, 1), 3)
    return style


def load_profile() -> dict:
    global _profile_cache, _profile_ts
    now = time.time()
    if _profile_cache and (now - _profile_ts) < 60:
        return _profile_cache
    if PROFILE_PATH.exists():
        try:
            _profile_cache = json.loads(PROFILE_PATH.read_text('utf-8', errors='ignore'))
            _profile_ts = now
            return _profile_cache
        except Exception:
            pass
    _profile_cache = _empty_profile()
    _profile_ts = now
    return _profile_cache


def save_profile(profile: dict):
    global _profile_cache, _profile_ts
    profile['updated'] = datetime.now(timezone.utc).isoformat()
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=1),
        encoding='utf-8',
    )
    _profile_cache = profile
    _profile_ts = time.time()


def update_profile_from_completion(buffer: str, completion: str, outcome: str,
                                   context: str = '', repo: str = ''):
    """Incrementally update profile after each completion event."""
    profile = load_profile()
    profile['samples'] += 1
    s = profile['shards']

    # --- voice shard ---
    words = buffer.lower().split()
    voice = s['voice']
    tw = voice['top_words']
    for w in words:
        if len(w) > 2 and w.isalpha():
            tw[w] = tw.get(w, 0) + 1
    # keep top 50
    if len(tw) > 80:
        voice['top_words'] = dict(Counter(tw).most_common(50))
    # bigrams
    bg = voice['bigrams']
    for i in range(len(words) - 1):
        if len(words[i]) > 2 and len(words[i+1]) > 2:
            key = f'{words[i]} {words[i+1]}'
            bg[key] = bg.get(key, 0) + 1
    if len(bg) > 60:
        voice['bigrams'] = dict(Counter(bg).most_common(30))
    # avg words per msg (rolling)
    n = profile['samples']
    voice['avg_words_per_msg'] = round(
        voice['avg_words_per_msg'] * (n-1)/n + len(words)/n, 1)
    voice['uses_caps'] = voice['uses_caps'] or any(c.isupper() for c in buffer[:20])
    # filler words
    fillers = {'like', 'also', 'just', 'basically', 'literally', 'actually',
               'maybe', 'kinda', 'gonna', 'wanna', 'gotta', 'tbh', 'ngl'}
    for w in words:
        if w in fillers:
            voice['filler_words'][w] = voice['filler_words'].get(w, 0) + 1

    # --- topics shard ---
    topics = s['topics']
    mm = topics['module_mentions']
    mod_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{3,}', buffer)
    for mw in mod_words:
        ml = mw.lower()
        if '_' in ml or ml in ('thought', 'completer', 'streaming', 'import',
                                'rewriter', 'compiler', 'entropy', 'profile'):
            mm[ml] = mm.get(ml, 0) + 1
    if len(mm) > 60:
        topics['module_mentions'] = dict(Counter(mm).most_common(40))
    # recent focus
    if words:
        key_words = [w for w in words if len(w) > 4 and w.isalpha()][:3]
        if key_words:
            topics['recent_focus'] = (topics['recent_focus'] + [' '.join(key_words)])[-5:]
    # recurring themes
    themes = topics['recurring_themes']
    theme_keys = {
        'debugging': {'fix', 'bug', 'error', 'broken', 'glitch', 'crash', 'fail'},
        'building': {'build', 'create', 'make', 'implement', 'write', 'add'},
        'testing': {'test', 'verify', 'check', 'run', 'launch', 'relaunch'},
        'auditing': {'audit', 'health', 'entropy', 'compliance', 'drift'},
        'exploring': {'what', 'how', 'why', 'show', 'explain', 'look'},
        'restructuring': {'split', 'refactor', 'rename', 'move', 'reorganize'},
    }
    word_set = set(words)
    for theme, keywords in theme_keys.items():
        if word_set & keywords:
            themes[theme] = themes.get(theme, 0) + 1

    # --- decisions shard ---
    dec = s['decisions']
    dec['total_completions'] += 1
    if outcome in ('accepted', 'rewarded'):
        old_rate = dec['accept_rate']
        dec['accept_rate'] = round(old_rate * (n-1)/n + 1/n, 3)
        # store what worked
        pattern = buffer[-50:].strip()
        dec['accepted_patterns'] = (dec['accepted_patterns'] + [pattern])[-15:]
        if outcome == 'rewarded':
            dec['reward_rate'] = round(
                dec['reward_rate'] * (n-1)/n + 1/n, 3)
        # track sweet spot length
        buf_len = len(buffer)
        dec['sweet_spot_len'] = round(
            dec['sweet_spot_len'] * (n-1)/n + buf_len/n, 0)
    else:
        dec['accept_rate'] = round(dec['accept_rate'] * (n-1)/n, 3)
        pattern = buffer[-50:].strip()
        dec['rejected_patterns'] = (dec['rejected_patterns'] + [pattern])[-10:]

    # --- predictions shard ---
    pred = s['predictions']
    if outcome in ('accepted', 'rewarded'):
        entry = {'buf_tail': buffer[-40:], 'comp_head': completion[:60], 'outcome': outcome}
        pred['working_templates'] = (pred['working_templates'] + [entry])[-20:]
        # operator phrases
        if len(buffer) > 10:
            pred['operator_phrases'] = (pred['operator_phrases'] + [buffer[-60:]])[-15:]
    elif outcome in ('dismissed', 'ignored'):
        entry = {'buf_tail': buffer[-40:], 'comp_head': completion[:40]}
        pred['dead_templates'] = (pred['dead_templates'] + [entry])[-10:]

    # --- code_style shard (incremental from code buffers) ---
    code_indicators = sum(1 for sig in ('def ', 'class ', 'import ', 'self.', ' = ',
                                         '()', 'return ', '    ') if sig in buffer)
    if code_indicators >= 2:
        cs = s.get('code_style', {})
        # learn from accepted code patterns
        if outcome in ('accepted', 'rewarded') and completion:
            combined = buffer + completion
            cp = cs.get('common_patterns', [])
            # extract short patterns from accepted code
            lines = combined.strip().split('\n')
            for line in lines[-3:]:
                stripped = line.strip()
                if stripped and len(stripped) > 10 and len(stripped) < 80:
                    cp.append(stripped)
            cs['common_patterns'] = cp[-20:]
            s['code_style'] = cs

    save_profile(profile)


def update_profile_from_composition(comp: dict):
    """Update profile from a raw composition event (from prompt_compositions.jsonl)."""
    profile = load_profile()
    s = profile['shards']

    # --- rhythm shard ---
    rhythm = s['rhythm']
    signals = comp.get('signals', {})
    wpm = signals.get('wpm', 0)
    if wpm > 0:
        n = max(profile['samples'], 1)
        rhythm['avg_wpm'] = round(rhythm['avg_wpm'] * (n-1)/n + wpm/n, 1)
    rhythm['avg_del_ratio'] = round(
        rhythm['avg_del_ratio'] * 0.95 + comp.get('deletion_ratio', 0) * 0.05, 4)

    # --- deletions shard ---
    dels = s['deletions']
    for dw in comp.get('deleted_words', []):
        word = dw if isinstance(dw, str) else dw.get('word', '')
        if word and len(word) > 2:
            dels['deleted_words'][word.lower()] = dels['deleted_words'].get(word.lower(), 0) + 1
    if len(dels['deleted_words']) > 60:
        dels['deleted_words'] = dict(Counter(dels['deleted_words']).most_common(40))
    # top unsaid — complete words that got deleted
    dels['top_unsaid'] = [w for w, c in Counter(dels['deleted_words']).most_common(8)
                          if len(w) > 3]

    # --- emotions shard ---
    emo = s['emotions']
    state = comp.get('cognitive_state', 'unknown')
    sd = emo['state_distribution']
    sd[state] = sd.get(state, 0) + 1
    # normalize to percentages
    total = sum(sd.values())
    emo['avg_hesitation'] = round(
        emo['avg_hesitation'] * 0.95 + signals.get('hesitation_score', 0) * 0.05, 3)

    save_profile(profile)


def bootstrap_profile():
    """Full rebuild from all historical data. Run once."""
    profile = _empty_profile()
    s = profile['shards']
    print('[profile] bootstrapping from historical data...')

    # --- Mine compositions ---
    comp_path = ROOT / 'logs' / 'prompt_compositions.jsonl'
    if comp_path.exists():
        entries = []
        for line in comp_path.read_text('utf-8', errors='ignore').strip().splitlines():
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
        print(f'  compositions: {len(entries)}')
        wpms = []
        for e in entries:
            sig = e.get('signals', {})
            wpm = sig.get('wpm', 0)
            if wpm > 0:
                wpms.append(wpm)
            # voice from final text
            text = e.get('final_text', '').lower()
            words = text.split()
            for w in words:
                if len(w) > 2 and w.isalpha():
                    s['voice']['top_words'][w] = s['voice']['top_words'].get(w, 0) + 1
            for i in range(len(words) - 1):
                if len(words[i]) > 2 and len(words[i+1]) > 2:
                    key = f'{words[i]} {words[i+1]}'
                    s['voice']['bigrams'][key] = s['voice']['bigrams'].get(key, 0) + 1
            # fillers
            fillers = {'like', 'also', 'just', 'basically', 'literally', 'actually',
                       'maybe', 'kinda', 'gonna', 'wanna'}
            for w in words:
                if w in fillers:
                    s['voice']['filler_words'][w] = s['voice']['filler_words'].get(w, 0) + 1
            # deletions
            for dw in e.get('deleted_words', []):
                word = dw if isinstance(dw, str) else dw.get('word', '')
                if word and len(word) > 2:
                    s['deletions']['deleted_words'][word.lower()] = \
                        s['deletions']['deleted_words'].get(word.lower(), 0) + 1
            # emotions
            state = e.get('cognitive_state', 'unknown')
            s['emotions']['state_distribution'][state] = \
                s['emotions']['state_distribution'].get(state, 0) + 1
            # deletions ratio
            s['rhythm']['avg_del_ratio'] = round(
                sum(e2.get('deletion_ratio', 0) for e2 in entries) / len(entries), 4) \
                if entries else 0
            # hours
            ts = e.get('ts', '')
            if 'T' in ts:
                try:
                    h = int(ts.split('T')[1][:2])
                    s['rhythm'].setdefault('_hours', Counter())[h] += 1
                except Exception:
                    pass
            # themes
            word_set = set(words)
            theme_keys = {
                'debugging': {'fix', 'bug', 'error', 'broken', 'glitch', 'crash'},
                'building': {'build', 'create', 'make', 'implement', 'write', 'add'},
                'testing': {'test', 'verify', 'check', 'run', 'launch'},
                'auditing': {'audit', 'health', 'entropy', 'compliance'},
                'exploring': {'what', 'how', 'why', 'show', 'explain'},
                'restructuring': {'split', 'refactor', 'rename', 'move'},
            }
            for theme, keywords in theme_keys.items():
                if word_set & keywords:
                    s['topics']['recurring_themes'][theme] = \
                        s['topics']['recurring_themes'].get(theme, 0) + 1

        # finalize rhythm
        if wpms:
            wpms.sort()
            s['rhythm']['avg_wpm'] = round(sum(wpms) / len(wpms), 1)
            s['rhythm']['wpm_p25'] = round(wpms[len(wpms)//4], 1)
            s['rhythm']['wpm_p75'] = round(wpms[3*len(wpms)//4], 1)
        hours_counter = s['rhythm'].pop('_hours', Counter())
        if hours_counter:
            s['rhythm']['peak_hours_utc'] = [h for h, _ in hours_counter.most_common(5)]
        # avg words
        texts = [e.get('final_text', '') for e in entries if e.get('final_text')]
        if texts:
            s['voice']['avg_words_per_msg'] = round(
                sum(len(t.split()) for t in texts) / len(texts), 1)
        # caps
        s['voice']['uses_caps'] = any(
            any(c.isupper() for c in e.get('final_text', '')[:20])
            for e in entries[:50])
        # trim voice
        s['voice']['top_words'] = dict(Counter(s['voice']['top_words']).most_common(50))
        s['voice']['bigrams'] = dict(Counter(s['voice']['bigrams']).most_common(30))
        # trim deletions
        s['deletions']['deleted_words'] = dict(
            Counter(s['deletions']['deleted_words']).most_common(40))
        s['deletions']['top_unsaid'] = [
            w for w, c in Counter(s['deletions']['deleted_words']).most_common(8)
            if len(w) > 3]
        # catchphrases (3-grams with count > 3)
        trigrams = Counter()
        for e in entries:
            words = e.get('final_text', '').lower().split()
            for i in range(len(words) - 2):
                if all(len(words[i+j]) > 2 for j in range(3)):
                    trigrams[f'{words[i]} {words[i+1]} {words[i+2]}'] += 1
        s['voice']['catchphrases'] = [p for p, c in trigrams.most_common(10) if c >= 3]

    # --- Mine completions ---
    tc_path = ROOT / 'logs' / 'thought_completions.jsonl'
    if tc_path.exists():
        completions = []
        for line in tc_path.read_text('utf-8', errors='ignore').strip().splitlines():
            try:
                completions.append(json.loads(line))
            except Exception:
                continue
        print(f'  completions: {len(completions)}')
        accepted = [c for c in completions if c.get('accepted')]
        rejected = [c for c in completions if not c.get('accepted')]
        rewarded = [c for c in completions if c.get('reward')]
        total = len(completions)
        if total:
            s['decisions']['accept_rate'] = round(len(accepted) / total, 3)
            s['decisions']['reward_rate'] = round(len(rewarded) / total, 3)
            s['decisions']['total_completions'] = total
        if accepted:
            s['decisions']['accepted_patterns'] = [
                c.get('buffer', '')[-50:] for c in accepted[-15:]]
            s['decisions']['sweet_spot_len'] = round(
                sum(len(c.get('buffer', '')) for c in accepted) / len(accepted), 0)
            s['predictions']['working_templates'] = [
                {'buf_tail': c.get('buffer', '')[-40:],
                 'comp_head': c.get('completion', '')[:60],
                 'outcome': 'rewarded' if c.get('reward') else 'accepted'}
                for c in accepted[-20:]]
            s['predictions']['operator_phrases'] = [
                c.get('buffer', '')[-60:] for c in accepted[-15:] if len(c.get('buffer', '')) > 10]
        if rejected:
            s['decisions']['rejected_patterns'] = [
                c.get('buffer', '')[-50:] for c in rejected[-10:]]
            s['predictions']['dead_templates'] = [
                {'buf_tail': c.get('buffer', '')[-40:],
                 'comp_head': c.get('completion', '')[:40]}
                for c in rejected[-10:]]

    # --- Mine journal for module mentions ---
    pj_path = ROOT / 'logs' / 'prompt_journal.jsonl'
    if pj_path.exists():
        for line in pj_path.read_text('utf-8', errors='ignore').strip().splitlines():
            try:
                e = json.loads(line)
            except Exception:
                continue
            refs = e.get('module_refs', [])
            for r in refs:
                if isinstance(r, str) and len(r) > 2:
                    s['topics']['module_mentions'][r] = \
                        s['topics']['module_mentions'].get(r, 0) + 1
        if len(s['topics']['module_mentions']) > 60:
            s['topics']['module_mentions'] = dict(
                Counter(s['topics']['module_mentions']).most_common(40))

    # --- Mine code style from actual source files ---
    print('  mining code style...')
    s['code_style'] = _mine_code_style(ROOT)

    profile['samples'] = len(entries) if comp_path.exists() else 0
    save_profile(profile)
    print(f'[profile] bootstrapped — {profile["samples"]} samples, 8 shards written')
    return profile


def format_profile_for_prompt(profile: dict | None = None) -> str:
    """Compress profile into a prompt injection block."""
    if profile is None:
        profile = load_profile()
    s = profile.get('shards', {})
    if not s or profile.get('samples', 0) < 5:
        return ''
    lines = ['OPERATOR PROFILE (learned from their typing history):']

    # voice
    v = s.get('voice', {})
    if v.get('top_words'):
        top5 = Counter(v['top_words']).most_common(8)
        lines.append(f'  VOICE: top words=[{", ".join(w for w,_ in top5)}] '
                     f'avg {v.get("avg_words_per_msg",0):.0f} words/msg '
                     f'caps={"yes" if v.get("uses_caps") else "never"}')
    if v.get('catchphrases'):
        lines.append(f'  CATCHPHRASES: {"; ".join(v["catchphrases"][:5])}')
    if v.get('filler_words'):
        top_fill = Counter(v['filler_words']).most_common(4)
        lines.append(f'  FILLERS: {", ".join(f"{w}({c}x)" for w,c in top_fill)}')

    # rhythm
    r = s.get('rhythm', {})
    if r.get('avg_wpm'):
        lines.append(f'  RHYTHM: {r["avg_wpm"]:.0f} WPM (p25={r.get("wpm_p25",0):.0f} '
                     f'p75={r.get("wpm_p75",0):.0f}) del_ratio={r.get("avg_del_ratio",0):.1%} '
                     f'peak_hours={r.get("peak_hours_utc",[])}')

    # deletions — the unsaid mind
    d = s.get('deletions', {})
    if d.get('top_unsaid'):
        lines.append(f'  UNSAID MIND: they delete these words most: {", ".join(d["top_unsaid"][:6])}')
    if d.get('deleted_words'):
        top_del = Counter(d['deleted_words']).most_common(5)
        lines.append(f'  DELETE PATTERNS: {", ".join(f"{w}({c}x)" for w,c in top_del)}')

    # topics
    t = s.get('topics', {})
    if t.get('recurring_themes'):
        themes = Counter(t['recurring_themes']).most_common(5)
        lines.append(f'  OBSESSIONS: {", ".join(f"{th}({c}x)" for th,c in themes)}')
    if t.get('module_mentions'):
        mods = Counter(t['module_mentions']).most_common(6)
        lines.append(f'  MODULE FOCUS: {", ".join(f"{m}({c})" for m,c in mods)}')
    if t.get('recent_focus'):
        lines.append(f'  RECENT FOCUS: {" → ".join(t["recent_focus"][-3:])}')

    # decisions
    dec = s.get('decisions', {})
    if dec.get('total_completions'):
        lines.append(f'  DECISIONS: {dec["accept_rate"]:.0%} accept rate '
                     f'({dec["total_completions"]} total) '
                     f'reward={dec["reward_rate"]:.0%} '
                     f'sweet_spot={dec.get("sweet_spot_len",0):.0f} chars')

    # emotions
    emo = s.get('emotions', {})
    if emo.get('state_distribution'):
        total_states = sum(emo['state_distribution'].values())
        top_states = Counter(emo['state_distribution']).most_common(4)
        state_str = ', '.join(f'{st}={c/total_states:.0%}' for st, c in top_states)
        lines.append(f'  EMOTIONS: {state_str} avg_hes={emo.get("avg_hesitation",0):.2f}')

    # predictions — what works for THIS operator
    pred = s.get('predictions', {})
    if pred.get('working_templates'):
        lines.append(f'  WHAT WORKS ({len(pred["working_templates"])} templates):')
        for t in pred['working_templates'][-3:]:
            lines.append(f'    ★ "{t["buf_tail"][-30:]}" → "{t["comp_head"][:40]}"')
    if pred.get('dead_templates'):
        lines.append(f'  WHAT FAILS ({len(pred["dead_templates"])} anti-patterns):')
        for t in pred['dead_templates'][-2:]:
            lines.append(f'    ✗ "{t["buf_tail"][-30:]}" → "{t["comp_head"][:30]}"')

    # code style — how they write code
    cs = s.get('code_style', {})
    if cs.get('top_imports'):
        lines.append(f'  CODE DNA: quotes={cs["preferred_quotes"]} '
                     f'hints={"yes" if cs.get("uses_type_hints") else "no"} '
                     f'imports={cs.get("import_style","?")} '
                     f'naming={cs.get("naming_convention","?")} '
                     f'avg_func={cs.get("avg_func_length",0):.0f}lines '
                     f'docstrings={cs.get("docstring_rate",0):.0%} '
                     f'fstrings={cs.get("fstring_rate",0):.0%}')
        lines.append(f'  TOP IMPORTS: {", ".join(cs["top_imports"][:8])}')
        if cs.get('top_decorators'):
            lines.append(f'  DECORATORS: {", ".join(cs["top_decorators"][:5])}')
        if cs.get('error_handling_style'):
            lines.append(f'  ERROR STYLE: {cs["error_handling_style"]} '
                         f'exceptions=[{", ".join(cs.get("top_exceptions",[])[:4])}]')
        if cs.get('func_name_samples'):
            lines.append(f'  FUNC NAMES: {", ".join(cs["func_name_samples"][:10])}')

    if len(lines) <= 1:
        return ''
    lines.append('  USE this profile to write AS THEM. Match their vocabulary, rhythm, obsessions.')
    lines.append('  For CODE mode: match their quote style, naming, import patterns, error handling.')
    return '\n'.join(lines)
