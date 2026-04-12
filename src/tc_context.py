"""Context loading — gathers live telemetry for thought completion prompts."""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

from .tc_constants import ROOT

_ctx_cache: dict | None = None
_ctx_ts: float = 0


def load_context(repo_root: Path | None = None) -> dict:
    """Load all context sources with 120s caching."""
    global _ctx_cache, _ctx_ts
    now = time.time()
    if _ctx_cache is not None and (now - _ctx_ts) < 120:
        return _ctx_cache

    r = repo_root or ROOT
    ctx: dict = {}

    # Recent prompts from journal
    journal = r / 'logs' / 'prompt_journal.jsonl'
    if journal.exists():
        try:
            lines = journal.read_text('utf-8', errors='ignore').strip().splitlines()
            ctx['recent_prompts'] = []
            for line in lines[-5:]:
                entry = json.loads(line)
                ctx['recent_prompts'].append({
                    'msg': entry.get('msg', '')[:300],
                    'intent': entry.get('intent', ''),
                })
        except Exception:
            pass

    # Prompt telemetry — hot modules + operator state
    telem = r / 'logs' / 'prompt_telemetry_latest.json'
    if telem.exists():
        try:
            t = json.loads(telem.read_text('utf-8', errors='ignore'))
            ctx['hot_modules'] = t.get('hot_modules', [])[:5]
            rs = t.get('running_summary', {})
            ctx['operator_state'] = {
                'dominant': rs.get('dominant_state', 'unknown'),
                'states': rs.get('state_distribution', {}),
                'avg_wpm': rs.get('avg_wpm'),
                'baselines': rs.get('baselines', {}),
            }
        except Exception:
            pass

    # Unsaid threads — deleted thoughts
    unsaid = r / 'logs' / 'unsaid_reconstructions.jsonl'
    if unsaid.exists():
        try:
            lines = unsaid.read_text('utf-8', errors='ignore').strip().splitlines()
            ctx['unsaid_threads'] = []
            for line in lines[-5:]:
                entry = json.loads(line)
                ctx['unsaid_threads'].append(
                    entry.get('reconstructed', entry.get('deleted', ''))[:200])
        except Exception:
            pass

    # Entropy map
    emap = r / 'logs' / 'entropy_map.json'
    if emap.exists():
        try:
            em = json.loads(emap.read_text('utf-8', errors='ignore'))
            ctx['entropy'] = {
                'global': em.get('global_avg_entropy', 0),
                'high_pct': em.get('high_entropy_pct', 0),
                'hotspots': [
                    {'mod': m['module'], 'H': round(m['avg_entropy'], 3)}
                    for m in em.get('top_entropy_modules', [])[:6]
                ],
            }
        except Exception:
            pass

    # File heat map — Copilot edit frequency + entropy
    fhm = r / 'file_heat_map.json'
    if fhm.exists():
        try:
            hm = json.loads(fhm.read_text('utf-8', errors='ignore'))
            heat = []
            for mod, data in hm.items():
                h = data.get('heat', 0)
                if h > 0:
                    heat.append({'mod': mod, 'heat': round(h, 3),
                                 'touches': data.get('touch_score', 0),
                                 'entropy': data.get('entropy', 0),
                                 'n': round(data.get('touch_score', 0))})
            heat.sort(key=lambda x: x['heat'], reverse=True)
            ctx['heat_map'] = heat[:8]
        except Exception:
            pass

    # Codebase topology from registry
    reg = r / 'pigeon_registry.json'
    if reg.exists():
        try:
            rj = json.loads(reg.read_text('utf-8', errors='ignore'))
            modules = []
            for f in rj.get('files', []):
                modules.append(f"{f.get('name', '?')}({f.get('tokens', 0)}t)")
            ctx['codebase_map'] = {
                'total_modules': rj.get('total', 0),
                'modules': ' '.join(modules[:60]),
            }
        except Exception:
            pass

    # Bug voices
    bp = r / 'docs' / 'BUG_PROFILES.md'
    if bp.exists():
        try:
            text = bp.read_text('utf-8', errors='ignore')
            demons = re.findall(r'\*Demon name: (.+?)\*', text)
            hosts = re.findall(r'### (\S+)\n', text)
            ctx['bug_demons'] = [
                {'host': h, 'demon': d}
                for h, d in zip(hosts, demons)
            ][:8]
        except Exception:
            pass

    # Self-fix known issues
    sf = r / 'logs' / 'self_fix_report.md'
    if sf.exists():
        try:
            text = sf.read_text('utf-8', errors='ignore')
            crits = re.findall(r'\[CRITICAL\]\s+(\w+)\s+in\s+`([^`]+)`', text)
            ctx['critical_bugs'] = [{'type': t, 'file': f} for t, f in crits[:6]]
        except Exception:
            pass

    # Session context — recent copilot chat messages for topic awareness
    cc = r / 'logs' / 'chat_compositions.jsonl'
    if cc.exists():
        try:
            lines = cc.read_text('utf-8', errors='ignore').strip().splitlines()
            ctx['session_messages'] = []
            for line in lines[-5:]:
                entry = json.loads(line)
                text_snip = entry.get('final_text', '')[:80]
                cs = entry.get('chat_state', {})
                state = cs.get('state', 'unknown') if isinstance(cs, dict) else 'unknown'
                deleted = entry.get('deleted_words', [])
                rewrites = entry.get('rewrite_chains', [])
                ctx['session_messages'].append({
                    'text': text_snip,
                    'state': state,
                    'del_ratio': entry.get('deletion_ratio', 0),
                    'deleted_words': deleted[-6:] if deleted else [],
                    'rewrites': [r[:80] if isinstance(r, str) else r for r in (rewrites[-3:] if rewrites else [])],
                })
        except Exception:
            pass

    # Session identity from prompt journal
    pj = r / 'logs' / 'prompt_journal.jsonl'
    if pj.exists():
        try:
            lines = pj.read_text('utf-8', errors='ignore').strip().splitlines()
            last = json.loads(lines[-1]) if lines else {}
            ctx['session_info'] = {
                'session_id': last.get('session_id', '')[:8],
                'session_n': last.get('session_n', 0),
                'intent': last.get('intent', ''),
                'cognitive_state': last.get('cognitive_state', ''),
            }
        except Exception:
            pass

    # File profiles — fears, hesitation, personality per module
    fprof = r / 'file_profiles.json'
    if fprof.exists():
        try:
            profiles = json.loads(fprof.read_text('utf-8', errors='ignore'))
            # Only include modules with interesting signals (fears or high hesitation)
            interesting = []
            for name, p in profiles.items():
                fears = p.get('fears', [])
                hes = p.get('avg_hes', 0)
                if fears or hes > 0.5:
                    interesting.append({
                        'mod': name,
                        'personality': p.get('personality', '?'),
                        'fears': fears[:3],
                        'hes': round(hes, 2),
                        'v': p.get('version', 0),
                    })
            interesting.sort(key=lambda x: x['hes'], reverse=True)
            ctx['file_profiles'] = interesting[:10]
        except Exception:
            pass

    # Interrogation answers — operator decisions from interrogation room
    ia = r / 'logs' / 'interrogation_answers.jsonl'
    if ia.exists():
        try:
            lines = ia.read_text('utf-8', errors='ignore').strip().splitlines()
            ctx['interrogation_answers'] = []
            for line in lines[-10:]:
                entry = json.loads(line)
                ctx['interrogation_answers'].append({
                    'module': entry.get('module', ''),
                    'answer': entry.get('answer', '')[:200],
                })
        except Exception:
            pass

    # Organism narrative — copilot's own consciousness statement
    ci_path = r / '.github' / 'copilot-instructions.md'
    if ci_path.exists():
        try:
            ci_text = ci_path.read_text('utf-8', errors='ignore')
            # Extract narrative glove (1-line organism consciousness)
            m = re.search(r'> (the organism .+?)$', ci_text, re.MULTILINE)
            if m:
                ctx['organism_narrative'] = m.group(1)[:300]
            # Extract current copilot query
            m2 = re.search(r'INTERPRETED INTENT: (.+?)$', ci_text, re.MULTILINE)
            if m2:
                ctx['copilot_intent'] = m2.group(1)[:200]
        except Exception:
            pass

    _ctx_cache = ctx
    _ctx_ts = now
    return ctx


def invalidate_context_cache():
    """Force context reload on next call."""
    global _ctx_cache, _ctx_ts
    _ctx_cache = None
    _ctx_ts = 0
