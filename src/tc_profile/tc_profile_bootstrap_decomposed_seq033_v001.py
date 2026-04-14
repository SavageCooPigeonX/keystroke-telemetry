"""tc_profile_bootstrap_decomposed_seq033_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 033 | VER: v001 | 180 lines | ~2,099 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from ..tc_constants import ROOT
from collections import Counter
import json
import re

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
