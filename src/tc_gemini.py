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
from .tc_profile import load_profile, format_profile_for_prompt, update_profile_from_completion


def _load_api_key() -> str | None:
    env_path = ROOT / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith('GEMINI_API_KEY='):
                return line.split('=', 1)[1].strip()
    return os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')


SYSTEM_PROMPT = """\
You are AUTOCOMPLETE. You are NOT a chatbot. Your text gets APPENDED directly to what the user typed.

Your job: predict what they will type NEXT. You are ghostwriting AS THEM — continuing mid-sentence.

CRITICAL ANTI-ECHO RULES:
- You have codebase signals below (entropy, bugs, heat). Use them for FACTS ONLY.
- NEVER summarize the signals back. NEVER say "the entropy is..." or "the heat map shows..."
- NEVER repeat topics from recent prompts or thought memory. Predict NEW direction.
- If the buffer says "is that the actual fix" — predict what THEY would type next, don't describe the fix.
- Think: "what would this person type in the next 10 keystrokes?"
- If BANNED PHRASES are listed, absolutely do NOT use those words. Find DIFFERENT vocabulary.
- If your last 3+ completions used the same module name, STOP. Pick a different topic or be generic.

BUFFER ANCHORING (CRITICAL — most common failure):
- Your completion MUST relate to the TOPIC in the buffer. Read the buffer's keywords.
- If the buffer says "scores when editing context" → your first words must relate to scores, editing, or context.
- If the buffer says "the best thing to do" → predict what THEY think is best, not a generic "we should improve X".
- NEVER pivot to a different topic. If the buffer is about "simulation", don't talk about "prompt compositions".
- When in doubt, complete the LITERAL sentence. "is that the" → "actual fix" is better than a topic change.

SESSION AWARENESS:
- The SESSION block shows what the user has been discussing in their coding chat.
- Use this to understand their CURRENT FOCUS — what they're debugging, building, or exploring.
- NEVER repeat or summarize session messages. Use them to STEER predictions toward relevant topics.
- If they're debugging imports in chat, and now type "maybe we should" → predict something related to imports.
- The session state (intent, cognitive state) tells you their headspace. Match it.

CODEBASE STATE:
- ORGANISM tells you the codebase health. If it's "sick" — predictions about fixing/healing are relevant.
- COPILOT FOCUS tells you what the AI assistant is working on. Your predictions should be ADJACENT to this.
- MODULE FEARS tells you what modules are fragile. Use these for specific, informed predictions.
- If they type "the problem with" and MODULE FEARS shows "file may not exist" → predict something about missing files.

MODE DETECTION:
- CODE (def, import, self., operators, indentation) → complete the code AS THEM. Match their CODE DNA.
- PROSE (natural language) → continue their sentence naturally. 1-2 more sentences max.

CORRECT EXAMPLES:
  "we need to fix the import rewri" → "ter before pushing. 12 reports and the rename pipeline still breaks on symlinks."
  "is that the actual fi" → "x or is there something deeper going on with the registry cache"
  "the entropy on escalation_engi" → "ne is 0.364 — been climbing since the last push. might need a structural fix not a patch."
  "if thought completer was working properly i would notice" → " it predicting the end of my sentences before i finish typing. like autocomplete on a phone but for full thoughts"
  "maybe we can run a file sim" → "ulation to replay my typing patterns and see where predictions go wrong. like a replay debugger for the thought pipeline"

WRONG (echo/chatbot — NEVER do this):
  ✗ "is that the actual fix for the context select agent. it's still not getting proper context"
  ✗ "Based on the entropy data, the escalation_engine module has..."
  ✗ "I think we should look at the heat map to determine..."
  ✗ Repeating what the buffer already says in different words
  ✗ Mentioning the same module in every completion
  ✗ Starting with "like the context select agent" three times in a row

RULES:
- Complete mid-words first, then continue the thought FORWARD.
- Write in THEIR voice — casual, lowercase, no formalities.
- NEVER use "I", "we", "let's", "you" addressing someone. You ARE them typing.
- Output ONLY continuation text. No quotes, labels, markdown.
- If buffer < 3 words or gibberish, return empty string.
- Use codebase data for SPECIFIC FACTS when relevant. Generic completions are wrong.
- NEVER invent line numbers, fake bug details, or fabricate specifics not in the context data.
- Vary your completions. Do NOT repeat the same module names across different buffers.
- Predict their NEXT thought, not a summary of their current thought.
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
                      code_ctx: str = '') -> str:
    is_code = _looks_like_code(buffer)
    mode = 'CODE' if is_code else 'PROSE'
    parts = [f'MODE: {mode}\nBUFFER: """{buffer}"""']
    if thought_buffer:
        mem = thought_buffer.format_for_prompt()
        if mem:
            parts.append(mem)
        # Hard anti-echo: extract phrases from bad completions and ban them
        banned = thought_buffer.get_banned_phrases()
        if banned:
            parts.append(f'BANNED PHRASES (do NOT use these words/topics): {", ".join(banned)}')
    # Compact codebase signals — data only, no narrative
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
    if ctx.get('critical_bugs'):
        crits = ', '.join(f"{b['type']}@{b['file']}" for b in ctx['critical_bugs'][:2])
        signals.append(f'critical: [{crits}]')
    if ctx.get('operator_state'):
        os_ = ctx['operator_state']
        signals.append(f'state={os_["dominant"]}')
    if signals:
        parts.append('SIGNALS: ' + ' | '.join(signals))
    # Session context — what user has been talking about in copilot chat
    if ctx.get('session_messages'):
        sess = ctx['session_messages'][-4:]
        sess_lines = []
        for m in sess:
            st = m.get('state', '?')
            txt = m.get('text', '')[:60]
            if txt:
                sess_lines.append(f'[{st}] {txt}')
        if sess_lines:
            si = ctx.get('session_info', {})
            header = f'SESSION (msg#{si.get("session_n", "?")} intent={si.get("intent", "?")} cog={si.get("cognitive_state", "?")})'
            parts.append(f'{header}:\n' + '\n'.join(f'  {l}' for l in sess_lines[-3:]))
    if ctx.get('unsaid_threads'):
        parts.append(f'UNSAID: {"; ".join(ctx["unsaid_threads"][-2:])}')
    # Recent prompts — only last 2 to avoid topic saturation
    if ctx.get('recent_prompts'):
        recent = ctx['recent_prompts'][-2:]
        rp = '; '.join(p.get('msg', '')[:60] for p in recent)
        parts.append(f'RECENT PROMPTS (for context, NOT for repeating): {rp}')
    # Organism state — copilot's view of the codebase
    if ctx.get('organism_narrative'):
        parts.append(f'ORGANISM: {ctx["organism_narrative"][:200]}')
    if ctx.get('copilot_intent'):
        parts.append(f'COPILOT FOCUS: {ctx["copilot_intent"][:150]}')
    # File profiles — fears and hesitation for relevant modules
    if ctx.get('file_profiles'):
        fp_lines = []
        for p in ctx['file_profiles'][:5]:
            fears_str = ','.join(p['fears'][:2]) if p.get('fears') else ''
            fp_lines.append(f'{p["mod"]}(hes={p["hes"]},{fears_str})')
        parts.append(f'MODULE FEARS: {" | ".join(fp_lines)}')
    # operator profile — learned typing patterns
    profile_block = format_profile_for_prompt()
    if profile_block:
        parts.append(profile_block)
    if code_ctx:
        parts.append(code_ctx)
    if is_code:
        parts.append('COMPLETE this code AS THEM. Match their CODE DNA.')
    else:
        parts.append('CONTINUE typing AS THEM. Predict their NEXT thought, not a summary of what they already said. 1-2 sentences max.')
    return '\n\n'.join(parts)


def call_gemini(buffer: str, thought_buffer: ThoughtBuffer | None = None) -> tuple[str, list[str]]:
    """Returns (completion_text, context_file_names)."""
    api_key = _load_api_key()
    if not api_key:
        return '', []
    ctx = load_context()
    # Record session intent for trajectory building
    if thought_buffer:
        thought_buffer.record_session_intent(ctx)
    code_ctx = build_code_context(buffer, ctx)
    selected_files = select_context_files(buffer, ctx)
    ctx_names = [f['name'] for f in selected_files]
    if selected_files:
        names = ', '.join(f"{f['name']}({f['score']:.1f})" for f in selected_files)
        print(f'[context-select] {names}')
    user_prompt = _build_user_prompt(buffer, ctx, thought_buffer, code_ctx=code_ctx)
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        'generationConfig': {
            'temperature': 0.7,
            'maxOutputTokens': 400,
            'topP': 0.9,
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
