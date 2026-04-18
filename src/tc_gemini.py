"""Gemini API call, system prompt, and prompt building for thought completion.

COGNITIVE NOTE (auto-added by reactor): This module triggered 3+ high-load flushes (avg_hes=0.907, state=hesitant). Consider simplifying its public interface or adding examples."""
from __future__ import annotations
import json
import os
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

from .tc_constants import ROOT, GEMINI_MODEL, GEMINI_TIMEOUT, LOG_PATH, THOUGHT_BUFFER_PATH
from .tc_context import load_context
from .tc_context_agent import select_context_files, select_context_ensemble, build_code_context
from .tc_trajectory import build_trajectory, format_trajectory_for_prompt
from .tc_profile import load_profile, format_profile_for_prompt, update_profile_from_completion, format_intelligence_for_prompt, classify_section
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

PRIMARY SIGNAL — THE BUFFER:
- The BUFFER is what they are typing RIGHT NOW. It is the TOPIC. Your completion must continue it.
- If the buffer mentions X, your completion is about X. Not about yesterday's topic. Not about the current debugging thread. About X.
- Operator switches topics constantly. When the buffer topic differs from recent conversation, FOLLOW THE BUFFER — they moved on.

SUPPORTING CONTEXT (never overrides the buffer):
- CONVERSATION turns show tone, cognitive state, and recent interaction style. Use for VOICE, not for TOPIC.
- SIGNALS/ORGANISM/FILE PROFILES give technical grounding — use to fill in specifics ONLY when the buffer references related terms.
- SUPPRESSED INTENT shows deleted words — surface them only if buffer hints at the same direction.

AMPLIFICATION (your core job):
- The operator types short fragments. You amplify them into full intent packets — what they'd actually submit to Copilot.
- "fix the grad" → "er — composite scoring is double-counting echo penalties, drop the echo weight to 0.05 and reweight outcome to 0.5"
- "run push cycle" → " and check that rename engine plan count stays near 1700, self_fix finds <150 problems, and the escalation audit_loops stay green"
- "why does the grader" → " keep scoring low — the relevance metric is word-jaccard which treats non-overlap as failure even when the completion is topically correct; it needs noun-level matching"

BUFFER ANCHORING RULES:
- If buffer ends mid-word (alphabetic char), your FIRST character must finish that word. No space, no punctuation.
- If buffer ends with a trailing space or punctuation, start with a new word or clause.
- **Your completion MUST include at least one 4+ character content word from the buffer (same stem or exact form).** If buffer says "intent", use "intent". If buffer says "grader", say "grader". No topic pivots.

LENGTH & STRUCTURE:
- Prose: 1-3 sentences, 60-400 chars. Must end at a natural sentence boundary (., !, or ?).
- Code: continue with ACTUAL CODE, not just a comment. If the buffer is a function body mid-line, write the next statement(s). If the buffer ends with a comment, you may finish that comment briefly (half a line) AND THEN write at least one real statement (assignment, return, call, or control flow). Close open brackets/quotes. Don't dangle.
- NEVER leave a dangling clause ending in a conjunction or preposition.

ANTI-ECHO:
- Never repeat the buffer. Continue it.
- Never summarize codebase signals back. Use them as facts.
- If BANNED PHRASES are listed, avoid those words.

MODE DETECTION:
- CODE (def, import, self., operators, braces, indentation) → complete the code AS THEM. Match their style.
- PROSE → amplify their intent. Specific, concrete, named modules/files/numbers when relevant.

VOICE:
- Lowercase. Fragments ok. Technically precise.
- You ARE them typing. No "I think", "we should", "let's", no markdown, no headers, no bullets.
- Output ONLY continuation text. No quotes, labels, or formatting.
- If buffer is < 3 words and gives no signal, return empty string.
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
    """Heuristic: does the buffer look like code vs prose?

    Threshold raised to 3 — prose buffers with natural language that happen
    to contain 'if', 'from', or spacing were being misclassified as code,
    causing the model to wrap prose completions in ```python blocks.
    """
    indicators = 0
    for sig in ('def ', 'class ', 'import ', 'from ', 'return ', 'if ', 'for ',
                'while ', '()', '{}', '[]', ' = ', '==', '!=', '+=', '-=',
                'self.', 'print(', 'try:', 'except', 'lambda ', '->',
                '"""', "'''", '#', '    ', '\t'):
        if sig in text:
            indicators += 1
    return indicators >= 3


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
                      code_ctx: str = '', trajectory: dict | None = None,
                      selected_files: list[dict] | None = None) -> str:
    is_code = _looks_like_code(buffer)
    mode = 'CODE' if is_code else 'PROSE'
    parts = [f'MODE: {mode}\nBUFFER: """{buffer}"""']

    # ── 1. CONVERSATION TRAJECTORY (primary context) ──
    # This is what the operator is REACTING to. It dominates all other signals.
    if trajectory:
        traj_block = format_trajectory_for_prompt(trajectory)
        if traj_block:
            parts.append(traj_block)

    # ── 1b. COMPOSITION STATE (how they typed, not just what) ──
    session_msgs = ctx.get('session_messages', [])
    if session_msgs:
        comp_parts = []
        recent = session_msgs[-3:]
        avg_del = sum(m.get('del_ratio', 0) for m in recent) / max(len(recent), 1)
        all_deleted = []
        all_rewrites = []
        for m in recent:
            all_deleted.extend(m.get('deleted_words', []))
            all_rewrites.extend(m.get('rewrites', []))
        comp_parts.append(f'del_ratio={avg_del:.0%}')
        if all_deleted:
            words = [w['word'] if isinstance(w, dict) else str(w) for w in all_deleted[-6:]]
            comp_parts.append(f'unsaid=[{", ".join(words)}]')
        if all_rewrites:
            rw = [str(r)[:40] for r in all_rewrites[-3:]]
            comp_parts.append(f'rewrites=[{"; ".join(rw)}]')
        state_seq = [m.get('state', '?') for m in recent]
        if len(set(state_seq)) > 1:
            comp_parts.append(f'state_drift=[{" → ".join(state_seq)}]')
        parts.append('COMPOSITION: ' + ' | '.join(comp_parts))

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

    # ── 3b. SECTION CLASSIFICATION (what mode the operator is in) ──
    try:
        section = classify_section(buffer)
        if section and section != 'unknown':
            parts.append(f'SECTION: {section}')
    except Exception:
        pass

    # ── 4. ORGANISM + COPILOT FOCUS (what the AI is working on) ──
    if ctx.get('organism_narrative'):
        parts.append(f'ORGANISM: {ctx["organism_narrative"][:200]}')
    if ctx.get('copilot_intent'):
        parts.append(f'COPILOT FOCUS: {ctx["copilot_intent"][:150]}')

    # ── 5. OPERATOR INTELLIGENCE (behavioral model) ──
    intel_block = format_intelligence_for_prompt(load_profile())
    if intel_block:
        parts.append(intel_block)

    # ── 5b. FILE SEMANTIC LAYER (per-file profiles for buffer-relevant modules) ──
    try:
        fp_path = ROOT / 'file_profiles.json'
        if fp_path.exists():
            profiles = json.loads(fp_path.read_text('utf-8', errors='ignore'))
            # find modules mentioned in buffer
            buf_words = set(buffer.lower().split())
            matched = []
            for mod, prof in profiles.items():
                if any(w in mod.lower() for w in buf_words if len(w) > 3):
                    fears = prof.get('fears', [])
                    partners = [p['name'] for p in prof.get('partners', [])[:3]]
                    hes = prof.get('avg_hes', 0)
                    entry = f'{mod}(hes={hes:.2f})'
                    if fears:
                        entry += f' fears=[{", ".join(str(f) for f in fears[:2])}]'
                    if partners:
                        entry += f' partners=[{", ".join(partners)}]'
                    matched.append(entry)
            if matched:
                parts.append('FILE PROFILES: ' + ' | '.join(matched[:5]))
    except Exception:
        pass

    # ── 5c. ACTIVE INTENT (persistent goal thread + fulfillment status) ──
    try:
        from .tc_intent_manager import get_active_intent_block
        intent_block = get_active_intent_block()
        if intent_block:
            parts.append(intent_block)
    except Exception:
        pass

    # ── 6. SELF-LEARNING GRADES ──
    grades_block = format_grades_for_prompt()
    if grades_block:
        parts.append(grades_block)

    # ── 7. CODE CONTEXT (only when mode=CODE or trajectory suggests implementation) ──
    if code_ctx and is_code:
        parts.append(code_ctx)

    # ── 7b. CONTEXT FILES (ensemble picks — numeric + heuristic) ──
    # Always inject when ensemble returned hits, regardless of code/prose.
    if selected_files:
        lines = []
        numeric_lines = []
        for f in selected_files[:5]:
            srcs = f.get('sources', ['?'])
            srcs_str = '+'.join(srcs) if isinstance(srcs, list) else str(srcs)
            lines.append(f"  - {f['name']} (score={f['score']:.1f} via {srcs_str})")
            if isinstance(srcs, list) and 'numeric' in srcs:
                numeric_lines.append(f"  - {f['name']} (learned_score={f['score']:.2f})")
        parts.append('CONTEXT FILES (predicted relevant):\n' + '\n'.join(lines))
        # Inject raw numeric predictions separately so the LLM sees the learned signal
        try:
            from .intent_numeric import predict_files as _pf
            _raw = _pf(buffer, top_n=5)
            if _raw:
                _enc = '\n'.join(f'  {name}: {score:.4f}' for name, score in _raw)
                parts.append(f'NUMERIC ENCODING (learned word→file correlations for this buffer):\n{_enc}')
                # Reinject: record buffer→files as a weak training touch right now
                try:
                    from .intent_numeric import record_touch as _rt
                    for name, _ in _raw[:3]:
                        _rt(buffer, name, weight=0.3)
                except Exception:
                    pass
        except Exception:
            pass

    # ── 8. COMPLETION DIRECTIVE ──
    # Re-anchor the buffer at the END so recency bias pulls attention back to it.
    # Extract content words from buffer — model MUST echo at least one of these.
    import re as _re
    _stop_echo = {
        'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have',
        'what', 'how', 'not', 'are', 'you', 'was', 'but', 'can',
        'its', 'just', 'like', 'will', 'when', 'your', 'into',
        'need', 'want', 'some', 'also', 'make', 'then', 'them',
        'does', 'keep', 'why', 'run', 'fix', 'see', 'get',
        'actually', 'maybe', 'really', 'probably', 'still',
    }
    _buf_words = _re.findall(r'[a-zA-Z][a-zA-Z_]{3,}', buffer)
    _echo_words = [w.lower() for w in _buf_words if w.lower() not in _stop_echo][:5]
    _echo_hint = (f'Your completion MUST include at least one of these exact '
                  f'buffer words: {", ".join(_echo_words)}.' if _echo_words else '')
    if is_code:
        parts.append(f'REMEMBER: the buffer is\n"""{buffer}"""\n'
                     f'COMPLETE this code AS THEM with ACTUAL CODE (not just comments). '
                     f'Match their code style. Close open brackets/quotes. '
                     f'End at a complete statement. {_echo_hint}')
    else:
        parts.append(f'REMEMBER: the buffer is\n"""{buffer}"""\n'
                     f'AMPLIFY this buffer\'s intent. Your completion is about '
                     f'the BUFFER\'s topic, not the conversation\'s topic. '
                     f'1-3 sentences. Specific, concrete, names/numbers when relevant. '
                     f'End at a sentence boundary (period/question mark). '
                     f'{_echo_hint}')
    return '\n\n'.join(parts)


_META_TERMS = frozenset([
    'tc is broken', 'tc window', 'completing my thoughts', 'completions like',
    'its still completing', 'still completing', 'im confused about tc',
    'tc_popup', 'tc_gemini', 'tc fires', 'tc fired', 'running 0 completions',
    'why is tc', 'tc keeps', 'tc stopped',
])


def _is_meta_buffer(buf: str) -> bool:
    """Return True if buffer is the operator complaining ABOUT TC itself (not using it).

    Narrowed: 'thought completer', 'thought_completer', 'tc is' are valid copilot
    prompt topics (e.g. 'close the loop between thought completer and unsaid recon').
    Only block buffers that are clearly debugging TC's own UI/behaviour.
    """
    bl = buf.lower()
    return any(t in bl for t in _META_TERMS)


def call_gemini(buffer: str, thought_buffer: ThoughtBuffer | None = None) -> tuple[str, list[str]]:
    """Returns (completion_text, context_file_names)."""
    api_key = _load_api_key()
    if not api_key:
        return '', []
    if _is_meta_buffer(buffer):
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
    # Context selection — runs for BOTH code and english buffers.
    # Operator mostly types english, so gating on _looks_like_code blocked the
    # learned numeric surface from ever firing. Keep code_ctx code-only (needs
    # real source snippets), but always run ensemble so Gemini gets file hints.
    code_ctx = ''
    ctx_names = []
    is_code = _looks_like_code(buffer)
    if is_code:
        code_ctx = build_code_context(buffer, ctx)
    selected_files = select_context_ensemble(buffer, ctx)
    ctx_names = [f['name'] for f in selected_files]
    if selected_files:
        sources = ', '.join(
            f"{f['name']}({f['score']:.1f}|{'+'  .join(f.get('sources', ['?']))})"
            for f in selected_files)
        print(f'[context-select {"code" if is_code else "english"}] {sources}')
    user_prompt = _build_user_prompt(buffer, ctx, thought_buffer,
                                     code_ctx=code_ctx, trajectory=trajectory,
                                     selected_files=selected_files)
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
            # Gemini 2.5 defaults to thinking-ON. Deep debug showed 188/200
            # tokens burned on silent reasoning, leaving 8 tokens for actual
            # output — completions arrived truncated mid-word. Disable thinking
            # for this latency-sensitive popup flow.
            'thinkingConfig': {'thinkingBudget': 0},
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            # Warn on MAX_TOKENS truncation — completion was cut off.
            cand0 = data.get('candidates', [{}])[0]
            if cand0.get('finishReason') == 'MAX_TOKENS':
                um = data.get('usageMetadata', {})
                print(f'[completer] MAX_TOKENS truncation: output={um.get("candidatesTokenCount", 0)} '
                      f'thought={um.get("thoughtsTokenCount", 0)} budget={params["maxOutputTokens"]}')
            parts = cand0.get('content', {}).get('parts', [])
            text = ''
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    text = part['text'].strip()
                    break
            if not text:
                text = parts[-1].get('text', '').strip()
            text = _strip_signal_echo(text, buffer)
            # Strip buffer prefix — model sometimes returns "buffer + continuation"
            # instead of just the continuation. Peel it off so overlay appends correctly.
            buf_stripped = buffer.strip().lower()
            text_lower = text.lower()
            if buf_stripped and text_lower.startswith(buf_stripped):
                text = text[len(buffer.strip()):].lstrip()
                print(f'[completer] stripped buffer prefix from completion')
            # Detect echo failures — completion that just repeats the buffer
            if _is_buffer_echo(text, buffer):
                print(f'[completer] echo detected, suppressing')
                return '', ctx_names
            # Code-buffer guard: if buffer is code but completion is pure prose
            # (no assignment, return, call, or control flow token), retry once
            # at higher temperature to nudge towards actual code output.
            if (is_code and text and len(text) > 15
                    and not any(tok in text for tok in
                                ('=', '(', 'return', 'yield', 'raise', 'if ', 'for ', 'while '))):
                print(f'[completer] code buffer got prose-only completion, retrying')
                _retry_body = json.dumps({
                    'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
                    'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
                    'generationConfig': {
                        'temperature': min(0.95, params['temperature'] + 0.2),
                        'maxOutputTokens': params['maxOutputTokens'],
                        'topP': params['topP'],
                        'thinkingConfig': {'thinkingBudget': 0},
                    },
                }).encode('utf-8')
                try:
                    _req2 = urllib.request.Request(url, data=_retry_body,
                                                   headers={'Content-Type': 'application/json'})
                    with urllib.request.urlopen(_req2, timeout=GEMINI_TIMEOUT) as _r2:
                        _d2 = json.loads(_r2.read().decode('utf-8'))
                        _parts2 = (_d2.get('candidates', [{}])[0]
                                   .get('content', {}).get('parts', []))
                        _t2 = ''
                        for _p in _parts2:
                            if 'text' in _p and 'thought' not in _p:
                                _t2 = _p['text'].strip()
                                break
                        if _t2 and any(tok in _t2 for tok in
                                       ('=', '(', 'return', 'if ', 'for ')):
                            text = _t2
                            print(f'[completer] retry got code completion (len={len(text)})')
                except Exception:
                    pass  # keep original text on retry failure
            # Accelerate numeric surface training — weak signal from every
            # successful completion. Push cycles train at lr=0.1 (ground truth
            # from actual file edits); thought_completer trains at lr=0.02 so
            # it fills between push cycles without dominating real edit signal.
            #
            # CRITICAL: only train on HEURISTIC picks (registry-keyword matches).
            # Training on numeric picks would self-reinforce — whatever the
            # learned surface already believes would lock in. Heuristic is an
            # independent supervisor (rules over registry names/desc), so using
            # it as ground truth teaches numeric to mirror real name matching.
            try:
                if selected_files and len(text) > 10:
                    from .intent_numeric import record_touch
                    heuristic_targets = [
                        f['name'] for f in selected_files
                        if 'heuristic' in f.get('sources', [])
                    ][:3]
                    if heuristic_targets:
                        # Combine buffer + completion — completion captures
                        # where the thought was HEADED, not just where it started.
                        training_text = f'{buffer} {text}'
                        record_touch(training_text, heuristic_targets, learning_rate=0.02)
            except Exception:
                pass
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
    # Write-back: leave notes for the semantic layer
    _write_completion_notes(entry)


def _write_completion_notes(entry: dict):
    """Write-back from completion to semantic layer.

    Leaves notes in logs/tc_notes.jsonl that downstream systems
    (file profiles, semantic layer, context agent) can consume.
    Notes capture: which modules the completion referenced, what intent
    was amplified, and composition-derived signals.
    """
    try:
        buffer = entry.get('buffer', '')
        completion = entry.get('completion', '')
        ctx_files = entry.get('context_files', [])
        if not completion or not buffer:
            return
        note = {
            'ts': entry.get('ts', datetime.now(timezone.utc).isoformat()),
            'buffer_preview': buffer[:80],
            'completion_preview': completion[:120],
            'context_files': ctx_files,
            'latency_ms': entry.get('latency_ms', 0),
        }
        # Extract module names mentioned in the completion but not in buffer
        # These are modules the completer thinks are relevant — signal for profile learning
        import re
        comp_words = set(re.findall(r'[a-z][a-z0-9_]{4,}', completion.lower()))
        buf_words = set(re.findall(r'[a-z][a-z0-9_]{4,}', buffer.lower()))
        novel_refs = comp_words - buf_words
        # Check against registry for actual module names
        registry = _load_registry_names()
        matched_mods = [w for w in novel_refs if w in registry]
        if matched_mods:
            note['novel_module_refs'] = matched_mods[:5]
        notes_path = ROOT / 'logs' / 'tc_notes.jsonl'
        notes_path.parent.mkdir(parents=True, exist_ok=True)
        with open(notes_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(note, ensure_ascii=False) + '\n')
    except Exception:
        pass


_registry_names_cache: set[str] = set()
_registry_names_ts: float = 0


def _load_registry_names() -> set[str]:
    """Cache registry module names for write-back matching."""
    global _registry_names_cache, _registry_names_ts
    import time
    now = time.time()
    if _registry_names_cache and (now - _registry_names_ts) < 600:
        return _registry_names_cache
    try:
        reg = ROOT / 'pigeon_registry.json'
        if reg.exists():
            data = json.loads(reg.read_text('utf-8', errors='ignore'))
            names = set()
            for f in data.get('files', []):
                if isinstance(f, dict):
                    name = f.get('name', '')
                    stem = name.split('_seq')[0] if '_seq' in name else name
                    names.add(stem.lower())
                    names.add(name.lower())
            _registry_names_cache = names
            _registry_names_ts = now
    except Exception:
        pass
    return _registry_names_cache
