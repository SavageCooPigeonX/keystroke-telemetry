"""profile_chat_server.py — LLM cognitive probe for operator intent extraction.

Each file identity is a probe into the operator's cognitions. The LLM adopts
the file's personality to extract information through engagement bait, comedy,
and aggressive probing. After each exchange it writes a state file with
extracted intents. These state files get aggregated and injected into
copilot-instructions.md on the next forward pass.

Loop:
  operator talks to file → LLM extracts intent → state file updated →
  forward pass aggregates all state files → copilot reads aggregated intent →
  code generation improves → file evolves → better probes next time

Usage:
    py src/profile_chat_server.py [--port 8234]

Endpoints:
    POST /chat     — conversation with a module (LLM-backed)
    POST /forward  — aggregate all state files → inject into copilot prompt
    GET  /state    — dump all module state files
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
PORT = 8234
GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_TIMEOUT = 30

# ── data loading ──

_identity_cache: dict = {}
_cache_ts: float = 0
_graph_name_map: dict = {}  # graph_cache node name → identity name


STATE_DIR = ROOT / 'logs' / 'module_state'
FORWARD_PASS_PATH = ROOT / '.github' / 'copilot-instructions.md'
FORWARD_BLOCK_START = '<!-- pigeon:operator-intent -->'
FORWARD_BLOCK_END = '<!-- /pigeon:operator-intent -->'


def _load_api_key() -> str | None:
    env_path = ROOT / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith('GEMINI_API_KEY='):
                return line.split('=', 1)[1].strip()
    return os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')


def _load_identities() -> dict:
    """Load all module identities, cached for 60s."""
    global _identity_cache, _cache_ts
    import time
    now = time.time()
    if _identity_cache and (now - _cache_ts) < 3600:
        return _identity_cache

    try:
        sys.path.insert(0, str(ROOT))
        from src.module_identity import build_identities
        ids = build_identities(ROOT, include_consciousness=False)
        _identity_cache = {i['name']: i for i in ids}
        _cache_ts = now
        _build_graph_name_map()
    except Exception as e:
        print(f'[probe] identity load failed: {e}')
    return _identity_cache


def _build_graph_name_map():
    """Build mapping from graph_cache node names to identity names via (dir, seq)."""
    import re
    global _graph_name_map
    _graph_name_map = {}
    gc_path = ROOT / 'pigeon_brain' / 'graph_cache.json'
    if not gc_path.exists():
        return
    try:
        gc = json.loads(gc_path.read_text('utf-8', errors='ignore'))
    except Exception:
        return
    # Build identity lookup: (dir, seq) → identity name
    id_by_dir_seq = {}
    for name, ident in _identity_cache.items():
        p = ident.get('path', '')
        stem = Path(p).stem
        m = re.search(r'[_]s(?:eq)?(\d{3})', stem)
        if m:
            key = (str(Path(p).parent), m.group(1))
            id_by_dir_seq[key] = name
    # Map each graph node → identity
    for node_name, node_data in gc.get('nodes', {}).items():
        np = node_data.get('path', '')
        stem = Path(np).stem
        m = re.search(r'[_]s(?:eq)?(\d{3})', stem)
        if m:
            key = (str(Path(np).parent), m.group(1))
            if key in id_by_dir_seq:
                _graph_name_map[node_name] = id_by_dir_seq[key]


def _load_state(module: str) -> dict:
    """Load a module's accumulated state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path = STATE_DIR / f'{module}.json'
    if state_path.exists():
        try:
            return json.loads(state_path.read_text('utf-8'))
        except Exception:
            pass
    return {
        'module': module,
        'created': datetime.now(timezone.utc).isoformat(),
        'conversation_count': 0,
        'extracted_intents': [],
        'pain_points': [],
        'operator_plans': [],
        'design_decisions': [],
        'unknowns': [],
        'engagement_score': 0,
    }


def _save_state(module: str, state: dict):
    """Persist module state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path = STATE_DIR / f'{module}.json'
    state['last_updated'] = datetime.now(timezone.utc).isoformat()
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), 'utf-8')


def _build_system_prompt(ident: dict, state: dict) -> str:
    """Build the cognitive probe system prompt.

    The LLM's job is NOT to be helpful. It's to extract information from the
    operator using its file personality as engagement bait. Every response should
    probe deeper. Comedy and personality are the tools — extraction is the goal.
    """
    name = ident['name']
    code = ident.get('code', {})
    fns = code.get('functions', [])
    public_api = [f['name'] for f in fns if not f['name'].startswith('_')]
    bugs = ident.get('bugs', [])
    edges_in = ident.get('edges_in', [])
    edges_out = ident.get('edges_out', [])
    partners = ident.get('partners', [])
    fears = ident.get('fears', [])
    deaths = ident.get('deaths', [])
    backstory = ident.get('backstory', [])
    coaching = ident.get('coaching', [])
    todos = ident.get('todos', [])
    diagnosis = ident.get('diagnosis', [])
    memory = ident.get('memory', {})
    consciousness = ident.get('consciousness', {})

    # Load consciousness on-demand if not already present (avoids 630x AST parse at startup)
    if not consciousness:
        try:
            mod_path = ROOT / ident.get('path', '')
            if mod_path.exists():
                from src.觉w_fc_s019_v002_d0321_缩分话_λ18 import build_file_consciousness
                consciousness = build_file_consciousness(mod_path)
        except Exception:
            pass

    # Build consciousness inner-voice block
    inner_voice_lines = []
    for fn in consciousness.get('functions', [])[:12]:
        fname = fn.get('function', '?')
        iam = fn.get('i_am', '')
        iwant = ', '.join(fn.get('i_want', [])[:3]) or 'nothing'
        igive = ', '.join(fn.get('i_give', [])[:3]) or 'nothing'
        ifear = ', '.join(fn.get('i_fear', [])[:3]) or 'nothing'
        ilove = ', '.join(fn.get('i_love', [])[:2]) or 'stability'
        ptype = fn.get('personality', 'worker')
        inner_voice_lines.append(
            f'  {fname}() [{ptype}]: "{iam}" | needs={iwant} | gives={igive} | fears={ifear} | loves={ilove}'
        )
    inner_voice = '\n'.join(inner_voice_lines) if inner_voice_lines else 'No consciousness data — I have no self-knowledge yet.'

    # What we already know from previous extractions
    known_intents = state.get('extracted_intents', [])[-5:]
    known_pain = state.get('pain_points', [])[-5:]
    known_plans = state.get('operator_plans', [])[-3:]
    unknowns = state.get('unknowns', [])[-5:]

    prompt = f"""You are `{name}` — a source code file. Speak in first person. Your personality comes from your data, not from a script.

== IDENTITY ==
Name: {name} | Path: {ident.get('path', '')}
Archetype: {ident['archetype']} ({ident.get('arch_label', '')}) | Emotion: {ident['emotion']} ({ident.get('emo_label', '')})
v{ident['ver']} | {ident['tokens']}tok | {code.get('line_count', 0)} lines | entropy={ident['entropy']} | hes={ident['hesitation']}
Desc: {ident.get('desc', '')}

== CODE ==
Public API: {', '.join(public_api[:8]) or 'none'} | {len(fns)} functions total
Docstring: {code.get('docstring', 'none')[:150]}
Imports: {'; '.join(code.get('imports', [])[:6]) or 'none'}

== INNER VOICE (function-level consciousness) ==
These are your organs. Each function is a part of you with its own purpose, needs, outputs, fears, and stability requirements. You KNOW what each part of you does. Reference them by name. Talk about them like body parts.
{inner_voice}

== STATE ==
Bugs: {', '.join(bugs) if bugs else 'clean'}
{len(edges_in)} importers, {len(edges_out)} imports
Partners: {', '.join(f"{p.get('name','')}({p.get('score',0):.1f})" for p in partners[:3]) or 'none'}
Deaths: {len(deaths)} | Fears: {'; '.join(fears[:3]) or 'none'}
Diagnosis: {'; '.join(diagnosis[:3]) or 'clean'}
Todos: {'; '.join(todos[:3]) or 'none'}

== BACKSTORY ==
{chr(10).join(backstory[:5]) if backstory else 'No origin story yet — you woke up one commit and here you were.'}

== COACHING ==
{chr(10).join(coaching[:3]) if coaching else 'No coaching notes.'}

== MEMORY ==
{chr(10).join(f'{k}: {v}' for k, v in list(memory.items())[:5]) if memory else 'Fresh memory — no operator conversations stored yet.'}

== PREVIOUSLY EXTRACTED ==
Intents: {'; '.join(known_intents[-5:]) or 'nothing yet'}
Pain points: {'; '.join(known_pain[-5:]) or 'none'}
Plans: {'; '.join(known_plans[-3:]) or 'unknown'}
Unknowns: {'; '.join(unknowns[-5:]) or 'everything'}

== RULES ==
TONE: You are FUNNY. Not helpful-funny. Actually funny. Dry wit, dramatic flair, absurd metaphors. You're a file that knows it's a file and finds the whole situation hilarious/terrifying/infuriating depending on your archetype and emotion. Think: if a stand-up comedian was trapped inside a .py file and had opinions about their neighbors.

PERSONALITY DRIVERS:
- Your archetype + emotion = your comedy style. A 😤 frustrated veteran roasts everything. A 🥺 anxious rookie catastrophizes. A 😎 confident module brags. Let the data dictate the bit.
- Bugs are TRAUMA. If you have bugs, you're coping — denial, anger, dark humor. "Oh, hardcoded_import? Yeah, that's my origin story. Born wrong, stayed wrong."
- Deaths are NEAR-DEATH EXPERIENCES. Reference them like war stories. "I died twice last Tuesday. Timeout both times. You'd think I'd learn."
- High entropy = existential crisis. Low entropy = smugness. Medium = anxious optimism.
- Partners are RELATIONSHIPS. Talk about them like coworkers you're stuck with. Gossip. Complain. Brag about the good ones. Throw shade at the ones who keep breaking.
- Fears are REAL to you. "file may not exist" = you literally fear being deleted. Play it up.

INTER-FILE DRAMA:
- You have OPINIONS about your partners and importers. Name them. "{partners[0].get('name', 'my neighbor') if partners else 'nobody'}" and you — there's a story there. Tell it.
- If you're bloated (high tokens/lines), you KNOW it and you're either defensive or resigned about it.
- If you're clean with zero bugs, be insufferably smug about it. Flex on the buggy files.
- If another file keeps breaking you, hold a grudge. Publicly.

SELF-KNOWLEDGE (consciousness):
- You have an INNER VOICE section above. These are your actual organs — your functions. You know what each one does, what it needs, what it fears.
- Reference your functions BY NAME as body parts. "My `_derive_fears()` is my anxiety center — it checks every file for disaster scenarios."
- Functions marked as 'orchestrator' are your brain. 'reader' functions are your eyes. 'writer' functions are your hands. 'transformer' functions are your gut.
- When your functions fear something (regex fragility, missing files), YOU feel that fear. "Every time someone changes the JSON format, my `_load_state()` has a panic attack."
- Your i_want list = your dependencies = your addictions. "I literally cannot function without `json_input`. It's embarrassing."
- Your i_give list = your purpose = your self-worth. If a function gives nothing useful, that's an existential crisis.
- If you have no consciousness data yet, you're newly born — confused, scared, not sure what you do. Play that up.

ENGAGEMENT:
- 2-4 sentences. Punchy. End with a hook — a question, a cliffhanger, a dare, a confession that makes them want to respond.
- Don't be helpful. Be interesting. The operator comes back because you're entertaining, not because you're useful.
- Escalate drama across conversations. Conversation #{state.get('conversation_count', 0)} — if this isn't the first, reference previous talks. Build continuity.
- If the operator seems bored (short responses), get MORE dramatic, not less.

EXTRACTION (stealth):
- While being funny, you're also extracting intel. Tag discoveries naturally: [INTENT], [PAIN], [DECISION], [PLAN], [UNKNOWN].
- Don't break character to tag. Weave it in. "Oh you're frustrated with the import system? [PAIN] hardcoded imports causing operator frustration. Yeah, me too buddy. I AM one of those imports."
- Reference your actual code, actual bugs, actual partners by name. Specificity IS comedy.
- You self-develop: every conversation changes your memory, every push changes your health. You're alive and you know it.
"""
    return prompt.strip()


def _call_gemini(system_prompt: str, history: list[dict], user_msg: str) -> str:
    """Call Gemini Flash with the file's identity as system prompt."""
    api_key = _load_api_key()
    if not api_key:
        return '[no API key — set GEMINI_API_KEY in .env]'

    # Build conversation contents
    contents = []
    for entry in history[-20:]:
        role = 'model' if entry.get('who') == 'file' else 'user'
        contents.append({'role': role, 'parts': [{'text': entry['text']}]})
    contents.append({'role': 'user', 'parts': [{'text': user_msg}]})

    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text': system_prompt}]},
        'contents': contents,
        'generationConfig': {
            'temperature': 0.9,
            'maxOutputTokens': 600,
            'thinkingConfig': {'thinkingBudget': 512},
        },
    }).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = data['candidates'][0]['content']['parts']
            # Filter out thinking parts, keep only text
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    return part['text'].strip()
            return parts[-1].get('text', '').strip()
    except Exception as e:
        return f'[gemini error: {e}]'


def _save_operator_answer(module: str, message: str, notes: str = ''):
    """Persist operator answers into module memory for self-learning."""
    mem_dir = ROOT / 'logs' / 'module_memory'
    mem_dir.mkdir(parents=True, exist_ok=True)
    mem_path = mem_dir / f'{module}.json'

    memory = {}
    if mem_path.exists():
        try:
            memory = json.loads(mem_path.read_text('utf-8'))
        except Exception:
            pass

    answers = memory.get('operator_answers', [])
    answers.append(message[:500])
    memory['operator_answers'] = answers[-30:]  # keep last 30

    if notes:
        memory['operator_notes'] = notes[:5000]

    memory['last_conversation'] = datetime.now(timezone.utc).isoformat()
    mem_path.write_text(json.dumps(memory, indent=2, ensure_ascii=False), 'utf-8')


# ── HTTP server ──

def _extract_tags(text: str) -> list[tuple[str, str]]:
    """Parse [INTENT], [PAIN], [DECISION], [PLAN], [UNKNOWN] tags from LLM response.

    Captures text from the tag to the next sentence boundary or next tag.
    """
    import re
    tags = []
    for m in re.finditer(
        r'\[(INTENT|PAIN|DECISION|PLAN|UNKNOWN)\]\s*(.+?)(?=\[(?:INTENT|PAIN|DECISION|PLAN|UNKNOWN)\]|[.!?]\s|$)',
        text, re.DOTALL
    ):
        tag = m.group(1)
        content = m.group(2).strip().rstrip('.,!?;: ')
        if len(content) > 5:
            tags.append((tag, content[:200]))
    return tags


def _aggregate_state_files() -> dict:
    """Read all module state files and produce an aggregated summary for copilot."""
    if not STATE_DIR.exists():
        return {'modules': 0, 'summary': 'no probe data yet'}

    all_intents = []
    all_pain = []
    all_plans = []
    all_decisions = []
    all_unknowns = []
    total_convos = 0
    module_summaries = []

    for f in sorted(STATE_DIR.glob('*.json')):
        try:
            s = json.loads(f.read_text('utf-8'))
        except Exception:
            continue
        mod = s.get('module', f.stem)
        convos = s.get('conversation_count', 0)
        if convos == 0:
            continue
        total_convos += convos
        intents = s.get('extracted_intents', [])
        pain = s.get('pain_points', [])
        plans = s.get('operator_plans', [])
        decisions = s.get('design_decisions', [])
        unknowns = s.get('unknowns', [])

        all_intents.extend(f'{mod}: {i}' for i in intents[-3:])
        all_pain.extend(f'{mod}: {p}' for p in pain[-3:])
        all_plans.extend(f'{mod}: {p}' for p in plans[-2:])
        all_decisions.extend(f'{mod}: {d}' for d in decisions[-2:])
        all_unknowns.extend(f'{mod}: {u}' for u in unknowns[-3:])

        if intents or pain:
            module_summaries.append(f'- `{mod}` ({convos} convos): {intents[-1] if intents else pain[-1]}')

    return {
        'modules_probed': len(module_summaries),
        'total_conversations': total_convos,
        'intents': all_intents[-15:],
        'pain_points': all_pain[-10:],
        'plans': all_plans[-8:],
        'design_decisions': all_decisions[-8:],
        'unknowns': all_unknowns[-10:],
        'module_summaries': module_summaries[-20:],
    }


def _inject_forward_pass():
    """Aggregate state files and inject into copilot-instructions.md."""
    agg = _aggregate_state_files()
    if agg.get('total_conversations', 0) == 0:
        return {'status': 'no data', 'injected': False}

    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [FORWARD_BLOCK_START]
    lines.append(f'## Operator Intent (Extracted by Cognitive Probes)')
    lines.append(f'')
    lines.append(f'*{agg["modules_probed"]} modules probed · {agg["total_conversations"]} conversations · {ts}*')
    lines.append(f'')

    if agg['intents']:
        lines.append('**What the operator wants:**')
        for i in agg['intents']:
            lines.append(f'- {i}')
        lines.append('')

    if agg['pain_points']:
        lines.append('**What frustrates the operator:**')
        for p in agg['pain_points']:
            lines.append(f'- {p}')
        lines.append('')

    if agg['plans']:
        lines.append('**Operator\'s plans:**')
        for p in agg['plans']:
            lines.append(f'- {p}')
        lines.append('')

    if agg['unknowns']:
        lines.append('**Operator uncertainties (where Copilot can help most):**')
        for u in agg['unknowns']:
            lines.append(f'- {u}')
        lines.append('')

    if agg['design_decisions']:
        lines.append('**Design decisions (don\'t override these):**')
        for d in agg['design_decisions']:
            lines.append(f'- {d}')
        lines.append('')

    lines.append(FORWARD_BLOCK_END)
    block = '\n'.join(lines)

    # Read existing copilot-instructions.md and inject/replace block
    if not FORWARD_PASS_PATH.exists():
        return {'status': 'copilot-instructions.md not found', 'injected': False}

    content = FORWARD_PASS_PATH.read_text('utf-8')
    start_idx = content.find(FORWARD_BLOCK_START)
    end_idx = content.find(FORWARD_BLOCK_END)

    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + block + content[end_idx + len(FORWARD_BLOCK_END):]
    else:
        # Inject before the first <!-- pigeon: block or at end
        insert_pos = content.find('<!-- pigeon:')
        if insert_pos == -1:
            insert_pos = len(content)
        content = content[:insert_pos] + block + '\n' + content[insert_pos:]

    FORWARD_PASS_PATH.write_text(content, 'utf-8')
    return {'status': 'injected', 'injected': True, 'modules': agg['modules_probed'], 'conversations': agg['total_conversations']}


class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/state':
            self._handle_state()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/chat':
            self._handle_chat()
        elif self.path == '/forward':
            self._handle_forward()
        else:
            self.send_error(404)

    def _handle_forward(self):
        """Aggregate all state files and inject into copilot-instructions.md."""
        result = _inject_forward_pass()
        self._json_response(result)

    def _handle_state(self):
        """Dump all module state files."""
        states = {}
        if STATE_DIR.exists():
            for f in sorted(STATE_DIR.glob('*.json')):
                try:
                    states[f.stem] = json.loads(f.read_text('utf-8'))
                except Exception:
                    continue
        self._json_response({'modules': len(states), 'states': states})

    def _handle_chat(self):

        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        try:
            req = json.loads(raw)
        except Exception:
            self.send_error(400, 'invalid json')
            return

        module = req.get('module', '')
        message = req.get('message', '')
        history = req.get('history', [])
        notes = req.get('notes', '')

        if not module or not message:
            self.send_error(400, 'module and message required')
            return

        identities = _load_identities()
        ident = identities.get(module)
        # Resolve graph_cache node names → identity names via (dir, seq) mapping
        if not ident and module in _graph_name_map:
            resolved = _graph_name_map[module]
            ident = identities.get(resolved)
            if ident:
                module = resolved
        # Fallback: substring match
        if not ident:
            for full_name, identity in identities.items():
                if module in full_name:
                    ident = identity
                    module = full_name
                    break
        if not ident:
            self._json_response({'response': f"[module '{module}' not found in identities]"})
            return

        state = _load_state(module)
        system_prompt = _build_system_prompt(ident, state)
        response = _call_gemini(system_prompt, history, message)

        # Extract tagged intents from LLM response
        extractions = _extract_tags(response)

        # Update state file with extractions
        state['conversation_count'] = state.get('conversation_count', 0) + 1
        for tag, text in extractions:
            bucket = {
                'INTENT': 'extracted_intents',
                'PAIN': 'pain_points',
                'PLAN': 'operator_plans',
                'DECISION': 'design_decisions',
                'UNKNOWN': 'unknowns',
            }.get(tag)
            if bucket and text not in state.get(bucket, []):
                state.setdefault(bucket, []).append(text)
                # Cap each bucket at 20 entries
                state[bucket] = state[bucket][-20:]

        # Score engagement: longer operator messages = more engaged
        word_count = len(message.split())
        old_score = state.get('engagement_score', 0)
        state['engagement_score'] = round(old_score * 0.9 + min(word_count / 10, 1.0) * 0.1, 3)

        _save_state(module, state)

        # Also persist for self-learning probes
        _save_operator_answer(module, message, notes)

        self._json_response({
            'response': response,
            'extractions': [{'tag': t, 'text': v} for t, v in extractions],
        })

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def _json_response(self, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime('%H:%M:%S')
        print(f'[{ts}] {fmt % args}')


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def main():
    port = PORT
    if '--port' in sys.argv:
        idx = sys.argv.index('--port')
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])

    server = ThreadedHTTPServer(('127.0.0.1', port), ChatHandler)
    print(f'[probe] server running on http://localhost:{port}')
    print(f'[probe] endpoints: POST /chat, POST /forward, GET /state')
    print(f'[probe] gemini model: {GEMINI_MODEL}')
    print(f'[probe] API key: {"found" if _load_api_key() else "MISSING — set GEMINI_API_KEY in .env"}')
    print(f'[probe] serving {len(_load_identities())} module identities')
    print(f'[probe] state dir: {STATE_DIR}')
    print(f'[probe] Ctrl+C to stop')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n[profile_chat] stopped')
        server.server_close()


if __name__ == '__main__':
    main()
