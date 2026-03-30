# ┌────────────────────────────────────────────────────────────┐
# │  voice_style_seq028_v001                                  │
# │  Extracts operator voice style from raw prompt text.      │
# │  Zero LLM calls — pure linguistic signal processing.      │
# │  Injects <!-- pigeon:voice-style --> into copilot-instr.  │
# └────────────────────────────────────────────────────────────┘

# ── telemetry:pulse ──
# EDIT_TS:   2026-03-30T01:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  initial voice style extractor
# EDIT_STATE: harvested
# ── /pulse ──

"""
Voice style personality adapter.

Reads operator prompts from prompt_journal.jsonl, extracts linguistic
features (not telemetry metrics), and generates a style directive block
for copilot-instructions.md.

The operator's VOICE tunes how Copilot responds — not what it does,
but how it talks back.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter


# ── Lexical markers ──────────────────────────────────────────────────────────

_SLANG = {
    'bruh', 'tbh', 'ngl', 'imo', 'asap', 'idk', 'wdt', 'wtf', 'lol',
    'nah', 'yep', 'yea', 'yeah', 'gonna', 'wanna', 'gotta', 'kinda',
    'sorta', 'cuz', 'tho', 'rn', 'btw', 'fyi', 'lmao', 'omg', 'smh',
    'woah', 'whoa', 'ahh', 'ooh', 'hmm', 'huh',
}
_CONTRACTIONS = re.compile(
    r"\b(can't|won't|don't|didn't|isn't|aren't|wasn't|weren't|"
    r"shouldn't|couldn't|wouldn't|haven't|hasn't|hadn't|"
    r"i'm|you're|they're|we're|it's|that's|there's|"
    r"i've|you've|we've|they've|i'll|you'll|we'll|they'll|"
    r"i'd|you'd|we'd|they'd|let's|ain't|y'all)\b", re.I
)
_TECHNICAL = {
    'import', 'module', 'function', 'refactor', 'pipeline', 'endpoint',
    'api', 'schema', 'compiler', 'ast', 'parser', 'debug', 'lint',
    'deploy', 'commit', 'push', 'branch', 'merge', 'rebase', 'hook',
    'callback', 'async', 'await', 'stream', 'buffer', 'socket',
    'telemetry', 'metric', 'signal', 'gradient', 'latency', 'throughput',
}
_SENTENCE_ENDERS = re.compile(r'[.!?]+')
_WORD_RE = re.compile(r'[a-zA-Z]+')


def _load_recent_prompts(root: Path, max_prompts: int = 80) -> list[str]:
    """Load recent operator prompt messages from journal."""
    journal = root / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return []
    try:
        lines = journal.read_bytes().decode('utf-8', errors='replace').strip().split('\n')
        msgs = []
        for line in lines[-max_prompts:]:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                msg = entry.get('msg', '').strip()
                # Skip conversation summaries and empty messages
                if msg and not msg.startswith('<conversation') and len(msg) > 5:
                    msgs.append(msg)
            except json.JSONDecodeError:
                continue
        return msgs
    except OSError:
        return []


def extract_voice_features(prompts: list[str]) -> dict:
    """Extract linguistic style features from a list of raw prompts."""
    if not prompts:
        return {}

    all_words: list[str] = []
    sentence_lengths: list[int] = []
    word_lengths: list[int] = []
    prompt_lengths: list[int] = []
    slang_count = 0
    contraction_count = 0
    technical_count = 0
    question_count = 0
    directive_count = 0
    dash_count = 0
    ellipsis_count = 0
    exclamation_count = 0
    no_caps_count = 0
    fragment_count = 0  # prompts with no sentence-ending punctuation

    for prompt in prompts:
        words = _WORD_RE.findall(prompt.lower())
        all_words.extend(words)
        prompt_lengths.append(len(words))
        word_lengths.extend(len(w) for w in words)

        # Slang
        slang_count += sum(1 for w in words if w in _SLANG)

        # Contractions
        contraction_count += len(_CONTRACTIONS.findall(prompt))

        # Technical jargon
        technical_count += sum(1 for w in words if w in _TECHNICAL)

        # Sentence structure
        sentences = _SENTENCE_ENDERS.split(prompt)
        sentences = [s.strip() for s in sentences if s.strip()]
        for s in sentences:
            sw = _WORD_RE.findall(s)
            if sw:
                sentence_lengths.append(len(sw))

        # Punctuation style
        dash_count += prompt.count(' - ') + prompt.count(' — ')
        ellipsis_count += prompt.count('...')
        exclamation_count += prompt.count('!')

        # Capitalization
        first_char = next((c for c in prompt if c.isalpha()), 'a')
        if first_char.islower():
            no_caps_count += 1

        # Question vs directive
        stripped = prompt.rstrip()
        if stripped.endswith('?') or any(prompt.lower().startswith(q) for q in
                                         ['how ', 'what ', 'why ', 'when ', 'where ',
                                          'is ', 'can ', 'should ', 'could ', 'would ']):
            question_count += 1
        elif any(prompt.lower().startswith(d) for d in
                 ['fix ', 'add ', 'build ', 'make ', 'update ', 'push ', 'test ',
                  'wire ', 'clear ', 'run ', 'write ', 'use ', 'refactor ']):
            directive_count += 1

        # Fragment detection (no period/question/exclamation)
        if not re.search(r'[.!?]', prompt):
            fragment_count += 1

    n = len(prompts)
    unique_words = set(all_words)

    return {
        'prompt_count': n,
        'avg_prompt_words': round(sum(prompt_lengths) / n, 1) if n else 0,
        'avg_word_length': round(sum(word_lengths) / len(word_lengths), 1) if word_lengths else 0,
        'avg_sentence_words': round(sum(sentence_lengths) / len(sentence_lengths), 1) if sentence_lengths else 0,
        'vocabulary_richness': round(len(unique_words) / max(len(all_words), 1), 3),
        'slang_rate': round(slang_count / max(len(all_words), 1), 3),
        'contraction_rate': round(contraction_count / max(n, 1), 2),
        'technical_density': round(technical_count / max(len(all_words), 1), 3),
        'question_rate': round(question_count / max(n, 1), 2),
        'directive_rate': round(directive_count / max(n, 1), 2),
        'dash_rate': round(dash_count / max(n, 1), 2),
        'ellipsis_rate': round(ellipsis_count / max(n, 1), 2),
        'exclamation_rate': round(exclamation_count / max(n, 1), 2),
        'no_caps_rate': round(no_caps_count / max(n, 1), 2),
        'fragment_rate': round(fragment_count / max(n, 1), 2),
        'top_words': [w for w, _ in Counter(all_words).most_common(15)],
    }


def _derive_style_directives(features: dict) -> list[str]:
    """Convert numeric features into actionable style directives."""
    directives = []
    if not features:
        return directives

    # ── Formality ──
    slang = features.get('slang_rate', 0)
    contractions = features.get('contraction_rate', 0)
    no_caps = features.get('no_caps_rate', 0)
    fragments = features.get('fragment_rate', 0)

    formality_score = 1.0 - (slang * 3 + (1 if no_caps > 0.6 else 0) * 0.3 +
                             (1 if fragments > 0.5 else 0) * 0.2)
    formality_score = max(0, min(1, formality_score))

    if formality_score < 0.3:
        directives.append('Operator writes casually — match their energy. No formal intros, no "I\'d be happy to help". Just talk.')
    elif formality_score < 0.6:
        directives.append('Operator is semi-casual — use contractions, skip formalities, but keep technical precision.')
    else:
        directives.append('Operator writes formally — maintain professional tone with proper grammar.')

    # ── Capitalization ──
    if no_caps > 0.7:
        directives.append('Operator never capitalizes — you don\'t need to either in casual responses, but keep code accurate.')

    # ── Brevity ──
    avg_words = features.get('avg_prompt_words', 0)
    if avg_words < 12:
        directives.append('Operator uses very short prompts — respond concisely. Bullets > paragraphs. Code > explanation.')
    elif avg_words < 25:
        directives.append('Operator uses medium-length prompts — balance explanation with brevity.')
    else:
        directives.append('Operator writes longer prompts with context — match depth. Full explanations are welcome.')

    # ── Question vs directive style ──
    q_rate = features.get('question_rate', 0)
    d_rate = features.get('directive_rate', 0)
    if d_rate > q_rate and d_rate > 0.3:
        directives.append('Operator gives commands, not questions — execute immediately, explain after if needed.')
    elif q_rate > d_rate and q_rate > 0.3:
        directives.append('Operator asks questions — answer the question first, then add context.')

    # ── Dash/stream-of-consciousness style ──
    if features.get('dash_rate', 0) > 0.5:
        directives.append('Operator thinks in dashes (stream-of-consciousness) — mirror this with dash-separated points when natural.')

    # ── Fragment style ──
    if fragments > 0.6:
        directives.append('Operator rarely uses punctuation — fragments and run-ons are normal. Don\'t overcorrect their style in quotes.')

    # ── Technical density ──
    tech = features.get('technical_density', 0)
    if tech > 0.15:
        directives.append('Operator uses heavy technical jargon — skip basic explanations, go straight to implementation.')
    elif tech < 0.05:
        directives.append('Operator uses plain language — avoid unnecessary jargon in explanations.')

    # ── Slang presence ──
    if slang > 0.02:
        directives.append('Operator uses slang/informal markers — casual tone is expected and appreciated.')

    return directives


def build_voice_profile(root: Path) -> dict:
    """Build a voice style profile from recent prompts."""
    prompts = _load_recent_prompts(root)
    if not prompts:
        return {'status': 'no_data'}

    features = extract_voice_features(prompts)
    directives = _derive_style_directives(features)

    profile = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'prompt_count': features.get('prompt_count', 0),
        'features': features,
        'directives': directives,
    }

    # Write to logs
    out_path = root / 'logs' / 'voice_style.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(profile, indent=2), encoding='utf-8')

    return profile


_VOICE_STYLE_RE = re.compile(
    r'<!-- pigeon:voice-style -->.*?<!-- /pigeon:voice-style -->',
    re.DOTALL
)


def inject_voice_style(root: Path) -> bool:
    """Rebuild <!-- pigeon:voice-style --> block in copilot-instructions.md."""
    root = Path(root)
    cp_path = root / '.github' / 'copilot-instructions.md'
    if not cp_path.exists():
        return False

    profile = build_voice_profile(root)
    if profile.get('status') == 'no_data':
        return False

    features = profile.get('features', {})
    directives = profile.get('directives', [])
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    n = features.get('prompt_count', 0)

    lines = [
        '<!-- pigeon:voice-style -->',
        '## Operator Voice Style',
        '',
        f'*Auto-extracted {today} · {n} prompts analyzed · zero LLM calls*',
        '',
        f'**Brevity:** {features.get("avg_prompt_words", 0)} words/prompt '
        f'| **Caps:** {"never" if features.get("no_caps_rate", 0) > 0.7 else "sometimes" if features.get("no_caps_rate", 0) > 0.3 else "normal"} '
        f'| **Fragments:** {features.get("fragment_rate", 0):.0%} '
        f'| **Questions:** {features.get("question_rate", 0):.0%} '
        f'| **Directives:** {features.get("directive_rate", 0):.0%}',
        '',
        '**Voice directives (personality tuning):**',
    ]
    for d in directives:
        lines.append(f'- {d}')

    if features.get('top_words'):
        lines.append('')
        lines.append(f'**Vocabulary fingerprint:** {", ".join(features["top_words"][:10])}')

    lines.append('<!-- /pigeon:voice-style -->')
    block = '\n'.join(lines)

    try:
        text = cp_path.read_text(encoding='utf-8')
    except Exception:
        return False

    if _VOICE_STYLE_RE.search(text):
        text = _VOICE_STYLE_RE.sub(block, text)
    else:
        # Insert before operator-state if present, otherwise append
        anchor = '<!-- pigeon:operator-state -->'
        if anchor in text:
            text = text.replace(anchor, block + '\n' + anchor)
        else:
            text = text.rstrip() + '\n' + block + '\n'

    cp_path.write_text(text, encoding='utf-8')
    return True
