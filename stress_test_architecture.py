"""Architecture stress test — resynthesizes intent from last 20 prompts,
runs 4 file sims per reconstructed intent, checks stale data, encoding,
and file self-awareness.

Usage:  py stress_test_architecture.py
"""
from __future__ import annotations
import json
import re
import sys
import time
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── ANSI colors ──────────────────────────────────────────────────────────────
G = '\033[92m'; R = '\033[91m'; Y = '\033[93m'; C = '\033[96m'; W = '\033[0m'

def _ts():
    return datetime.now(timezone.utc).strftime('%H:%M:%S')

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: STALE DATA AUDIT
# ═══════════════════════════════════════════════════════════════════════════════
def audit_stale_files() -> list[dict]:
    """Check all data files for staleness, existence, and encoding."""
    checks = [
        ('logs/tc_intent_reinjection.json', 300, 'sim reinjection'),
        ('logs/tc_sim_results.jsonl', 3600, 'sim results log'),
        ('logs/prompt_telemetry_latest.json', 7200, 'prompt telemetry'),
        ('logs/unsaid_reconstructions.jsonl', 3600, 'unsaid threads'),
        ('logs/completion_grades.jsonl', 14400, 'completion grades'),
        ('logs/entropy_map.json', 86400, 'entropy map'),
        ('file_heat_map.json', 7200, 'file heat map'),
        ('file_profiles.json', 7200, 'file profiles'),
        ('pigeon_registry.json', 14400, 'pigeon registry'),
        ('logs/chat_compositions.jsonl', 3600, 'chat compositions'),
        ('logs/prompt_journal.jsonl', 3600, 'prompt journal'),
        ('logs/operator_profile_tc.json', 14400, 'operator profile'),
        ('logs/thought_completions.jsonl', 3600, 'thought completions'),
    ]
    results = []
    now = time.time()
    for path, max_age_s, label in checks:
        p = ROOT / path
        r = {'file': path, 'label': label, 'max_age_s': max_age_s}
        if not p.exists():
            r['status'] = 'MISSING'
            r['severity'] = 'warn' if 'sim' in path else 'error'
        else:
            age_s = now - p.stat().st_mtime
            size = p.stat().st_size
            r['age_s'] = round(age_s)
            r['age_h'] = round(age_s / 3600, 1)
            r['size'] = size
            text = ''
            # Encoding check
            try:
                raw = p.read_bytes()
                text = raw.decode('utf-8')
                r['encoding'] = 'utf-8'
                r['has_bom'] = raw[:3] == b'\xef\xbb\xbf'
                # Check for null bytes (binary corruption)
                if b'\x00' in raw[:1000]:
                    r['encoding_issue'] = 'null_bytes_detected'
            except UnicodeDecodeError:
                r['encoding'] = 'BROKEN'
                r['encoding_issue'] = 'utf-8 decode failed'
            # Staleness
            if age_s > max_age_s:
                r['status'] = 'STALE'
                r['severity'] = 'warn'
            else:
                r['status'] = 'OK'
                r['severity'] = 'ok'
            # JSONL integrity — check last 3 lines parse
            if path.endswith('.jsonl') and size > 0:
                try:
                    lines = text.strip().splitlines()
                    bad = 0
                    for line in lines[-3:]:
                        try:
                            json.loads(line)
                        except Exception:
                            bad += 1
                    r['jsonl_tail_ok'] = bad == 0
                    r['jsonl_total_lines'] = len(lines)
                except Exception:
                    r['jsonl_tail_ok'] = False
        results.append(r)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: INTENT RESYNTHESIS FROM LAST 20 PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════
def _decode_triple_chars(text: str) -> str:
    """Decode triple-character encoding from keystroke capture.
    e.g. 'iiiwwwaaannnttt' -> 'iwant' -> 'i want' (roughly)
    """
    if not text:
        return text
    try:
        from src.intent_numeric_seq001_v003_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade import normalize_prompt_text
        return normalize_prompt_text(text)
    except Exception:
        return text


def resynthesize_intents() -> list[dict]:
    """Read last 20 prompts, decode triple-char, extract intent."""
    journal = ROOT / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return []
    lines = journal.read_text('utf-8', errors='ignore').strip().splitlines()
    last20 = lines[-20:]
    intents = []
    for line in last20:
        try:
            e = json.loads(line)
        except Exception:
            continue
        raw_msg = e.get('msg', '')
        decoded = _decode_triple_chars(raw_msg)
        # Extract meaningful words
        words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]{2,}', decoded)
        # Remove stutters
        real_words = [w for w in words if len(set(w.lower())) > 2]
        intent_slug = e.get('intent', 'unknown')
        cog_state = e.get('cognitive_state', 'unknown')
        ts = e.get('ts', '')

        # Semantic intent reconstruction
        intent_keywords = set()
        for w in real_words:
            wl = w.lower()
            if wl not in {'the', 'and', 'for', 'with', 'this', 'that', 'from',
                          'have', 'what', 'how', 'not', 'are', 'you', 'was',
                          'but', 'can', 'yes', 'nope', 'yeah', 'sure'}:
                intent_keywords.add(wl)

        intents.append({
            'ts': ts,
            'raw_head': raw_msg[:60],
            'decoded_head': decoded[:80],
            'intent': intent_slug,
            'cognitive_state': cog_state,
            'keywords': sorted(intent_keywords)[:10],
            'word_count': len(real_words),
        })
    return intents


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: FILE SELF-AWARENESS AUDIT
# ═══════════════════════════════════════════════════════════════════════════════
def audit_file_awareness() -> dict:
    """Check which files have pitches, profiles, and task awareness."""
    pitches: list[dict] = []
    profiles: list[dict] = []
    missing_awareness: list[str] = []

    # Module pitches
    pitches_dir = ROOT / 'logs' / 'module_pitches'
    if pitches_dir.exists():
        for f in pitches_dir.iterdir():
            try:
                d = json.loads(f.read_text('utf-8', errors='ignore'))
                if isinstance(d, list):
                    d = d[0]
                pitches.append({
                    'module': d.get('module', '?'),
                    'score': d.get('score', {}).get('overall', 0),
                    'code_path': d.get('code_path', '?'),
                    'has_contract': 'contract' in d.get('pitch', '').lower(),
                    'has_warning': d.get('score', {}).get('has_warning', False),
                })
            except Exception:
                pass

    # File profiles
    fp_path = ROOT / 'file_profiles.json'
    if fp_path.exists():
        try:
            fp = json.loads(fp_path.read_text('utf-8', errors='ignore'))
            for name, p in fp.items():
                profiles.append({
                    'name': name,
                    'personality': p.get('personality', '?'),
                    'fears': p.get('fears', []),
                    'avg_hes': p.get('avg_hes', 0),
                    'version': p.get('version', 0),
                })
        except Exception:
            pass

    # Check which src modules lack pitches
    src_modules = set()
    for f in (ROOT / 'src').glob('*.py'):
        if f.name.startswith('__'):
            continue
        # Extract module base name
        m = re.match(r'([a-z_]+)', f.stem)
        if m:
            src_modules.add(m.group(1))
    pitched = {p['module'] for p in pitches}
    missing_awareness = sorted(src_modules - pitched)
    return {
        'pitches': pitches,
        'profiles': profiles,
        'missing_awareness': missing_awareness,
        'awareness_coverage': (
        f"{len(pitched)}/{len(src_modules)}"
        f" ({100 * len(pitched) / max(1, len(src_modules)):.0f}%)"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: 4-FILE SIM ON RECONSTRUCTED INTENTS
# ═══════════════════════════════════════════════════════════════════════════════
def _load_context_minimal() -> dict:
    """Load minimal context without importing src (avoids circular deps)."""
    ctx = {}
    # Recent prompts
    journal = ROOT / 'logs' / 'prompt_journal.jsonl'
    if journal.exists():
        try:
            lines = journal.read_text('utf-8', errors='ignore').strip().splitlines()
            ctx['recent_prompts'] = []
            for line in lines[-5:]:
                e = json.loads(line)
                ctx['recent_prompts'].append({
                    'msg': e.get('msg', '')[:300],
                    'intent': e.get('intent', ''),
                })
        except Exception:
            pass

    # Deleted words from compositions
    cc = ROOT / 'logs' / 'chat_compositions.jsonl'
    if cc.exists():
        try:
            lines = cc.read_text('utf-8', errors='ignore').strip().splitlines()
            all_deleted = []
            for line in lines[-10:]:
                e = json.loads(line)
                dw = e.get('deleted_words', [])
                for d in dw:
                    w = d.get('word', d) if isinstance(d, dict) else str(d)
                    if isinstance(w, str) and len(w) >= 4 and len(set(w.lower())) > 2:
                        all_deleted.append(w[:30])
            ctx['deleted_words_recent'] = all_deleted[-15:]
        except Exception:
            pass

    # Cognitive state
    ctx['cognitive_state'] = 'stress_test'

    # Hot modules from heat map
    hm_path = ROOT / 'file_heat_map.json'
    if hm_path.exists():
        try:
            hm = json.loads(hm_path.read_text('utf-8', errors='ignore'))
            hot = sorted(hm.items(), key=lambda x: x[1].get('heat', 0), reverse=True)
            ctx['hot_modules'] = [k for k, v in hot[:5]]
        except Exception:
            pass

    # Sim reinjection
    sri = ROOT / 'logs' / 'tc_intent_reinjection.json'
    if sri.exists():
        try:
            d = json.loads(sri.read_text('utf-8', errors='ignore'))
            ctx['sim_reinjection'] = d
        except Exception:
            pass

    return ctx


def _select_files_for_intent(keywords: list[str], ctx: dict) -> list[dict]:
    """Select files by semantic similarity to intent keywords."""
    reg_path = ROOT / 'pigeon_registry.json'
    if not reg_path.exists():
        return []
    try:
        reg = json.loads(reg_path.read_text('utf-8', errors='ignore'))
        files = reg.get('files', [])
    except Exception:
        return []

    kw_set = set(k.lower() for k in keywords)
    scored = []
    for f in files:
        name = f.get('name', '').lower()
        path = f.get('path', '').lower()
        # Semantic similarity: keyword overlap with file name/path
        name_words = set(re.findall(r'[a-z_]{3,}', name + ' ' + path))
        overlap = len(kw_set & name_words)
        # Boost hot modules
        is_hot = name in [h.lower() for h in ctx.get('hot_modules', [])]
        score = overlap * 2 + (3 if is_hot else 0)
        if score > 0:
            scored.append((score, f))

    scored.sort(key=lambda x: x[0], reverse=True)
    # If no semantic match, fall back to hot modules
    if not scored:
        for f in files[:4]:
            scored.append((0, f))
    return [s[1] for s in scored[:4]]


def _build_sim_prompt(intent: dict, files: list[dict], sim_config: dict, ctx: dict) -> str:
    """Build a prompt for one sim variant."""
    kw_str = ', '.join(intent['keywords'][:8])
    files_block = ''
    for f in files:
        name = f.get('name', '?')
        path = f.get('path', '?')
        tokens = f.get('tokens', 0)
        # Try to load a snippet of the actual file
        snippet_text = ''
        full_path = ROOT / path if path != '?' else None
        if full_path and full_path.exists():
            try:
                raw = full_path.read_text('utf-8', errors='ignore')
                # Get docstring + first function
                lines = raw.splitlines()[:30]
                snippet_text = '\n'.join(lines)[:400]
            except Exception:
                pass
        files_block += f"\nFILE: {name} ({tokens}t) @ {path}\n{snippet_text}\n"

    deleted_block = ''
    if sim_config.get('use_deleted') and ctx.get('deleted_words_recent'):
        words = ctx['deleted_words_recent'][-5:]
        deleted_block = f"\nSUPPRESSED THOUGHTS: {', '.join(words)}"

    return (
        f"STRESS TEST SIM: {sim_config['name']}\n"
        f"RECONSTRUCTED INTENT: {intent['decoded_head']}\n"
        f"KEYWORDS: {kw_str}\n"
        f"COGNITIVE STATE: {intent['cognitive_state']}\n"
        f"ORIGINAL INTENT CLASS: {intent['intent']}"
        f"{deleted_block}\n\n"
        f"CONTEXT FILES:{files_block}\n\n"
        f"Continue this operator's thought. What are they trying to do? "
        f"Produce a concrete next action or completion."
    )


# 4 sim configs — extending the standard 3 + 1 for "archaeology" (old intent)
_STRESS_SIM_CONFIGS = [
    {'name': 'grounded', 'temp': 0.3, 'use_deleted': False},
    {'name': 'adjacent', 'temp': 0.6, 'use_deleted': False},
    {'name': 'divergent', 'temp': 0.9, 'use_deleted': True},
    {'name': 'archaeology', 'temp': 0.5, 'use_deleted': True},  # old reconstructed intent
]


def _call_gemini_stress(prompt: str, temperature: float) -> str:
    """Call Gemini for stress test sim."""
    import urllib.request
    import os
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        # Try loading from .env or key file
        key_file = ROOT / '.gemini_key'
        if key_file.exists():
            api_key = key_file.read_text().strip()
        if not api_key:
            env_file = ROOT / '.env'
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
    if not api_key:
        return '[NO_API_KEY]'
    model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    url = (f'https://generativelanguage.googleapis.com/v1beta/models/{model}'
           f':generateContent?key={api_key}')
    body = json.dumps({
        'system_instruction': {'parts': [{'text':
            'You are a thought completion engine stress tester. Given reconstructed '
            'operator intent and code context, produce what the operator was trying to '
            'say or do. Be specific — name files, functions, concrete actions. '
            'Max 3 sentences.'
        }]},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': temperature,
            'maxOutputTokens': 200,
            'topP': 0.95,
            'thinkingConfig': {'thinkingBudget': 0},
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = (data.get('candidates', [{}])[0]
                     .get('content', {}).get('parts', []))
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    return part['text'].strip()
            return parts[-1].get('text', '').strip() if parts else ''
    except Exception as e:
        return f'[ERROR: {e}]'


def _score_sim_result(completion: str, intent: dict) -> float:
    """Score how well a sim result matches reconstructed intent."""
    if not completion or completion.startswith('['):
        return 0.0
    comp_words = set(re.findall(r'[a-z_]{3,}', completion.lower()))
    kw_set = set(intent['keywords'])
    if not comp_words:
        return 0.0
    # Keyword overlap
    overlap = len(comp_words & kw_set)
    kw_score = min(1.0, overlap / max(1, len(kw_set))) if kw_set else 0.5
    # Specificity — module/function names
    spec = min(1.0, (completion.count('_') + completion.count('.') + completion.count('(')) / 6)
    # Length utility
    length = len(completion)
    len_score = 1.0 if 30 <= length <= 200 else max(0.2, 1.0 - abs(length - 100) / 200)
    return round(0.4 * kw_score + 0.3 * spec + 0.3 * len_score, 3)


def run_4_sims(intents: list[dict], ctx: dict, max_intents: int = 5) -> list[dict]:
    """Run 4 file sims on up to max_intents reconstructed intents."""
    # Pick the most interesting intents (most keywords, not duplicates)
    scored_intents = sorted(intents, key=lambda i: len(i['keywords']), reverse=True)
    # Deduplicate by keyword set
    seen = set()
    unique = []
    for intent in scored_intents:
        key = tuple(intent['keywords'][:5])
        if key not in seen and intent['keywords']:
            seen.add(key)
            unique.append(intent)
    targets = unique[:max_intents]

    all_results = []
    for intent in targets:
        files = _select_files_for_intent(intent['keywords'], ctx)
        file_names = [f.get('name', '?') for f in files]

        sim_results = []
        lock = threading.Lock()

        def _run_one(cfg):
            prompt = _build_sim_prompt(intent, files, cfg, ctx)
            completion = _call_gemini_stress(prompt, cfg['temp'])
            score = _score_sim_result(completion, intent)
            with lock:
                sim_results.append({
                    'sim': cfg['name'],
                    'temp': cfg['temp'],
                    'completion': completion[:300],
                    'score': score,
                })

        threads = [threading.Thread(target=_run_one, args=(cfg,), daemon=True)
                   for cfg in _STRESS_SIM_CONFIGS]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=20)

        winner = max(sim_results, key=lambda r: r['score']) if sim_results else None
        all_results.append({
            'intent_ts': intent['ts'],
            'keywords': intent['keywords'],
            'decoded': intent['decoded_head'][:60],
            'files_selected': file_names,
            'sims': sim_results,
            'winner': winner['sim'] if winner else None,
            'winner_score': winner['score'] if winner else 0,
            'winner_completion': winner['completion'][:150] if winner else '',
        })

    return all_results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: INTENT CLEARING AUDIT
# ═══════════════════════════════════════════════════════════════════════════════
def audit_intent_clearing(intents: list[dict]) -> dict:
    """Check which intents got resolved vs still pending."""
    resolved = []
    pending = []
    for i in intents:
        if i['intent'] != 'unknown' and i['keywords']:
            resolved.append(i)
        else:
            pending.append(i)
    return {
        'total': len(intents),
        'resolved': len(resolved),
        'pending': len(pending),
        'resolution_rate': f"{100 * len(resolved) / max(1, len(intents)):.0f}%",
        'pending_keywords': [p['keywords'][:3] for p in pending if p['keywords']][:5],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — RUN ALL PHASES
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n{C}{'='*70}")
    print(f"ARCHITECTURE STRESS TEST — {_ts()}")
    print(f"{'='*70}{W}\n")

    # ── Phase 1: Stale data ──
    print(f"{Y}[PHASE 1] Stale Data + Encoding Audit{W}")
    stale = audit_stale_files()
    for r in stale:
        status = r['status']
        color = G if status == 'OK' else (Y if status == 'STALE' else R)
        age = f"age={r.get('age_h', '?')}h" if 'age_h' in r else ''
        size = f"size={r.get('size', 0):,}" if 'size' in r else ''
        enc = r.get('encoding', '')
        enc_issue = r.get('encoding_issue', '')
        jsonl_ok = r.get('jsonl_tail_ok', '')
        extra = ''
        if enc_issue:
            extra += f" {R}ENCODING:{enc_issue}{W}"
        if jsonl_ok is False:
            extra += f" {R}JSONL_CORRUPT{W}"
        print(f"  {color}[{status:7s}]{W} {r['label']:25s} {age:12s} {size:15s}{extra}")
    print()

    # ── Phase 2: Intent resynthesis ──
    print(f"{Y}[PHASE 2] Intent Resynthesis (last 20 prompts){W}")
    intents = resynthesize_intents()
    for i, intent in enumerate(intents):
        kw = ', '.join(intent['keywords'][:5])
        cog = intent['cognitive_state']
        cls = intent['intent']
        ts_short = intent['ts'][11:19] if len(intent['ts']) > 19 else intent['ts']
        decoded = intent['decoded_head'][:50]
        color = G if cls != 'unknown' else Y
        print(f"  {color}[{i:2d}]{W} {ts_short} cog={cog:12s} cls={cls:12s} kw=[{kw}]")
        print(f"       decoded: {decoded}")
    print()

    # ── Phase 3: File awareness ──
    print(f"{Y}[PHASE 3] File Self-Awareness Audit{W}")
    aware = audit_file_awareness()
    print(f"  Coverage: {aware['awareness_coverage']}")
    for p in aware['pitches']:
        color = G if p['score'] >= 0.5 else Y
        print(f"  {color}[pitch]{W} {p['module']:30s} score={p['score']:.2f} "
              f"contract={'Y' if p['has_contract'] else 'N'} "
              f"warning={'Y' if p['has_warning'] else 'N'}")
    if aware['missing_awareness']:
        print(f"  {R}Missing awareness:{W} {', '.join(aware['missing_awareness'][:10])}")
        if len(aware['missing_awareness']) > 10:
            print(f"    ...and {len(aware['missing_awareness']) - 10} more")
    print()

    # ── Phase 4: Intent clearing ──
    print(f"{Y}[PHASE 4] Intent Board Clearing{W}")
    clearing = audit_intent_clearing(intents)
    color = G if clearing['resolution_rate'].rstrip('%').isdigit() and int(clearing['resolution_rate'].rstrip('%')) >= 50 else Y
    print(f"  {color}Resolution rate:{W} {clearing['resolution_rate']} "
          f"({clearing['resolved']}/{clearing['total']})")
    if clearing['pending_keywords']:
        print(f"  {Y}Pending intents:{W}")
        for kw in clearing['pending_keywords']:
            print(f"    - {kw}")
    print()

    # ── Phase 5: 4-file sims ──
    print(f"{Y}[PHASE 5] 4-File Sims on Reconstructed Intent{W}")
    ctx = _load_context_minimal()
    sim_results = run_4_sims(intents, ctx, max_intents=5)
    for sr in sim_results:
        print(f"\n  {C}Intent:{W} {sr['decoded']}")
        print(f"  Keywords: {sr['keywords'][:5]}")
        print(f"  Files: {sr['files_selected']}")
        for sim in sr['sims']:
            color = G if sim['score'] >= 0.4 else (Y if sim['score'] >= 0.2 else R)
            marker = ' ★' if sim['sim'] == sr['winner'] else ''
            print(f"    {color}[{sim['sim']:12s}]{W} score={sim['score']:.2f} "
                  f"temp={sim['temp']}{marker}")
            # Show first 100 chars of completion
            comp = sim['completion'][:100].replace('\n', ' ')
            print(f"      → {comp}")
    print()

    # ── Summary ──
    total_sims = sum(len(sr['sims']) for sr in sim_results)
    avg_score = (sum(s['score'] for sr in sim_results for s in sr['sims']) /
                 max(1, total_sims))
    stale_count = sum(1 for r in stale if r['status'] in ('STALE', 'MISSING'))
    missing_awareness = len(aware.get('missing_awareness', []))

    print(f"{C}{'='*70}")
    print(f"STRESS TEST SUMMARY")
    print(f"{'='*70}{W}")
    print(f"  Stale/missing files:    {stale_count}/{len(stale)}")
    print(f"  Intent resolution:      {clearing['resolution_rate']}")
    print(f"  File awareness:         {aware['awareness_coverage']}")
    print(f"  Sims run:               {total_sims}")
    print(f"  Avg sim score:          {avg_score:.3f}")
    print(f"  Winner distribution:    ", end='')
    winner_counts = {}
    for sr in sim_results:
        w = sr.get('winner', '?')
        winner_counts[w] = winner_counts.get(w, 0) + 1
    print(' | '.join(f"{k}:{v}" for k, v in winner_counts.items()))

    # Write results to file
    output = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'stale_audit': stale,
        'intents': intents,
        'file_awareness': aware,
        'intent_clearing': clearing,
        'sim_results': sim_results,
        'summary': {
            'stale_count': stale_count,
            'intent_resolution': clearing['resolution_rate'],
            'awareness_coverage': aware['awareness_coverage'],
            'total_sims': total_sims,
            'avg_sim_score': avg_score,
            'winner_distribution': winner_counts,
        },
    }
    out_path = ROOT / 'logs' / 'stress_test_architecture_results.json'
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n  Results saved to: {out_path.relative_to(ROOT)}")
    print()


if __name__ == '__main__':
    main()
