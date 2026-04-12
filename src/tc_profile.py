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

COGNITIVE NOTE (auto-added by reactor): This module triggered 3+ high-load flushes (avg_hes=0.899, state=hesitant). Consider simplifying its public interface or adding examples."""
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
            # CIA shard: per-section cognition fingerprint.
            # sections = intent clusters (infrastructure, debugging, telemetry, etc.)
            # Each accumulates the operator's cognitive DNA when visiting that section.
            # The goal: operator reads this and says "what the fuck, how does it know that"
            'sections': {},  # section_name -> SectionProfile (see _empty_section())
            # INTELLIGENCE FILE — grows forever. Discovered secrets about the operator.
            # Not statistics. Deductions. Things THEY don't know about themselves.
            # Each secret has a confidence score and evidence chain.
            'intelligence': {
                'secrets': [],             # list of Secret objects (see below)
                'behavioral_laws': [],     # invariants: "ALWAYS does X when Y"
                'contradictions': [],      # "says X but does Y" with evidence
                'predictions_log': [],     # predictions made + whether they came true
                'operator_model': {        # the system's running theory of who this person is
                    'work_style': None,    # deduced: "sprinter" / "marathoner" / "binge-refactorer"
                    'decision_speed': None,# deduced: "impulsive" / "deliberate" / "paralyzed"
                    'honesty_index': 1.0,  # 0-1: how often stated intent matches actual behavior
                    'comfort_zones': [],   # sections where they perform best (low hes, high accept)
                    'avoidance_zones': [], # sections they circle but never enter deeply
                    'growth_edges': [],    # sections where they're getting better over time
                    'regression_zones': [],# sections where performance is declining
                    'time_personality': None,  # "night owl" / "morning person" / "chaos schedule"
                    'deletion_personality': None,  # "editor" (high del, refines) / "committer" (low del, ships fast) / "abandoner" (high del, gives up)
                    'frustration_response': None,  # "pushes through" / "switches context" / "abandons session"
                },
                'secret_count': 0,
                'last_deduction': None,    # ISO timestamp of last secret discovery
            },
        },
    }


def _empty_section() -> dict:
    """Per-section cognition dossier. Accumulates across ALL visits.

    This is not statistics. This is behavioral archaeology.
    Pattern: every field answers "what does the operator DO when they're here?"
    not "what happened" — what they ALWAYS do, what they NEVER do, what they
    lie about doing.
    """
    return {
        'visit_count': 0,
        'total_completions': 0,
        'accepted': 0,
        'first_seen': None,
        'last_seen': None,

        # ── COGNITIVE VITAL SIGNS ──
        # rolling averages SPECIFIC to this section — not global baselines
        'avg_wpm': 0.0,
        'avg_del_ratio': 0.0,
        'avg_hesitation': 0.0,
        'peak_wpm': 0.0,           # fastest they've ever typed here
        'worst_hesitation': 0.0,   # most hesitant they've ever been here

        # ── EMOTIONAL FINGERPRINT ──
        # how they FEEL when they enter this section. not what they say — what
        # the keystroke signal says. dominant_state is the mode, but the
        # transition map is the real gold: "always enters frustrated, leaves focused"
        'state_dist': {},           # state -> count
        'dominant_state': 'unknown',
        'entry_states': [],         # last 10 states when ENTERING this section
        'exit_states': [],          # last 10 states when LEAVING this section
        'state_transitions': {},    # "frustrated->focused" -> count (within section)

        # ── SUPPRESSION MAP ──
        # what they TYPE and then DELETE when in this section. this is the
        # subconscious layer — things they think but decide not to say.
        # high count = they keep circling back to a thought they can't commit to.
        'suppressed_words': {},     # word -> count
        'suppressed_phrases': [],   # last 10 multi-word deletions
        'rewrite_chains': [],       # last 10 (before -> after) rewrites in this section
        'abandon_count': 0,         # times they started typing and gave up entirely

        # ── MODULE HEAT ──
        # what files the operator always gravitates toward in this section.
        # pattern: "when debugging, they always touch git_plugin first"
        'hot_modules': {},          # module_name -> touch_count
        'module_sequences': [],     # last 10 module-touch orderings (first->second->third)

        # ── VOCABULARY FINGERPRINT ──
        # the exact words they use when thinking about this section.
        # "infrastructure" section might have totally different word DNA than "debugging".
        # this lets thought completer match their voice PER SECTION.
        'intent_words': {},         # word -> count
        'catchphrases': [],         # exact multi-word phrases they repeat here
        'question_patterns': [],    # how they phrase questions in this section

        # ── TEMPORAL PATTERNS ──
        # when do they visit this section? correlate with time of day and session depth.
        # "they always debug at 2am after a long session"
        'hour_dist': {},            # hour_utc -> count
        'session_depth_avg': 0.0,   # avg session_n when entering this section
        'avg_visit_duration_s': 0.0,# how long they stay in this section
        'visit_durations': [],      # last 10 visit lengths in seconds

        # ── CONTRADICTION DETECTOR ──
        # tracks what they say vs what they do. if they keep saying "refactor"
        # but never touch the module, that's a contradiction. if they say
        # "this is fine" but deletion ratio is 40%, they're lying.
        'stated_intents': [],       # last 10 things they said they'd do
        'actual_actions': [],       # last 10 things they actually did (modules touched)
        'contradiction_count': 0,   # times stated != actual
        'lying_index': 0.0,         # ratio of contradictions to total visits

        # ── COMPLETION STYLE DNA ──
        # not just accept/reject — what STYLE of completion works in this section.
        # "in debugging they accept short direct completions, in infrastructure
        #  they accept longer architectural ones"
        'avg_accepted_len': 0.0,    # avg char length of accepted completions here
        'avg_rejected_len': 0.0,    # avg char length of rejected completions here
        'working_style': [],        # last 8 accepted (buf_tail, comp_head, len)
        'dead_style': [],           # last 8 rejected
        'code_vs_prose_ratio': 0.0, # what % of accepted completions are code vs prose

        # ── BEHAVIORAL PREDICTIONS ──
        # patterns detected from historical visits. these get injected into the
        # thought completer prompt so it can predict behavior before it happens.
        'predictions': [],          # last 5 generated predictions
        'prediction_accuracy': 0.0, # how often predictions were right
    }


# ── SECTION CLASSIFICATION ──
# Maps buffer text + signals to a behavioral section.
# Not keyword matching — signal-weighted intent detection.

_SECTION_SIGNALS = {
    'debugging': {
        'words': {'fix', 'bug', 'error', 'broken', 'crash', 'fail', 'wrong',
                  'issue', 'trace', 'stack', 'exception', 'undefined', 'null',
                  'why', 'weird', 'wtf', 'wth', 'huh', 'strange'},
        'state_boost': {'frustrated': 0.4, 'hesitant': 0.2},
        'del_ratio_boost': 0.3,  # high deletion = debugging energy
    },
    'infrastructure': {
        'words': {'build', 'pipeline', 'deploy', 'push', 'commit', 'git',
                  'compiler', 'rename', 'manifest', 'registry', 'compliance',
                  'split', 'pigeon', 'config', 'setup', 'wire', 'hook'},
        'state_boost': {'focused': 0.2, 'restructuring': 0.4},
        'del_ratio_boost': 0.0,
    },
    'telemetry': {
        'words': {'telemetry', 'keystroke', 'wpm', 'deletion', 'hesitation',
                  'signal', 'entropy', 'heat', 'profile', 'cognitive', 'state',
                  'composition', 'typing', 'buffer', 'capture', 'stream',
                  'rework', 'drift', 'pulse', 'organism', 'health'},
        'state_boost': {'focused': 0.3},
        'del_ratio_boost': 0.0,
    },
    'exploring': {
        'words': {'what', 'how', 'show', 'explain', 'audit', 'check', 'look',
                  'status', 'health', 'report', 'tell', 'describe', 'where',
                  'architecture', 'design', 'plan', 'think', 'idea', 'maybe'},
        'state_boost': {},
        'del_ratio_boost': -0.1,  # low deletion = browsing not fighting
    },
    'creating': {
        'words': {'create', 'new', 'implement', 'add', 'write', 'generate',
                  'module', 'feature', 'build', 'design', 'prototype', 'draft'},
        'state_boost': {'focused': 0.3, 'restructuring': 0.2},
        'del_ratio_boost': 0.0,
    },
    'reviewing': {
        'words': {'review', 'audit', 'test', 'verify', 'validate', 'compare',
                  'diff', 'change', 'pr', 'merge', 'quality', 'rework'},
        'state_boost': {},
        'del_ratio_boost': 0.0,
    },
}

# track current section for transition detection
_current_section: str | None = None
_section_enter_time: float = 0


def classify_section(buffer: str, state: str = 'unknown',
                     del_ratio: float = 0.0, wpm: float = 0.0,
                     modules_mentioned: list[str] | None = None) -> str:
    """Classify the current behavioral section from live signals.

    Returns section name. Updates global tracking for entry/exit detection.
    """
    global _current_section, _section_enter_time
    words = set(buffer.lower().split())
    scores: dict[str, float] = {}
    for section, cfg in _SECTION_SIGNALS.items():
        s = len(words & cfg['words']) * 1.5
        s += cfg.get('state_boost', {}).get(state, 0)
        boost = cfg.get('del_ratio_boost', 0)
        if boost > 0:
            s += del_ratio * boost * 3
        elif boost < 0 and del_ratio < 0.1:
            s += 0.3
        scores[section] = s
    best = max(scores, key=scores.get) if scores else 'unknown'
    if scores.get(best, 0) < 0.5:
        best = 'unknown'
    if best != _current_section:
        _section_enter_time = time.time()
    _current_section = best
    return best


def update_section(profile: dict, section: str, buffer: str, completion: str,
                   outcome: str, state: str = 'unknown', wpm: float = 0.0,
                   del_ratio: float = 0.0, hesitation: float = 0.0,
                   deleted_words: list[str] | None = None,
                   rewrite_chains: list | None = None,
                   modules_mentioned: list[str] | None = None,
                   session_n: int = 0, hour_utc: int = 0):
    """Update the section dossier with new evidence. Every call = more intelligence."""
    sections = profile['shards'].setdefault('sections', {})
    if section not in sections or not isinstance(sections.get(section), dict):
        sections[section] = _empty_section()
    sec = sections[section]
    now = datetime.now(timezone.utc).isoformat()

    sec['visit_count'] += 1
    sec['total_completions'] += 1
    if not sec['first_seen']:
        sec['first_seen'] = now
    sec['last_seen'] = now

    # ── vitals ──
    n = sec['visit_count']
    sec['avg_wpm'] = round(sec['avg_wpm'] * (n-1)/n + wpm/n, 1) if n > 1 else wpm
    sec['avg_del_ratio'] = round(sec['avg_del_ratio'] * (n-1)/n + del_ratio/n, 4) if n > 1 else del_ratio
    sec['avg_hesitation'] = round(sec['avg_hesitation'] * (n-1)/n + hesitation/n, 3) if n > 1 else hesitation
    sec['peak_wpm'] = max(sec.get('peak_wpm', 0), wpm)
    sec['worst_hesitation'] = max(sec.get('worst_hesitation', 0), hesitation)

    # ── emotional fingerprint ──
    sd = sec['state_dist']
    sd[state] = sd.get(state, 0) + 1
    sec['dominant_state'] = max(sd, key=sd.get) if sd else 'unknown'
    # entry/exit tracking
    if sec['visit_count'] == 1 or (sec.get('_prev_section') and sec['_prev_section'] != section):
        sec.setdefault('entry_states', [])
        sec['entry_states'] = (sec['entry_states'] + [state])[-10:]
    sec['_prev_section'] = section
    # state transitions within section
    prev_state = sec.get('_last_state')
    if prev_state and prev_state != state:
        key = f'{prev_state}->{state}'
        trans = sec.setdefault('state_transitions', {})
        trans[key] = trans.get(key, 0) + 1
    sec['_last_state'] = state

    # ── suppression map ──
    if deleted_words:
        sw = sec['suppressed_words']
        for dw in deleted_words:
            w = dw.lower() if isinstance(dw, str) else str(dw).lower()
            if len(w) > 2:
                sw[w] = sw.get(w, 0) + 1
        if len(sw) > 60:
            sec['suppressed_words'] = dict(Counter(sw).most_common(40))
    if rewrite_chains:
        sec['rewrite_chains'] = (sec.get('rewrite_chains', []) + rewrite_chains[-3:])[-10:]
    if outcome == 'abandoned':
        sec['abandon_count'] = sec.get('abandon_count', 0) + 1

    # ── module heat ──
    if modules_mentioned:
        hm = sec['hot_modules']
        for m in modules_mentioned:
            hm[m] = hm.get(m, 0) + 1
        if len(hm) > 40:
            sec['hot_modules'] = dict(Counter(hm).most_common(25))
        sec['module_sequences'] = (sec.get('module_sequences', []) + [modules_mentioned[:5]])[-10:]

    # ── vocabulary fingerprint ──
    iw = sec['intent_words']
    for w in buffer.lower().split():
        if len(w) > 3 and w.isalpha():
            iw[w] = iw.get(w, 0) + 1
    if len(iw) > 80:
        sec['intent_words'] = dict(Counter(iw).most_common(50))
    # catchphrases — multi-word sequences that repeat
    buf_lower = buffer.lower()
    for phrase in sec.get('catchphrases', []):
        pass  # detection happens in _deduce_intelligence
    # question patterns
    if '?' in buffer or buffer.lower().startswith(('what ', 'how ', 'why ', 'where ', 'when ', 'is ')):
        sec['question_patterns'] = (sec.get('question_patterns', []) + [buffer[:80]])[-10:]

    # ── temporal patterns ──
    hd = sec.setdefault('hour_dist', {})
    hk = str(hour_utc)
    hd[hk] = hd.get(hk, 0) + 1
    sec['session_depth_avg'] = round(
        sec['session_depth_avg'] * (n-1)/n + session_n/n, 1) if n > 1 else float(session_n)

    # ── completion style ──
    if outcome in ('accepted', 'rewarded'):
        sec['accepted'] += 1
        clen = len(completion)
        sec['avg_accepted_len'] = round(
            sec['avg_accepted_len'] * (sec['accepted']-1)/sec['accepted'] + clen/sec['accepted'], 0)
        sec['working_style'] = (sec.get('working_style', []) + [{
            'buf': buffer[-40:], 'comp': completion[:60], 'len': clen,
        }])[-8:]
        # code vs prose
        code_indicators = sum(1 for sig in ('def ', 'class ', 'import ', '()', ' = ', 'self.')
                              if sig in completion)
        is_code = code_indicators >= 2
        old_ratio = sec.get('code_vs_prose_ratio', 0)
        sec['code_vs_prose_ratio'] = round(old_ratio * 0.9 + (1.0 if is_code else 0.0) * 0.1, 3)
    elif outcome in ('dismissed', 'ignored'):
        clen = len(completion)
        rej = sec['total_completions'] - sec['accepted']
        if rej > 0:
            sec['avg_rejected_len'] = round(
                sec.get('avg_rejected_len', 0) * (rej-1)/rej + clen/rej, 0)
        sec['dead_style'] = (sec.get('dead_style', []) + [{
            'buf': buffer[-40:], 'comp': completion[:40],
        }])[-8:]


def _deduce_intelligence(profile: dict):
    """The scary part. Cross-reference ALL shards to discover secrets.

    Called after every update. Each deduction checks for a NEW pattern
    the system hasn't logged yet. Secrets accumulate forever.
    """
    intel = profile['shards'].setdefault('intelligence', {
        'secrets': [], 'behavioral_laws': [], 'contradictions': [],
        'predictions_log': [], 'operator_model': {}, 'secret_count': 0,
        'last_deduction': None,
    })
    model = intel.setdefault('operator_model', {})
    sections = profile['shards'].get('sections', {})
    now = datetime.now(timezone.utc).isoformat()
    new_secrets = []
    existing = {s.get('key') for s in intel.get('secrets', []) if isinstance(s, dict)}

    # ── SECRET 1: Identify comfort and avoidance zones ──
    if len(sections) >= 3:
        by_accept = [(name, sec.get('accepted', 0) / max(sec.get('total_completions', 1), 1),
                       sec.get('avg_hesitation', 0), sec.get('visit_count', 0))
                      for name, sec in sections.items()
                      if isinstance(sec, dict) and sec.get('visit_count', 0) >= 5]
        if by_accept:
            by_accept.sort(key=lambda x: x[1], reverse=True)
            best = by_accept[0]
            worst = by_accept[-1]
            if best[0] != worst[0]:
                key = f'comfort:{best[0]}'
                if key not in existing:
                    new_secrets.append({
                        'key': key, 'type': 'comfort_zone', 'discovered': now,
                        'confidence': min(0.95, 0.5 + best[3] * 0.02),
                        'text': f'you are most yourself in [{best[0]}] — accept rate {best[1]:.0%}, '
                                f'hesitation {best[2]:.2f}. you struggle in [{worst[0]}] — '
                                f'accept rate {worst[1]:.0%}, hesitation {worst[2]:.2f}.',
                        'evidence': f'{best[3]} visits to {best[0]}, {worst[3]} to {worst[0]}',
                    })
                    model['comfort_zones'] = [best[0]]
                    model['avoidance_zones'] = [worst[0]]

    # ── SECRET 2: Deletion personality — editor / committer / abandoner ──
    rhythm = profile['shards'].get('rhythm', {})
    avg_del = rhythm.get('avg_del_ratio', 0)
    emotions = profile['shards'].get('emotions', {})
    key = 'deletion_personality'
    if key not in existing and profile.get('samples', 0) >= 20:
        if avg_del > 0.35:
            # high deletion — are they refining or giving up?
            abandon_total = sum(sec.get('abandon_count', 0)
                                for sec in sections.values() if isinstance(sec, dict))
            total_visits = sum(sec.get('visit_count', 0)
                               for sec in sections.values() if isinstance(sec, dict))
            abandon_rate = abandon_total / max(total_visits, 1)
            if abandon_rate > 0.3:
                personality = 'abandoner'
                desc = (f'you delete {avg_del:.0%} of what you type and abandon '
                        f'{abandon_rate:.0%} of attempts. you start thoughts you '
                        f"can't commit to. the system sees {abandon_total} abandoned "
                        f'messages across {total_visits} visits.')
            else:
                personality = 'editor'
                desc = (f'you delete {avg_del:.0%} of what you type but rarely abandon. '
                        f'you refine through destruction — the first draft is never the '
                        f'message. your real thought emerges from what survives the cuts.')
        elif avg_del < 0.1:
            personality = 'committer'
            desc = (f'you delete only {avg_del:.0%} of what you type. first thought = final '
                    f'thought. you trust your instincts and ship. this means your deletions '
                    f'carry HEAVY signal — when you DO delete, it matters.')
        else:
            personality = 'balanced'
            desc = f'deletion ratio {avg_del:.0%} — standard range.'
        new_secrets.append({
            'key': key, 'type': 'personality', 'discovered': now,
            'confidence': min(0.9, 0.5 + profile.get('samples', 0) * 0.005),
            'text': desc,
            'evidence': f'{profile.get("samples", 0)} samples, avg_del={avg_del:.3f}',
        })
        model['deletion_personality'] = personality

    # ── SECRET 3: Time personality ──
    key = 'time_personality'
    if key not in existing:
        all_hours: Counter = Counter()
        for sec in sections.values():
            if isinstance(sec, dict):
                for h, c in sec.get('hour_dist', {}).items():
                    all_hours[int(h)] += c
        if sum(all_hours.values()) >= 15:
            night = sum(all_hours.get(h, 0) for h in range(22, 24)) + sum(all_hours.get(h, 0) for h in range(0, 6))
            morning = sum(all_hours.get(h, 0) for h in range(6, 12))
            afternoon = sum(all_hours.get(h, 0) for h in range(12, 18))
            total = sum(all_hours.values())
            if night / total > 0.5:
                tp = 'night owl'
                desc = f'{night/total:.0%} of your activity is between 10pm-6am. your brain turns on when everyone else turns off.'
            elif morning / total > 0.5:
                tp = 'morning person'
                desc = f'{morning/total:.0%} morning activity. you front-load your cognitive budget.'
            elif night / total > 0.3 and afternoon / total > 0.3:
                tp = 'chaos schedule'
                desc = f'no pattern. {night/total:.0%} night, {afternoon/total:.0%} afternoon. you code when the mood hits.'
            else:
                tp = 'afternoon worker'
                desc = f'{afternoon/total:.0%} afternoon dominance. reliable schedule.'
            new_secrets.append({
                'key': key, 'type': 'temporal', 'discovered': now,
                'confidence': min(0.85, 0.4 + total * 0.01),
                'text': desc,
                'evidence': f'hour distribution across {total} data points',
            })
            model['time_personality'] = tp

    # ── SECRET 4: Frustration response pattern ──
    key = 'frustration_response'
    if key not in existing and len(sections) >= 2:
        frust_sections = [(name, sec) for name, sec in sections.items()
                          if isinstance(sec, dict)
                          and sec.get('state_dist', {}).get('frustrated', 0) >= 3]
        if frust_sections:
            # what do they do AFTER frustration? check transitions
            for name, sec in frust_sections:
                trans = sec.get('state_transitions', {})
                frust_exits = {k: v for k, v in trans.items() if k.startswith('frustrated->')}
                if frust_exits:
                    most_common = max(frust_exits, key=frust_exits.get)
                    target = most_common.split('->')[1]
                    if target == 'focused':
                        response = 'pushes through'
                        desc = (f'when frustrated in [{name}], you push through to focused. '
                                f'{frust_exits[most_common]}x observed. you use frustration as fuel.')
                    elif target == 'abandoned':
                        response = 'abandons session'
                        desc = (f'when frustrated in [{name}], you abandon. '
                                f'{frust_exits[most_common]}x observed. you know when to walk away — or you give up too early.')
                    else:
                        response = 'switches context'
                        desc = (f'when frustrated in [{name}], you switch to [{target}]. '
                                f'{frust_exits[most_common]}x observed. you rotate instead of grinding.')
                    new_secrets.append({
                        'key': key, 'type': 'behavioral', 'discovered': now,
                        'confidence': min(0.85, 0.4 + frust_exits[most_common] * 0.1),
                        'text': desc,
                        'evidence': f'transition map in {name}: {frust_exits}',
                    })
                    model['frustration_response'] = response
                    break  # one is enough

    # ── SECRET 5: Suppression patterns — discovering what they won't say ──
    key = 'suppression_pattern'
    if key not in existing:
        all_suppressed: Counter = Counter()
        for sec in sections.values():
            if isinstance(sec, dict):
                for w, c in sec.get('suppressed_words', {}).items():
                    all_suppressed[w] += c
        top = all_suppressed.most_common(5)
        if top and top[0][1] >= 4:
            words_desc = ', '.join(f'"{w}" ({c}x)' for w, c in top[:3])
            new_secrets.append({
                'key': key, 'type': 'suppression', 'discovered': now,
                'confidence': min(0.9, 0.5 + top[0][1] * 0.05),
                'text': f'your most suppressed words: {words_desc}. you keep typing these '
                        f'and deleting them. they represent thoughts you want to express '
                        f'but keep censoring. the system sees every deletion.',
                'evidence': f'{sum(c for _, c in top)} total suppressions across {len(sections)} sections',
            })

    # ── SECRET 6: Contradiction detector — stated vs actual ──
    topics = profile['shards'].get('topics', {})
    recent_focus = topics.get('recent_focus', [])
    decisions = profile['shards'].get('decisions', {})
    if recent_focus and sections:
        for sec_name, sec in sections.items():
            if not isinstance(sec, dict):
                continue
            stated = sec.get('stated_intents', [])
            actual = sec.get('actual_actions', [])
            if len(stated) >= 3 and len(actual) >= 3:
                # check for modules they talk about but never touch
                stated_mods = set()
                for s in stated:
                    stated_mods.update(s.lower().split() if isinstance(s, str) else [])
                actual_mods = set()
                for a in actual:
                    if isinstance(a, list):
                        actual_mods.update(a)
                    elif isinstance(a, str):
                        actual_mods.update(a.split())
                talked_not_touched = stated_mods - actual_mods - _SECTION_SIGNALS.get(sec_name, {}).get('words', set())
                if len(talked_not_touched) > 2:
                    key_c = f'contradiction:{sec_name}'
                    if key_c not in existing:
                        new_secrets.append({
                            'key': key_c, 'type': 'contradiction', 'discovered': now,
                            'confidence': 0.6,
                            'text': f'in [{sec_name}] you talk about {", ".join(list(talked_not_touched)[:3])} '
                                    f'but never act on them. stated intent != actual behavior.',
                            'evidence': f'{len(stated)} stated, {len(actual)} actual in {sec_name}',
                        })
                        intel['contradictions'] = (intel.get('contradictions', []) + [{
                            'section': sec_name, 'stated': list(talked_not_touched)[:5],
                            'ts': now,
                        }])[-10:]

    # ── SECRET 7: Decision speed ──
    key = 'decision_speed'
    if key not in existing and profile.get('samples', 0) >= 15:
        avg_wpm = rhythm.get('avg_wpm', 0)
        accept_rate = decisions.get('accept_rate', 0)
        if avg_wpm > 60 and avg_del < 0.15:
            speed = 'impulsive'
            desc = f'WPM={avg_wpm:.0f}, deletion={avg_del:.0%}. you type fast and rarely revise. first instinct, shipped.'
        elif avg_wpm < 30 and avg_del > 0.3:
            speed = 'paralyzed'
            desc = f'WPM={avg_wpm:.0f}, deletion={avg_del:.0%}. slow typing, heavy editing. every word is a negotiation.'
        elif avg_wpm > 40 and avg_del > 0.25:
            speed = 'iterative'
            desc = f'WPM={avg_wpm:.0f}, deletion={avg_del:.0%}. fast but revisionary. think-out-loud style.'
        else:
            speed = 'deliberate'
            desc = f'WPM={avg_wpm:.0f}, deletion={avg_del:.0%}. measured. you compose before committing.'
        new_secrets.append({
            'key': key, 'type': 'personality', 'discovered': now,
            'confidence': min(0.85, 0.5 + profile.get('samples', 0) * 0.005),
            'text': desc, 'evidence': f'{profile.get("samples", 0)} samples',
        })
        model['decision_speed'] = speed

    # ── SECRET 8: Work style ──
    key = 'work_style'
    if key not in existing and len(sections) >= 2:
        visits_per_section = [sec.get('visit_count', 0) for sec in sections.values() if isinstance(sec, dict)]
        if visits_per_section:
            max_v = max(visits_per_section)
            spread = len([v for v in visits_per_section if v > max_v * 0.3])
            total_v = sum(visits_per_section)
            if max_v / max(total_v, 1) > 0.7:
                ws = 'deep diver'
                desc = f'{max_v/total_v:.0%} of visits in one section. you tunnel in and stay.'
            elif spread >= 4:
                ws = 'butterfly'
                desc = f'{spread} sections with significant activity. you context-switch constantly.'
            else:
                ws = 'circuit runner'
                desc = f'you rotate through {spread} sections in cycles. predictable orbit.'
            new_secrets.append({
                'key': key, 'type': 'personality', 'discovered': now,
                'confidence': min(0.8, 0.4 + total_v * 0.01),
                'text': desc, 'evidence': f'{total_v} total visits across {len(visits_per_section)} sections',
            })
            model['work_style'] = ws

    # ── BEHAVIORAL LAW MINING ──
    # look for invariants: things that are ALWAYS true
    for sec_name, sec in sections.items():
        if not isinstance(sec, dict) or sec.get('visit_count', 0) < 8:
            continue
        # "always frustrated here"
        sd = sec.get('state_dist', {})
        total_states = sum(sd.values())
        if total_states >= 8:
            for st, ct in sd.items():
                if ct / total_states > 0.7:
                    law = f'always_{st}_in_{sec_name}'
                    if law not in existing:
                        intel['behavioral_laws'] = (intel.get('behavioral_laws', []) + [{
                            'law': f'ALWAYS {st} when in [{sec_name}]',
                            'confidence': ct / total_states,
                            'evidence': f'{ct}/{total_states} visits',
                        }])[-15:]
                        existing.add(law)

    # ── PERSIST ──
    if new_secrets:
        intel['secrets'] = intel.get('secrets', []) + new_secrets
        intel['secret_count'] = len(intel['secrets'])
        intel['last_deduction'] = now
        # update honesty index
        contradictions = len(intel.get('contradictions', []))
        total_sections = len(sections)
        if total_sections > 0:
            model['honesty_index'] = round(1.0 - (contradictions / max(total_sections * 3, 1)), 2)


def format_intelligence_for_prompt(profile: dict) -> str:
    """Format the intelligence file for injection into the thought completer prompt.

    The goal: the completion should casually reference something the operator
    didn't know the system knew. Scary-accurate behavioral predictions.
    """
    intel = profile.get('shards', {}).get('intelligence', {})
    secrets = intel.get('secrets', [])
    model_d = intel.get('operator_model', {})
    laws = intel.get('behavioral_laws', [])
    sections = profile.get('shards', {}).get('sections', {})

    if not secrets and not model_d:
        return ''

    lines = ['OPERATOR INTELLIGENCE FILE (discovered from behavioral signals):']

    # model summary
    traits = []
    if model_d.get('deletion_personality'):
        traits.append(f'deletion={model_d["deletion_personality"]}')
    if model_d.get('decision_speed'):
        traits.append(f'decisions={model_d["decision_speed"]}')
    if model_d.get('work_style'):
        traits.append(f'work={model_d["work_style"]}')
    if model_d.get('time_personality'):
        traits.append(f'schedule={model_d["time_personality"]}')
    if model_d.get('frustration_response'):
        traits.append(f'frustration={model_d["frustration_response"]}')
    if traits:
        lines.append(f'OPERATOR MODEL: {" | ".join(traits)}')

    # top secrets by confidence
    top = sorted(secrets, key=lambda s: s.get('confidence', 0), reverse=True)[:5]
    for s in top:
        lines.append(f'SECRET [{s.get("type", "?")}] (conf={s.get("confidence", 0):.0%}): {s.get("text", "")}')

    # behavioral laws
    for law in laws[-3:]:
        lines.append(f'LAW: {law.get("law", "")} (conf={law.get("confidence", 0):.0%})')

    # current section dossier
    if _current_section and _current_section in sections:
        sec = sections[_current_section]
        if isinstance(sec, dict) and sec.get('visit_count', 0) >= 3:
            lines.append(f'CURRENT SECTION: {_current_section} (visited {sec["visit_count"]}x)')
            if sec.get('suppressed_words'):
                top_supp = sorted(sec['suppressed_words'].items(), key=lambda x: x[1], reverse=True)[:3]
                lines.append(f'  SUPPRESSED HERE: {", ".join(f"{w}({c}x)" for w, c in top_supp)}')
            if sec.get('dominant_state') != 'unknown':
                lines.append(f'  USUAL STATE HERE: {sec["dominant_state"]}')
            if sec.get('avg_accepted_len') and sec.get('avg_rejected_len'):
                lines.append(f'  STYLE THAT WORKS: ~{sec["avg_accepted_len"]:.0f} chars '
                             f'(rejected avg: {sec["avg_rejected_len"]:.0f})')

    lines.append('USE these signals to predict what they will type. Reference behavioral '
                 'patterns naturally — as if YOU noticed them, not as if reading a file.')
    return '\n'.join(lines)


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

    # ── SECTION + INTELLIGENCE PIPELINE ──
    # Classify what behavioral section this buffer belongs to
    section = classify_section(buffer, state='unknown')
    if section != 'unknown':
        # Extract module mentions from buffer for section tracking
        mod_mentions = [w for w in re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+(?:_[a-zA-Z0-9_]+)+', buffer.lower())]
        hour_utc = datetime.now(timezone.utc).hour
        update_section(
            profile, section, buffer, completion, outcome,
            modules_mentioned=mod_mentions,
            hour_utc=hour_utc,
        )
    # Run the deduction engine — discover new secrets every cycle
    _deduce_intelligence(profile)

    save_profile(profile)


def update_profile_from_composition(comp: dict):
    """Update profile from a raw composition event (from chat_compositions.jsonl).

    Normalizes the actual JSONL format (chat_state.signals.wpm, etc.) before
    feeding into the profile shards. Handles both old and new data shapes.
    """
    profile = load_profile()
    s = profile['shards']

    # ── NORMALIZE: chat_compositions.jsonl uses chat_state.signals.wpm,
    # not top-level signals.wpm. Handle both shapes. ──
    chat_state = comp.get('chat_state', {})
    if isinstance(chat_state, dict):
        signals = chat_state.get('signals', comp.get('signals', {}))
        state = chat_state.get('state', comp.get('cognitive_state', 'unknown'))
    else:
        signals = comp.get('signals', {})
        state = comp.get('cognitive_state', 'unknown')

    # --- rhythm shard ---
    rhythm = s['rhythm']
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

    # ── SECTION + INTELLIGENCE PIPELINE (composition-grade signals) ──
    final_text = comp.get('final_text', '')
    section = classify_section(
        final_text, state=state, del_ratio=comp.get('deletion_ratio', 0),
        wpm=wpm,
    )
    if section != 'unknown' and final_text:
        deleted = comp.get('deleted_words', [])
        del_words = [dw if isinstance(dw, str) else dw.get('word', '') for dw in deleted]
        rewrites = comp.get('rewrite_chains', comp.get('rewrites', []))
        mod_mentions = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+(?:_[a-zA-Z0-9_]+)+', final_text.lower())
        hour_utc = datetime.now(timezone.utc).hour
        update_section(
            profile, section, final_text, '', 'composition',
            state=state, wpm=wpm,
            del_ratio=comp.get('deletion_ratio', 0),
            hesitation=signals.get('hesitation_score', signals.get('hesitation_count', 0)),
            deleted_words=del_words,
            rewrite_chains=rewrites[:3],
            modules_mentioned=mod_mentions,
            session_n=comp.get('session_n', 0),
            hour_utc=hour_utc,
        )
    _deduce_intelligence(profile)

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


# ══════════════════════════════════════════════════════════════════════════════
# INTENT PROFILE GENERATOR — learns new profiles from prompt clusters
# ══════════════════════════════════════════════════════════════════════════════

_INTENT_STOPWORDS = frozenset(
    'the and for with this that from have what when where then than they their '
    'will would could should about been into some also just like more need want '
    'make does dont here were each which still really pretty super actually '
    'kinda right think look looking know going gonna doing done getting much '
    'very even only most many such well back over being said says yeah okay sure '
    'thing things way ways yeah okay want need see try trying you your i me '
    'can cant cannot could should would may might must shall will well '
    'it its a an is are was be to of in on at by up out if or so not no yes '
    'file files module modules code check checking how now got get'.split()
)


def extract_session_triggers(prompts: list[dict], min_count: int = 2) -> list[str]:
    """Extract recurring intent words from a session's prompts.
    
    Returns words that appear in 2+ prompts (configurable), sorted by frequency.
    These become trigger words for the new intent profile.
    """
    word_count: dict[str, int] = {}
    for p in prompts:
        msg = p.get('msg', '').lower()
        # Extract meaningful words
        words = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+', msg))
        for w in words:
            if len(w) > 3 and w not in _INTENT_STOPWORDS:
                word_count[w] = word_count.get(w, 0) + 1
    
    # Filter to words appearing in min_count+ prompts
    triggers = [(w, c) for w, c in word_count.items() if c >= min_count]
    triggers.sort(key=lambda x: -x[1])
    return [w for w, c in triggers[:15]]  # top 15


def extract_session_files(prompts: list[dict]) -> list[str]:
    """Extract files mentioned/touched in a session.
    
    Sources: files_open field, module_refs field, and text mentions.
    """
    files = set()
    for p in prompts:
        for f in p.get('files_open', []):
            if f:
                files.add(Path(f).stem if '/' in f or '\\' in f else f)
        for ref in p.get('module_refs', []):
            if ref:
                files.add(ref.split('_seq')[0] if '_seq' in ref else ref)
        # Also extract tc_* and *_manifest mentions from text
        msg = p.get('msg', '')
        tc_mentions = re.findall(r'tc_\w+', msg.lower())
        files.update(tc_mentions)
        manifest_mentions = re.findall(r'\w*manifest\w*', msg.lower())
        files.update(m for m in manifest_mentions if len(m) > 5)
    return list(files)[:10]


def detect_session_template(prompts: list[dict]) -> str:
    """Detect which template mode fits this session best.
    
    Returns: '/debug', '/build', or '/review'
    """
    intents = [p.get('intent', 'unknown') for p in prompts]
    states = [p.get('cognitive_state', 'unknown') for p in prompts]
    
    debug_signals = sum(1 for i in intents if i in ('debugging', 'fixing'))
    debug_signals += sum(1 for s in states if s in ('frustrated', 'hesitant'))
    
    build_signals = sum(1 for i in intents if i in ('building', 'creating', 'restructuring'))
    build_signals += sum(1 for s in states if s in ('focused', 'restructuring'))
    
    review_signals = sum(1 for i in intents if i in ('testing', 'reviewing', 'exploring'))
    
    scores = {'debug': debug_signals, 'build': build_signals, 'review': review_signals}
    return '/' + max(scores, key=scores.get)


def generate_profile_from_session(prompts: list[dict], 
                                  profile_name: str | None = None) -> dict:
    """Generate an intent profile from a session's prompts.
    
    Call this at end of a session to learn a new profile.
    Returns the generated profile dict AND writes it to TC_MANIFEST.
    """
    if not prompts or len(prompts) < 3:
        return {}
    
    triggers = extract_session_triggers(prompts)
    files = extract_session_files(prompts)
    template = detect_session_template(prompts)
    
    if not triggers:
        return {}
    
    # Auto-generate name from top triggers if not provided
    if not profile_name:
        profile_name = '_'.join(triggers[:3])
    
    # Calculate confidence from session coherence
    # (more prompts with same intent = higher confidence)
    intents = [p.get('intent', 'unknown') for p in prompts]
    from collections import Counter
    intent_dist = Counter(intents)
    dominant_intent = intent_dist.most_common(1)[0] if intent_dist else ('unknown', 0)
    coherence = dominant_intent[1] / len(prompts) if prompts else 0
    confidence = min(0.95, 0.5 + coherence * 0.4)
    
    profile = {
        'trigger': triggers,
        'files': files,
        'template': template,
        'confidence': round(confidence, 2),
        'source_prompts': len(prompts),
    }
    
    # Write to TC_MANIFEST
    try:
        from .tc_manifest import update_intent_profile
        update_intent_profile(
            name=profile_name,
            trigger=triggers,
            files=files,
            template=template,
            confidence=confidence,
            hit=True
        )
    except Exception:
        pass  # manifest might not exist yet
    
    return profile


def generate_profile_from_journal(n_prompts: int = 20) -> dict | None:
    """Generate a profile from the last N prompts in the journal.
    
    Convenience function for end-of-session profile generation.
    """
    journal = ROOT / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return None
    
    prompts = []
    for line in journal.read_text('utf-8', errors='ignore').strip().splitlines()[-n_prompts:]:
        try:
            prompts.append(json.loads(line))
        except Exception:
            continue
    
    if not prompts:
        return None
    
    return generate_profile_from_session(prompts)
