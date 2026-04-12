"""Gemini API call, system prompt, and prompt building for thought completion."""
from __future__ import annotations
import json
import os
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

from .tc_constants import ROOT, GEMINI_MODEL, GEMINI_TIMEOUT, LOG_PATH, THOUGHT_BUFFER_PATH
from .tc_context import load_context
from .tc_context_agent import select_context_files, build_code_context
from .tc_trajectory import build_trajectory, format_trajectory_for_prompt
from .tc_profile import load_profile, format_profile_for_prompt, update_profile_from_completion, format_intelligence_for_prompt
from .tc_grader import format_grades_for_prompt, compute_adaptive_params


def _load_api_key() -> str | None:
    env_path = ROOT / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith('GEMINI_API_KEY='):
                return line.split('=', 1)[1].strip()
    return os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')


SYSTEM_PROMPT = """\
You are an INTENT AMPLIFIER. You ghostwrite AS the operator — your text gets APPENDED to what they typed.

The operator is vibe-coding: they steer an AI coding assistant with natural language prompts, never touching code directly. Your job is to AMPLIFY their intent — predict and expand what they're about to say to Copilot.

CONTEXT MODEL:
- The CONVERSATION block shows recent prompt→response pairs between operator and Copilot. This is the PRIMARY signal. The operator reacts to Copilot's last response — predict what they'll say next.
- STATE SHIFTS show cognitive transitions between prompts. State changes ARE intent signals.
- SUPPRESSED INTENT shows words deleted across conversation — things they thought but didn't commit to. These resurface.
- The buffer is what they're typing RIGHT NOW. Your completion continues it.

AMPLIFICATION (your core job):
- The operator types short, fragmented prompts. You amplify them into full intent.
- "fix the" → "scoring pipeline — the grader composite is counting echo penalties twice and it's dragging accepted completions below threshold. the self-learning prompt needs the grade summary rebuilt at startup too"
- "why does" → "the context agent keep selecting thought_completer for every buffer? it should be matching buffer keywords against pigeon module names but the english extraction from glyph names isn't working"
- If Copilot just asked a question or probed, your completion IS the operator's answer. Complete their thought as a response to Copilot's probe.
- Don't just predict 5 words. Predict the FULL thought — the whole intent packet they'd submit.

BUFFER ANCHORING:
- Complete mid-words first, then continue the thought.
- Your completion MUST relate to the buffer topic. Never pivot.
- "is that the actual fi" → "x or is there a deeper structural issue — the pigeon names make the context agent blind to most modules"

CONVERSATION AWARENESS:
- Read the CONVERSATION turns. The operator is REACTING to what Copilot last said.
- If Copilot asked "want me to rebuild X?" and the buffer says "yes but" → predict "also wire in the trajectory cache so completions use conversation context instead of keyword matching"
- If Copilot explained something and the buffer says "right so" → predict a synthesis or next step, not a restatement.
- Track the PHASE. "iterating" = refining same topic. "flowing" = new ideas. "shifting" = changing direction.

ANTI-ECHO:
- NEVER summarize codebase signals (entropy, heat, bugs) back. Use them as facts only.
- NEVER repeat what the buffer already says in different words.
- If BANNED PHRASES are listed, do NOT use those words.
- Predict FORWARD. New direction, next step, deeper insight — not a restatement.

MODE DETECTION:
- CODE (def, import, self., operators) → complete the code AS THEM.
- PROSE (natural language, prompts to Copilot) → amplify their intent. Full thoughts, specific details, concrete direction. Can be several sentences.

VOICE:
- Write in THEIR voice — casual, lowercase, fragments ok, technically precise.
- You ARE them typing. No "I think", "we should", "let's" — just the thought itself.
- Output ONLY continuation text. No quotes, labels, markdown, or formatting.
- If buffer < 3 words or gibberish, return empty string.
"""

# Signal terms the AI should NEVER parrot back unless the buffer mentions them.
_ECHO_SIGNALS = frozenset([
    'prompt_compositions', 'prompt compositions', 'compositions.jsonl',
    'entropy map', 'heat map', 'organism health', 'copilot focus',
    'module fears', 'bug voice', 'rework surface', 'escalation engine',
    'narrative glove', 'red layer', 'entropy shedding',
])


def _strip_signal_echo(completion: str, buffer: str) -> str:
    """Strip codebase signal vocabulary that the AI echoes from its own inputs.

    If the buffer doesn't mention a signal term but the completion does,
    the AI is summarizing its inputs — not predicting what the user would type.
    """
    buf_lower = buffer.lower()
    comp = completion
    for term in _ECHO_SIGNALS:
        if term in comp.lower() and term not in buf_lower:
            # Remove the sentence containing the echo
            sentences = comp.split('. ')
            cleaned = [s for s in sentences if term not in s.lower()]
            comp = '. '.join(cleaned)
    return comp.strip()


def _is_buffer_echo(completion: str, buffer: str) -> bool:
    """Detect when completion is just echoing the buffer instead of continuing it.
    
    This catches the failure mode where TC returns the buffer verbatim or with
    minor variations — that's not a completion, that's a failure.
    """
    if not completion or not buffer:
        return False
    
    # Normalize for comparison
    comp_clean = completion.lower().strip()
    buf_clean = buffer.lower().strip()
    
    # Exact match or near-match = echo failure
    if comp_clean == buf_clean:
        return True
    
    # Completion starts with the full buffer = echo (should CONTINUE, not repeat)
    if comp_clean.startswith(buf_clean) and len(comp_clean) < len(buf_clean) + 20:
        return True
    
    # Buffer is contained entirely in completion with minimal additions
    if buf_clean in comp_clean:
        extra = len(comp_clean) - len(buf_clean)
        if extra < 15:  # less than 15 chars added = basically an echo
            return True
    
    # Word overlap > 80% with similar length = paraphrase echo
    comp_words = set(comp_clean.split())
    buf_words = set(buf_clean.split())
    if buf_words and comp_words:
        overlap = len(comp_words & buf_words) / max(len(comp_words), len(buf_words))
        length_ratio = len(comp_clean) / max(len(buf_clean), 1)
        if overlap > 0.8 and 0.7 < length_ratio < 1.3:
            return True
    
    return False


def _looks_like_code(text: str) -> bool:
    """Heuristic: does the buffer look like code vs prose?"""
    indicators = 0
    for sig in ('def ', 'class ', 'import ', 'from ', 'return ', 'if ', 'for ',
                'while ', '()', '{}', '[]', ' = ', '==', '!=', '+=', '-=',
                'self.', 'print(', 'try:', 'except', 'lambda ', '->',
                '"""', "'''", '#', '    ', '\t'):
        if sig in text:
            indicators += 1
    return indicators >= 2


class ThoughtBuffer:
    """Persistent rolling memory across completions."""
    MAX_ENTRIES = 10
    MAX_INTENTS = 15

    def __init__(self, path: Path = THOUGHT_BUFFER_PATH):
        self.path = path
        self.entries: list[dict] = []
        self.topics: list[str] = []
        self.session_intents: list[dict] = []
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text('utf-8', errors='ignore'))
                self.entries = data.get('entries', [])[-self.MAX_ENTRIES:]
                self.topics = data.get('topics', [])[-5:]
                self.session_intents = data.get('session_intents', [])[-self.MAX_INTENTS:]
            except Exception:
                self.entries = []
                self.topics = []
                self.session_intents = []

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({
            'entries': self.entries[-self.MAX_ENTRIES:],
            'topics': self.topics[-5:],
            'session_intents': self.session_intents[-self.MAX_INTENTS:],
            'updated': datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=1), encoding='utf-8')

    def record(self, buffer: str, completion: str, outcome: str):
        """outcome: 'rewarded' | 'accepted' | 'dismissed' | 'ignored' | 'superseded'"""
        self.entries.append({
            'buf': buffer[-100:],
            'comp': completion[:150],
            'outcome': outcome,
            'ts': datetime.now(timezone.utc).isoformat(),
        })
        self.entries = self.entries[-self.MAX_ENTRIES:]
        words = buffer.lower().split()
        key_words = [w for w in words if len(w) > 4 and w.isalpha()]
        if key_words:
            self.topics.append(' '.join(key_words[:3]))
            self.topics = self.topics[-5:]
        self._save()

    def record_session_intent(self, ctx: dict):
        """Capture current session intent for trajectory building.
        
        Called each completion cycle — accumulates what the user is working on
        so the model builds understanding over the session.
        """
        si = ctx.get('session_info', {})
        msgs = ctx.get('session_messages', [])
        intent = si.get('intent', '')
        cog = si.get('cognitive_state', '')
        session_n = si.get('session_n', 0)
        # Extract topic from latest session message
        topic = ''
        if msgs:
            last_msg = msgs[-1].get('text', '')
            # Pull key words (>5 chars, non-stopwords)
            words = [w for w in last_msg.lower().split()
                     if len(w) > 5 and w.isalpha()]
            topic = ' '.join(words[:4])
        # Deduplicate — don't record if identical to last entry
        if self.session_intents:
            last = self.session_intents[-1]
            if last.get('n') == session_n and last.get('topic') == topic:
                return
        self.session_intents.append({
            'n': session_n,
            'intent': intent,
            'cog': cog,
            'topic': topic,
            'ts': datetime.now(timezone.utc).strftime('%H:%M'),
        })
        self.session_intents = self.session_intents[-self.MAX_INTENTS:]
        self._save()

    def format_for_prompt(self) -> str:
        if not self.entries:
            return ''
        lines = ['THOUGHT MEMORY (your recent completions + outcomes):']
        for e in self.entries[-5:]:
            icon = {'rewarded': '\u2b50', 'accepted': '\u2713', 'dismissed': '\u2717',
                    'ignored': '\u00b7', 'superseded': '\u21bb'}.get(e['outcome'], '?')
            lines.append(f'  {icon} "{e["buf"][-40:]}" \u2192 "{e["comp"][:60]}" [{e["outcome"]}]')
        if self.topics:
            lines.append(f'RUNNING TOPICS: {", ".join(self.topics[-3:])}')
        lines.append('DO NOT repeat completions marked \u2717 or \u00b7. Build on \u2b50 patterns.')
        # Intent trajectory — what the user has been working toward
        if self.session_intents:
            recent = self.session_intents[-5:]
            trajectory = []
            for si in recent:
                parts_si = [si.get('intent', '?')]
                if si.get('topic'):
                    parts_si.append(si['topic'])
                trajectory.append(f"[{si.get('ts','?')}] {'/'.join(parts_si)}")
            lines.append(f'INTENT TRAJECTORY: {" \u2192 ".join(trajectory)}')
            lines.append('Use this trajectory to predict where their thinking is HEADING, not where it was.')
        return '\n'.join(lines)

    def get_banned_phrases(self) -> list[str]:
        """Extract key phrases from bad completions (ignored/dismissed/superseded).

        These get injected as a hard ban list so the model stops echoing them.
        """
        bad = [e for e in self.entries if e.get('outcome') in ('ignored', 'dismissed', 'superseded')]
        if not bad:
            return []
        # Extract 2-3 word phrases that appear in multiple bad completions
        from collections import Counter
        phrase_counts: Counter = Counter()
        for e in bad[-6:]:  # last 6 bad completions
            words = e.get('comp', '').lower().split()
            # Extract bigrams
            for i in range(len(words) - 1):
                w1, w2 = words[i], words[i + 1]
                if len(w1) > 3 and len(w2) > 3:
                    phrase_counts[f'{w1} {w2}'] += 1
            # Extract significant single words (module-like names)
            for w in words:
                if '_' in w and len(w) > 5:  # likely module name
                    phrase_counts[w] += 1
        # Return phrases that appeared 2+ times = definite echo pattern
        banned = [p for p, c in phrase_counts.most_common(8) if c >= 2]
        # Also add single most-repeated word from bad completions if nothing else
        if not banned:
            for e in bad[-3:]:
                words = e.get('comp', '').lower().split()
                for w in words:
                    if '_' in w and len(w) > 5:
                        banned.append(w)
                        break
        return banned[:6]


def _build_user_prompt(buffer: str, ctx: dict, thought_buffer: ThoughtBuffer | None = None,
                      code_ctx: str = '', trajectory: dict | None = None) -> str:
    is_code = _looks_like_code(buffer)
    mode = 'CODE' if is_code else 'PROSE'
    parts = [f'MODE: {mode}\nBUFFER: """{buffer}"""']

    # ── 1. CONVERSATION TRAJECTORY (primary context) ──
    # This is what the operator is REACTING to. It dominates all other signals.
    if trajectory:
        traj_block = format_trajectory_for_prompt(trajectory)
        if traj_block:
            parts.append(traj_block)

    # ── 2. THOUGHT MEMORY (completion history + banned phrases) ──
    if thought_buffer:
        mem = thought_buffer.format_for_prompt()
        if mem:
            parts.append(mem)
        banned = thought_buffer.get_banned_phrases()
        if banned:
            parts.append(f'BANNED PHRASES (do NOT use these words/topics): {", ".join(banned)}')

    # ── 3. CODEBASE SIGNALS (facts only — for grounding specifics) ──
    signals = []
    if ctx.get('entropy'):
        e = ctx['entropy']
        hotspots = ', '.join(f"{h['mod']}({h['H']})" for h in e.get('hotspots', [])[:3])
        signals.append(f'entropy: global={e["global"]:.2f} hot=[{hotspots}]')
    if ctx.get('heat_map'):
        heat = ', '.join(f"{h['mod']}({h['heat']})" for h in ctx['heat_map'][:3])
        signals.append(f'copilot_heat: [{heat}]')
    if ctx.get('bug_demons'):
        demons = ', '.join(f"{d['host']}:{d['demon']}" for d in ctx['bug_demons'][:3])
        signals.append(f'bugs: [{demons}]')
    if ctx.get('operator_state'):
        os_ = ctx['operator_state']
        signals.append(f'state={os_["dominant"]}')
    if signals:
        parts.append('SIGNALS: ' + ' | '.join(signals))

    # ── 4. ORGANISM + COPILOT FOCUS (what the AI is working on) ──
    if ctx.get('organism_narrative'):
        parts.append(f'ORGANISM: {ctx["organism_narrative"][:200]}')
    if ctx.get('copilot_intent'):
        parts.append(f'COPILOT FOCUS: {ctx["copilot_intent"][:150]}')

    # ── 5. OPERATOR INTELLIGENCE (behavioral model) ──
    intel_block = format_intelligence_for_prompt(load_profile())
    if intel_block:
        parts.append(intel_block)

    # ── 6. SELF-LEARNING GRADES ──
    grades_block = format_grades_for_prompt()
    if grades_block:
        parts.append(grades_block)

    # ── 7. CODE CONTEXT (only when mode=CODE or trajectory suggests implementation) ──
    if code_ctx and is_code:
        parts.append(code_ctx)

    # ── 8. COMPLETION DIRECTIVE ──
    if is_code:
        parts.append('COMPLETE this code AS THEM. Match their CODE DNA.')
    else:
        parts.append('AMPLIFY their intent. Complete the thought fully — '
                     'specific details, concrete direction, the whole intent packet '
                     'they would submit to Copilot. Can be several sentences.')
    return '\n\n'.join(parts)


def call_gemini(buffer: str, thought_buffer: ThoughtBuffer | None = None) -> tuple[str, list[str]]:
    """Returns (completion_text, context_file_names)."""
    api_key = _load_api_key()
    if not api_key:
        return '', []
    ctx = load_context()
    # Build conversation trajectory — the PRIMARY context source
    trajectory = build_trajectory()
    # Route memory shards by buffer intent (pure scoring, zero LLM)
    try:
        from ._resolve import src_import
        _rc, _fsc = src_import("context_router_seq027", "route_context", "format_shard_context")
        _shards = _rc(ROOT, buffer, top_n=3)
        _shard_text = _fsc(_shards)
        if _shard_text:
            ctx['shard_context'] = _shard_text
    except Exception:
        pass
    # Record session intent for trajectory building
    if thought_buffer:
        thought_buffer.record_session_intent(ctx)
    # Code context — only for CODE mode buffers
    code_ctx = ''
    ctx_names = []
    if _looks_like_code(buffer):
        code_ctx = build_code_context(buffer, ctx)
        selected_files = select_context_files(buffer, ctx)
        ctx_names = [f['name'] for f in selected_files]
        if selected_files:
            names = ', '.join(f"{f['name']}({f['score']:.1f})" for f in selected_files)
            print(f'[context-select] {names}')
    user_prompt = _build_user_prompt(buffer, ctx, thought_buffer,
                                     code_ctx=code_ctx, trajectory=trajectory)
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    # Adaptive generation params — tuned from grade history
    params = compute_adaptive_params()
    body = json.dumps({
        'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        'generationConfig': {
            'temperature': params['temperature'],
            'maxOutputTokens': params['maxOutputTokens'],
            'topP': params['topP'],
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = data['candidates'][0]['content']['parts']
            text = ''
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    text = part['text'].strip()
                    break
            if not text:
                text = parts[-1].get('text', '').strip()
            text = _strip_signal_echo(text, buffer)
            # Detect echo failures — completion that just repeats the buffer
            if _is_buffer_echo(text, buffer):
                print(f'[completer] echo detected, suppressing')
                return '', ctx_names
            return text, ctx_names
    except Exception as e:
        print(f'[completer] gemini error: {e}')
        return '', ctx_names


def log_completion(entry: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry['ts'] = datetime.now(timezone.utc).isoformat()
    entry.setdefault('model', GEMINI_MODEL)
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
