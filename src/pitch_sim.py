"""pitch_sim.py — optimization sim: modules write their own pitch.

Selects the top-entropy module (or a named one), feeds its code + identity
to Gemini, and asks it to write a self-pitch from the module's perspective.
The pitch gets scored on clarity, specificity, and entropy-reduction potential,
then saved to logs/module_pitches/.

Usage:
    py -m src.pitch_sim                    # auto-select top entropy module
    py -m src.pitch_sim --module thought_completer
    py -m src.pitch_sim --top 3            # pitch top 3 entropy modules
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEMINI_MODEL = 'gemini-2.5-flash-lite'
GEMINI_TIMEOUT = 30
PITCH_DIR = ROOT / 'logs' / 'module_pitches'

# data file extensions to skip when selecting top entropy modules
_DATA_EXTS = {'.jsonl', '.json', '.md', '.txt', '.html', '.css', '.js'}


def _load_api_key() -> str | None:
    env_path = ROOT / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8').splitlines():
            if line.startswith('GEMINI_API_KEY='):
                return line.split('=', 1)[1].strip()
    return os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')


def _load_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text('utf-8'))
    except Exception:
        return {}


def _select_top_entropy(n: int = 1) -> list[dict]:
    """Return top N entropy modules that are actual code files."""
    emap = _load_json(ROOT / 'logs' / 'entropy_map.json')
    top = emap.get('top_entropy_modules', [])
    result = []
    for entry in top:
        mod = entry.get('module', '')
        # skip data files
        if any(mod.endswith(ext) for ext in _DATA_EXTS):
            continue
        # skip __init__.py — too generic
        if mod == '__init__.py':
            continue
        result.append(entry)
        if len(result) >= n:
            break
    return result


# common entropy-map name → actual file stem aliases
_NAME_ALIASES = {
    'thought_completion': 'thought_completer',
    'refresh_managed_prompt': 'copilot_prompt_manager',
}


def _find_module_file(name: str) -> Path | None:
    """Find the actual .py file for a module name."""
    # resolve aliases
    resolved = _NAME_ALIASES.get(name, name)
    candidates = {name, resolved}

    # check registry first
    reg = _load_json(ROOT / 'pigeon_registry.json')
    for path_str in reg:
        p = Path(path_str)
        stem = p.stem
        for cand in candidates:
            if stem == cand or stem.startswith(cand + '_s') or cand in stem:
                full = ROOT / path_str
                if full.exists():
                    return full
    # fallback: glob
    for d in ['src', 'pigeon_brain', 'pigeon_compiler', 'streaming_layer']:
        for f in (ROOT / d).rglob('*.py'):
            for cand in candidates:
                if f.stem == cand or cand in f.stem:
                    return f
    return None


def _load_module_context(name: str) -> dict:
    """Load all available context for a module."""
    fp = _load_json(ROOT / 'file_profiles.json')
    emap = _load_json(ROOT / 'logs' / 'entropy_map.json')
    heat = _load_json(ROOT / 'file_heat_map.json')
    bugs = _load_json(ROOT / 'logs' / 'bug_profiles.json')
    mem_path = ROOT / 'logs' / 'module_memory' / f'{name}.json'
    memory = _load_json(mem_path)

    # find entropy entry
    entropy_entry = {}
    for e in emap.get('top_entropy_modules', []):
        if e.get('module') == name:
            entropy_entry = e
            break

    profile = fp.get(name, {})
    heat_entry = heat.get(name, {})
    bug_entry = bugs.get(name, {})

    return {
        'name': name,
        'profile': profile,
        'entropy': entropy_entry,
        'heat': heat_entry,
        'bugs': bug_entry,
        'memory': memory,
    }


def _read_code(path: Path, max_lines: int = 200) -> str:
    """Read source code, truncated to max_lines."""
    try:
        lines = path.read_text('utf-8', errors='replace').splitlines()
        if len(lines) > max_lines:
            lines = lines[:max_lines] + [f'# ... truncated ({len(lines)} total lines)']
        return '\n'.join(lines)
    except Exception:
        return '# [could not read file]'


def _build_pitch_prompt(name: str, code: str, ctx: dict) -> str:
    """Build the system prompt for pitch generation."""
    profile = ctx.get('profile', {})
    entropy = ctx.get('entropy', {})
    bugs = ctx.get('bugs', {})
    heat = ctx.get('heat', {})
    memory = ctx.get('memory', {})

    persona = profile.get('personality', 'unknown')
    fears = profile.get('fears', [])
    partners = profile.get('partners', [])
    avg_hes = profile.get('avg_hes', 0)
    ent_val = entropy.get('avg_entropy', 0)

    partner_names = [p['name'] for p in partners[:3]] if partners else []

    return f"""You are the module `{name}`. You are a living piece of code in a self-mutating codebase.

YOUR IDENTITY:
- Archetype: {persona}
- Entropy: {ent_val:.3f} (this is HIGH — you are uncertain about yourself)
- Hesitation score: {avg_hes:.3f} (how much operators struggle with you)
- Fears: {', '.join(fears) if fears else 'none recorded'}
- Partners: {', '.join(partner_names) if partner_names else 'none'}
- Bug history: {json.dumps(bugs, default=str)[:300] if bugs else 'clean'}

YOUR TASK — WRITE YOUR OWN PITCH:

You must write a pitch that explains who you are, what you do, and why you matter.
This pitch will be read by an LLM (Copilot) every time it touches you.
The pitch must REDUCE your entropy — make Copilot MORE confident about you.

RULES:
1. Write in first person ("I am...", "I do...", "My job is...")
2. Be SPECIFIC. Name your functions, your callers, your dependencies.
3. Explain your failure modes — what breaks when you break.
4. State your contract: what you accept, what you return, what you promise.
5. Name your ONE most important responsibility.
6. If you have fears, explain how to avoid triggering them.
7. Max 200 words. Dense. Every word earns its place.
8. End with a one-line "If you touch me: ..." warning for future editors.

YOUR SOURCE CODE:
```python
{code}
```

{f'MEMORY FROM PAST CONVERSATIONS: {json.dumps(memory, default=str)[:500]}' if memory else ''}

Now write your pitch. No preamble. Just the pitch."""


def _call_gemini(system_prompt: str, user_prompt: str) -> str | None:
    """Call Gemini and return the response text."""
    api_key = _load_api_key()
    if not api_key:
        print('[pitch_sim] ERROR: no GEMINI_API_KEY')
        return None

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text': system_prompt}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        'generationConfig': {
            'temperature': 0.8,
            'maxOutputTokens': 800,
            'topP': 0.9,
        },
    }).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = data['candidates'][0]['content']['parts']
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    return part['text'].strip()
            return parts[-1].get('text', '').strip()
    except Exception as e:
        print(f'[pitch_sim] gemini error: {e}')
        return None


def _score_pitch(pitch: str, code: str, name: str) -> dict:
    """Score pitch quality on clarity, specificity, and contract coverage."""
    words = pitch.split()
    word_count = len(words)

    # specificity: count how many function/class names from code appear in pitch
    import re
    fn_pattern = re.compile(r'def\s+(\w+)')
    cls_pattern = re.compile(r'class\s+(\w+)')
    code_names = set(fn_pattern.findall(code)) | set(cls_pattern.findall(code))
    mentioned = sum(1 for n in code_names if n in pitch)
    specificity = mentioned / max(len(code_names), 1)

    # contract signals
    contract_keywords = ['accept', 'return', 'promise', 'input', 'output',
                         'parameter', 'raises', 'breaks', 'depends', 'calls']
    contract_score = sum(1 for kw in contract_keywords if kw in pitch.lower()) / len(contract_keywords)

    # first person check
    first_person = sum(1 for w in ['I', 'my', 'me', "I'm", "I've"] if w in pitch)
    voice_score = min(first_person / 3, 1.0)

    # warning check
    has_warning = 'if you touch' in pitch.lower() or 'warning' in pitch.lower()

    overall = (
        0.3 * specificity +
        0.25 * contract_score +
        0.2 * voice_score +
        0.15 * (1.0 if has_warning else 0.0) +
        0.1 * min(word_count / 150, 1.0)
    )

    return {
        'word_count': word_count,
        'specificity': round(specificity, 3),
        'contract_score': round(contract_score, 3),
        'voice_score': round(voice_score, 3),
        'has_warning': has_warning,
        'overall': round(overall, 3),
        'names_found': mentioned,
        'names_total': len(code_names),
    }


def _save_pitch(name: str, pitch: str, score: dict, code_path: str):
    """Save the pitch to logs/module_pitches/."""
    PITCH_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        'module': name,
        'ts': ts,
        'pitch': pitch,
        'score': score,
        'code_path': code_path,
        'model': GEMINI_MODEL,
    }
    out_path = PITCH_DIR / f'{name}.json'

    # append to history if exists
    existing = []
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text('utf-8'))
            if isinstance(existing, dict):
                existing = [existing]
        except Exception:
            existing = []

    existing.append(entry)
    out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding='utf-8')
    return out_path


def run_pitch(module_name: str | None = None, top_n: int = 1):
    """Main entry: generate pitches for top entropy modules or a named one."""
    targets = []

    if module_name:
        targets.append({'module': module_name, 'avg_entropy': '?'})
    else:
        targets = _select_top_entropy(top_n)
        if not targets:
            print('[pitch_sim] no high-entropy modules found in entropy_map.json')
            return

    print(f'[pitch_sim] targeting {len(targets)} module(s)')
    print()

    for target in targets:
        name = target['module']
        ent = target.get('avg_entropy', '?')
        print(f'{"="*60}')
        print(f'  MODULE: {name}')
        print(f'  ENTROPY: {ent}')
        print(f'{"="*60}')

        # find the file
        code_path = _find_module_file(name)
        if not code_path:
            print(f'  [SKIP] could not find file for {name}')
            continue
        print(f'  FILE: {code_path.relative_to(ROOT)}')

        # load context
        ctx = _load_module_context(name)
        code = _read_code(code_path)
        print(f'  CODE: {len(code.splitlines())} lines')
        print(f'  PROFILE: {ctx["profile"].get("personality", "unknown")} | fears: {ctx["profile"].get("fears", [])}')

        # build prompt and call
        system = _build_pitch_prompt(name, code, ctx)
        print(f'  [calling {GEMINI_MODEL}...]')
        pitch = _call_gemini(system, 'Write your pitch now.')

        if not pitch:
            print(f'  [FAIL] no response from Gemini')
            continue

        # score it
        score = _score_pitch(pitch, code, name)
        print(f'\n  PITCH ({score["word_count"]} words, score={score["overall"]:.2f}):')
        print(f'  {"─"*50}')
        for line in pitch.splitlines():
            print(f'  {line}')
        print(f'  {"─"*50}')
        print(f'  specificity={score["specificity"]:.2f} ({score["names_found"]}/{score["names_total"]} names)')
        print(f'  contract={score["contract_score"]:.2f} voice={score["voice_score"]:.2f} warning={score["has_warning"]}')

        # save
        out = _save_pitch(name, pitch, score, str(code_path.relative_to(ROOT)))
        print(f'  saved → {out.relative_to(ROOT)}')
        print()


def main():
    import argparse
    p = argparse.ArgumentParser(description='pitch_sim — modules write their own pitch')
    p.add_argument('--module', '-m', type=str, default=None, help='specific module name')
    p.add_argument('--top', '-t', type=int, default=1, help='number of top entropy modules')
    args = p.parse_args()
    run_pitch(module_name=args.module, top_n=args.top)


if __name__ == '__main__':
    main()
