"""dynamic_prompt_seq017_profile_analysis_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import json, re, subprocess

def _profile_history(root):
    p = root / 'operator_profile.md'
    if not p.exists(): return []
    m = re.search(r'<!--\s*\n?DATA\s*\n(.*?)\nDATA\s*\n-->',
                  p.read_text(encoding='utf-8', errors='ignore'), re.DOTALL)
    if not m: return []
    try: return json.loads(m.group(1).strip()).get('history', [])
    except Exception: return []


def _unsaid(comps, root=None):
    """Extract unsaid threads: raw deleted words + thought completions."""
    threads = []
    for c in comps[-8:]:
        for w in (c.get('deleted_words') or []):
            word = w.get('word', w) if isinstance(w, dict) else str(w)
            if word and len(word) > 3: threads.append(word)
    raw = threads[-6:]

    # Load thought completions from unsaid_reconstructions.jsonl
    completions = []
    if root:
        recon_path = root / 'logs' / 'unsaid_reconstructions.jsonl'
        if recon_path.exists():
            try:
                lines = recon_path.read_text('utf-8', errors='replace').strip().splitlines()
                for line in lines[-5:]:
                    try:
                        r = json.loads(line)
                        tc = r.get('thought_completion', '')
                        if tc and tc.lower() not in ('typo correction only', ''):
                            completions.append(tc)
                    except json.JSONDecodeError:
                        pass
            except OSError:
                pass

    return {'raw': raw, 'completions': completions[-3:]}
