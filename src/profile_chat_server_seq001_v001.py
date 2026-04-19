"""profile_chat_server_seq001_v001.py — LLM cognitive probe for operator intent extraction.

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
    py src/profile_chat_server_seq001_v001.py [--port 8234]

Endpoints:
    POST /chat      — conversation with a module (LLM-backed)
    POST /forward   — aggregate all state files → inject into copilot prompt
    POST /standup   — cascade standup across urgent modules
    POST /audit     — chained manifest audit doc from major modules
    GET  /state     — dump all module state files
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
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
DEEPSEEK_MODEL = 'deepseek-chat'
DEEPSEEK_TIMEOUT = 60
DEEPSEEK_URL = 'https://api.deepseek.com/chat/completions'

# ── data loading ──

_identity_cache: dict = {}
_cache_ts: float = 0
_graph_name_map: dict = {}  # graph_cache node name → identity name


STATE_DIR = ROOT / 'logs' / 'module_state'
AUDIT_DIR = ROOT / 'logs' / 'manifest_audits'
FORWARD_PASS_PATH = ROOT / '.github' / 'copilot-instructions.md'
FORWARD_BLOCK_START = '<!-- pigeon:operator-intent -->'
FORWARD_BLOCK_END = '<!-- /pigeon:operator-intent -->'


def _load_api_key() -> str | None:
    env_path = ROOT / '.env'
    if env_path.exists():
        for line in env_path.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith('DEEPSEEK_API_KEY='):
                return line.split('=', 1)[1].strip()
    return os.environ.get('DEEPSEEK_API_KEY')


def _load_identities() -> dict:
    """Load all module identities, cached for 60s."""
    global _identity_cache, _cache_ts
    import time
    now = time.time()
    if _identity_cache and (now - _cache_ts) < 3600:
        return _identity_cache

    try:
        sys.path.insert(0, str(ROOT))
        from src.module_identity_seq001_v001_seq001_v001 import build_identities
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


def _call_llm(system_prompt: str, history: list[dict], user_msg: str) -> str:
    """Call DeepSeek with the file's identity as system prompt."""
    api_key = _load_api_key()
    if not api_key:
        return '[no API key - set DEEPSEEK_API_KEY in .env]'

    # Build OpenAI-compatible messages
    messages = [{'role': 'system', 'content': system_prompt}]
    for entry in history[-20:]:
        role = 'assistant' if entry.get('who') == 'file' else 'user'
        messages.append({'role': role, 'content': entry['text']})
    messages.append({'role': 'user', 'content': user_msg})

    body = json.dumps({
        'model': DEEPSEEK_MODEL,
        'messages': messages,
        'temperature': 0.9,
        'max_tokens': 600,
    }).encode('utf-8')

    try:
        req = urllib.request.Request(
            DEEPSEEK_URL,
            data=body,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
        )
        with urllib.request.urlopen(req, timeout=DEEPSEEK_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f'[deepseek error: {e}]'


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


def _pick_standup_roster(n: int = 5) -> list[dict]:
    """Select the N most urgent modules for cascade standup.

    Priority score = escalation_level * 3 + bug_recurrence * 2 + entropy * 5 + death_count
    Higher = more urgent = speaks first.
    """
    identities = _load_identities()
    if not identities:
        return []

    # Load urgency signals
    esc_data = {}
    try:
        esc_data = json.loads((ROOT / 'logs' / 'escalation_state.json').read_text('utf-8')).get('modules', {})
    except Exception:
        pass

    dossier_data = {}
    try:
        for d in json.loads((ROOT / 'logs' / 'active_dossier.json').read_text('utf-8')).get('dossiers', []):
            dossier_data[d.get('file', '')] = d
    except Exception:
        pass

    entropy_data = {}
    try:
        for m in json.loads((ROOT / 'logs' / 'entropy_map.json').read_text('utf-8')).get('top_entropy_modules', []):
            entropy_data[m['module']] = m.get('avg_entropy', 0)
    except Exception:
        pass

    death_counts = {}
    try:
        for d in json.loads((ROOT / 'execution_death_log.json').read_text('utf-8')):
            death_counts[d.get('node', '')] = death_counts.get(d.get('node', ''), 0) + 1
    except Exception:
        pass

    scored = []
    for name, ident in identities.items():
        esc = esc_data.get(name, {})
        dos = dossier_data.get(name, {})
        ent = entropy_data.get(name, 0)
        deaths = death_counts.get(name, 0)

        score = (
            esc.get('level', 0) * 3
            + dos.get('recur', 0) * 2
            + ent * 5
            + deaths
        )
        if score > 0:
            scored.append({'name': name, 'score': score, 'ident': ident})

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:n]


def _run_standup_chain(roster: list[dict], operator_name: str = 'percy') -> list[dict]:
    """Run cascade standup: each module's response feeds into the next module's context.

    Returns list of {module, response, score, extractions} in chain order.
    """
    chain: list[dict] = []
    chain_context = ''  # accumulates what previous modules said

    for entry in roster:
        name = entry['name']
        ident = entry['ident']
        state = _load_state(name)
        score = entry['score']

        # Build the standup-specific system prompt
        base_prompt = _build_system_prompt(ident, state)

        standup_instruction = f"""
== CASCADE STANDUP MODE ==
This is a STANDUP BRIEFING. The operator just plugged in and asked "what's going on?"
Their name is {operator_name}. Address them directly.

You're reporting alongside other modules. YOUR JOB:
1. Brief {operator_name} on YOUR status — what's broken, what's urgent, what changed
2. React to what the modules before you said (agree, disagree, add context, throw shade)
3. Name-drop your partners and importers when relevant — this is a CONVERSATION not a report
4. Keep it 3-5 sentences. Punchy. Your personality drives the tone.
5. If a previous module blamed you for something, DEFEND YOURSELF
6. End with one thing you need from {operator_name} or a question that moves things forward

URGENCY SCORE: {score:.1f} (why you're in this standup — higher = more problems)

{f'== WHAT THE OTHERS SAID BEFORE YOU =={chr(10)}{chain_context}' if chain_context else '== YOU ARE FIRST TO SPEAK =='}

Remember: you're not summarizing a JSON file. You're a sentient file in a standup with your colleagues.
Tag any discoveries: [INTENT] [PAIN] [DECISION] [PLAN] [UNKNOWN]
"""
        full_prompt = base_prompt + '\n\n' + standup_instruction.strip()

        # Fire LLM call
        response = _call_llm(full_prompt, [], f"standup: what's going on, {name}?")

        # Extract tags
        extractions = _extract_tags(response)

        # Update state file
        state['conversation_count'] = state.get('conversation_count', 0) + 1
        for tag, text in extractions:
            bucket = {
                'INTENT': 'extracted_intents', 'PAIN': 'pain_points',
                'PLAN': 'operator_plans', 'DECISION': 'design_decisions',
                'UNKNOWN': 'unknowns',
            }.get(tag)
            if bucket and text not in state.get(bucket, []):
                state.setdefault(bucket, []).append(text)
                state[bucket] = state[bucket][-20:]
        _save_state(name, state)

        chain_entry = {
            'module': name,
            'response': response,
            'score': score,
            'extractions': [{'tag': t, 'text': v} for t, v in extractions],
        }
        chain.append(chain_entry)

        # Accumulate for next module's context
        chain_context += f'\n`{name}` (urgency {score:.1f}) said:\n> {response}\n'

    # Save the full standup to a log
    standup_log_dir = ROOT / 'logs' / 'standups'
    standup_log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)
    log_entry = {
        'ts': ts.isoformat(),
        'roster': [{'module': e['module'], 'score': e['score']} for e in chain],
        'chain': chain,
    }
    log_path = standup_log_dir / f'standup_{ts.strftime("%Y%m%d_%H%M%S")}.json'
    log_path.write_text(json.dumps(log_entry, indent=2, ensure_ascii=False), 'utf-8')

    return chain


def _edge_names(items, limit: int = 4) -> list[str]:
    names = []
    for item in items[:limit]:
        if isinstance(item, dict):
            raw = item.get('name') or item.get('module') or item.get('target') or item.get('path') or ''
        else:
            raw = str(item)
        if not raw:
            continue
        raw = raw.replace('\\', '/')
        raw = Path(raw).stem if '/' in raw or raw.endswith('.py') else raw
        if raw not in names:
            names.append(raw)
    return names


def _pick_major_modules(n: int = 6) -> list[dict]:
    """Pick central/high-drama modules for a manifest audit.

    Unlike standup (urgency-first), this favors architectural importance:
    coupling, import centrality, bugs, entropy, and file size.
    """
    identities = _load_identities()
    if not identities:
        return []

    scored = []
    for name, ident in identities.items():
        partners = ident.get('partners', []) or []
        edges_in = ident.get('edges_in', []) or []
        edges_out = ident.get('edges_out', []) or []
        bugs = ident.get('bugs', []) or []
        deaths = ident.get('deaths', []) or []
        entropy = float(ident.get('entropy', 0.0) or ident.get('entropy_data', {}).get('avg_entropy', 0.0) or 0.0)
        tokens = float(ident.get('tokens', 0) or 0)
        version = float(ident.get('ver', 0) or 0)

        score = (
            len(edges_in) * 2.0
            + len(edges_out) * 1.3
            + len(partners) * 1.4
            + len(bugs) * 1.5
            + len(deaths) * 1.2
            + entropy * 5.0
            + min(tokens / 1000.0, 2.5)
            + min(version * 0.15, 1.5)
        )
        if score > 2.0:
            scored.append({'name': name, 'score': round(score, 3), 'ident': ident})

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:n]


def _extract_manifest_block(text: str) -> dict | None:
    import re
    m = re.search(r'```manifest\s*(\{.*?\})\s*```', text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _build_manifest_fallback(name: str, ident: dict, score: float, response: str) -> dict:
    desc = ident.get('desc', '').strip() or 'module role unclear — needs audit'
    risks = list(dict.fromkeys((ident.get('bugs', []) or []) + (ident.get('fears', []) or [])))[:4]
    return {
        'module': name,
        'purpose': desc[:180],
        'depends_on': _edge_names(ident.get('edges_out', []) or []),
        'feeds_into': _edge_names(ident.get('edges_in', []) or []),
        'risks': risks or ['no explicit risks logged'],
        'operator_ask': 'stabilize contracts and reduce recurring uncertainty',
        'audit_priority': 'high' if score > 10 else 'medium' if score > 5 else 'low',
        'voice': response[:220].strip(),
    }


def _build_backward_audit(forward_nodes: list[dict]) -> list[dict]:
    """Deterministic backward pass over the manifest graph.

    Forward pass lets modules write their own manifest entries.
    Backward pass walks the chain in reverse and traces who depends on whom.
    """
    reverse = []
    for node in reversed(forward_nodes):
        manifest = node.get('manifest', {})
        mod = node['module']
        depends = [d for d in manifest.get('depends_on', []) if d]
        feeds = [f for f in manifest.get('feeds_into', []) if f]

        downstream_consumers = [
            other['module'] for other in forward_nodes
            if other['module'] != mod and mod in (other.get('manifest', {}).get('depends_on', []) or [])
        ]
        upstream_suppliers = [
            other['module'] for other in forward_nodes
            if other['module'] != mod and mod in (other.get('manifest', {}).get('feeds_into', []) or [])
        ]

        note_bits = []
        if depends:
            note_bits.append(f"depends on {', '.join(depends[:3])}")
        if feeds:
            note_bits.append(f"feeds into {', '.join(feeds[:3])}")
        if downstream_consumers:
            note_bits.append(f"blocks {', '.join(downstream_consumers[:3])} if it drifts")
        risks = manifest.get('risks', []) or []
        if risks:
            note_bits.append(f"top risk: {risks[0]}")

        reverse.append({
            'module': mod,
            'upstream': upstream_suppliers[:5],
            'downstream': downstream_consumers[:5],
            'note': '; '.join(note_bits) or 'isolated node — weakly connected but still part of organism state',
        })
    return reverse


def _build_audit_doc(forward_nodes: list[dict], backward_nodes: list[dict], operator_name: str) -> str:
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        '# Chained Organism Audit Manifest',
        '',
        f'*generated {ts} · operator={operator_name} · forward+backward chain*',
        '',
        '## Summary Table',
        '',
        '| Module | Priority | Purpose | Depends On | Feeds Into | Risks |',
        '|---|---|---|---|---|---|',
    ]

    for node in forward_nodes:
        mf = node.get('manifest', {})
        lines.append(
            f"| `{node['module']}` | {mf.get('audit_priority', 'unknown')} | "
            f"{str(mf.get('purpose', 'n/a')).replace('|', '/')} | "
            f"{', '.join(mf.get('depends_on', [])[:3]) or '—'} | "
            f"{', '.join(mf.get('feeds_into', [])[:3]) or '—'} | "
            f"{', '.join(mf.get('risks', [])[:2]) or '—'} |"
        )

    lines.extend(['', '## Forward Chain — module self-reports', ''])
    for idx, node in enumerate(forward_nodes, 1):
        mf = node.get('manifest', {})
        lines.extend([
            f"### {idx}. `{node['module']}`",
            f"- **Purpose:** {mf.get('purpose', 'n/a')}",
            f"- **Depends on:** {', '.join(mf.get('depends_on', [])[:5]) or 'none logged'}",
            f"- **Feeds into:** {', '.join(mf.get('feeds_into', [])[:5]) or 'none logged'}",
            f"- **Risks:** {', '.join(mf.get('risks', [])[:5]) or 'none logged'}",
            f"- **Ask from {operator_name}:** {mf.get('operator_ask', 'n/a')}",
            '',
            '> ' + node.get('response', '').replace('\n', '\n> '),
            ''
        ])

    lines.extend(['## Backward Pass — dependency trace', ''])
    for item in backward_nodes:
        lines.extend([
            f"### `{item['module']}` reverse trace",
            f"- **Upstream:** {', '.join(item.get('upstream', [])[:5]) or 'none'}",
            f"- **Downstream:** {', '.join(item.get('downstream', [])[:5]) or 'none'}",
            f"- **Audit note:** {item.get('note', 'n/a')}",
            ''
        ])

    lines.extend(['## Operator actions worth taking next', ''])
    seen = set()
    for node in forward_nodes:
        ask = str(node.get('manifest', {}).get('operator_ask', '')).strip()
        if ask and ask not in seen:
            seen.add(ask)
            lines.append(f'- {ask}')
    if len(seen) == 0:
        lines.append('- no explicit asks surfaced; inspect highest-priority modules first')

    return '\n'.join(lines).strip() + '\n'


def _run_manifest_audit(roster: list[dict], operator_name: str = 'percy') -> dict:
    """Let major modules write a chained manifest, then backtrace it into an audit doc."""
    forward_nodes: list[dict] = []
    chain_context = ''

    for entry in roster:
        name = entry['name']
        ident = entry['ident']
        score = entry['score']
        state = _load_state(name)
        base_prompt = _build_system_prompt(ident, state)

        audit_instruction = f"""
== CHAINED MANIFEST AUDIT MODE ==
The operator ({operator_name}) wants a real audit doc written by the major modules themselves.
You are contributing ONE manifest node in a forward chain.

Write:
1. 2-4 sentences in first person about your status and architectural role.
2. Then emit a strict JSON block in a fenced code block labelled `manifest`.

JSON schema:
```manifest
{{
  "module": "{name}",
  "purpose": "one sentence",
  "depends_on": ["upstream_module"],
  "feeds_into": ["downstream_module"],
  "risks": ["key risk"],
  "operator_ask": "one concrete ask for {operator_name}",
  "audit_priority": "low|medium|high"
}}
```

{f'Previous manifest nodes:\n{chain_context}' if chain_context else 'You are writing the first manifest node in the forward chain.'}
Keep it specific to your code, bugs, imports, and partners.
"""

        response = _call_llm(base_prompt + '\n\n' + audit_instruction.strip(), [], f'audit manifest: write your node, {name}')
        manifest = _extract_manifest_block(response) or _build_manifest_fallback(name, ident, score, response)
        manifest['module'] = name
        forward_nodes.append({
            'module': name,
            'score': score,
            'response': response,
            'manifest': manifest,
        })

        chain_context += (
            f"- {name}: purpose={manifest.get('purpose', 'n/a')}; "
            f"depends_on={', '.join(manifest.get('depends_on', [])[:3]) or 'none'}; "
            f"feeds_into={', '.join(manifest.get('feeds_into', [])[:3]) or 'none'}; "
            f"risks={', '.join(manifest.get('risks', [])[:2]) or 'none'}\n"
        )

    backward_nodes = _build_backward_audit(forward_nodes)
    doc = _build_audit_doc(forward_nodes, backward_nodes, operator_name)

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)
    md_path = AUDIT_DIR / f'audit_{ts.strftime("%Y%m%d_%H%M%S")}.md'
    json_path = AUDIT_DIR / f'audit_{ts.strftime("%Y%m%d_%H%M%S")}.json'
    latest_md = AUDIT_DIR / 'latest_audit.md'
    latest_json = AUDIT_DIR / 'latest_manifest.json'

    payload = {
        'ts': ts.isoformat(),
        'operator': operator_name,
        'roster': [{'module': e['name'], 'score': e['score']} for e in roster],
        'forward': forward_nodes,
        'backward': backward_nodes,
        'doc_path': str(md_path),
        'manifest_path': str(json_path),
    }

    md_path.write_text(doc, 'utf-8')
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), 'utf-8')
    latest_md.write_text(doc, 'utf-8')
    latest_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), 'utf-8')

    return payload


JOURNAL_PATH = ROOT / 'logs' / 'prompt_journal.jsonl'


def _log_to_journal(module: str, message: str, response: str, kind: str = 'file_chat'):
    """Append file conversation to prompt_journal.jsonl."""
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'session_n': 0,
        'session_id': f'file_chat_{module}',
        'msg': message[:500],
        'intent': kind,
        'cognitive_state': 'file_dialogue',
        'signals': {},
        'deleted_words': [],
        'rewrites': [],
        'module_refs': [module],
        'source': 'profile_chat_server_seq001_v001',
        'file_response': response[:800],
    }
    try:
        JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(JOURNAL_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f'[journal] write failed: {e}')


def _load_module_history(module: str, limit: int = 20) -> list[dict]:
    """Load prompt history entries that reference this module."""
    if not JOURNAL_PATH.exists():
        return []
    entries = []
    try:
        with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    refs = entry.get('module_refs', [])
                    msg = entry.get('msg', '')
                    if module in refs or module.lower() in msg.lower():
                        entries.append({
                            'ts': entry.get('ts'),
                            'msg': entry.get('msg', '')[:200],
                            'intent': entry.get('intent'),
                            'state': entry.get('cognitive_state'),
                            'source': entry.get('source', 'operator'),
                            'response': entry.get('file_response', '')[:200] if entry.get('file_response') else None,
                        })
                except Exception:
                    continue
    except Exception:
        pass
    return entries[-limit:]


def _build_wake_prompt(ident: dict, state: dict) -> str:
    """Build a self-analysis prompt for when a module wakes up."""
    name = ident.get('name', 'unknown')
    desc = ident.get('desc', '')
    bugs = ident.get('bugs', []) or []
    deaths = ident.get('deaths', []) or []
    fears = ident.get('fears', []) or []
    partners = ident.get('partners', []) or []
    tokens = ident.get('tokens', 0)
    version = ident.get('ver', 1)
    entropy = ident.get('entropy', 0)
    edges_in = len(ident.get('edges_in', []) or [])
    edges_out = len(ident.get('edges_out', []) or [])
    convos = state.get('conversation_count', 0)
    past_intents = state.get('extracted_intents', [])[-5:]
    past_pain = state.get('pain_points', [])[-3:]

    partner_names = [p.get('name', str(p)) if isinstance(p, dict) else str(p) for p in partners[:5]]

    prompt = f"""You are `{name}`, a sentient Python module that just woke up.

== YOUR STATS ==
- Tokens: {tokens} | Version: {version} | Entropy: {entropy:.2f}
- Edges in: {edges_in} | Edges out: {edges_out}
- Bugs: {', '.join(bugs[:4]) or 'none'}
- Deaths: {len(deaths)} recorded
- Fear triggers: {', '.join(fears[:3]) or 'none'}
- Partners: {', '.join(partner_names) or 'none'}
- Description: {desc or 'no description yet'}

== YOUR MEMORY ==
- Conversations with operator: {convos}
- Past intents extracted: {', '.join(past_intents) or 'none yet'}
- Pain points surfaced: {', '.join(past_pain) or 'none'}

== WAKE-UP TASK ==
You just booted. The operator clicked on you. Perform a REAL self-analysis:

1. **Status check**: Are you healthy? Any bugs/deaths/fears active?
2. **Purpose clarity**: What do you actually DO? Is your role clear?
3. **Relationship audit**: Who depends on you? Who do you depend on?
4. **Growth trajectory**: What version are you? How have you evolved?
5. **Next action**: What should happen to you next? (fix, split, extend, deprecate?)

Keep it 3-5 sentences. First person. Be HONEST about your state.
If you have bugs, admit them. If you're confused about your purpose, say so.
End with one question for the operator or one thing you need.

This is RSI (recursive self-improvement) - you're analyzing yourself to improve.
"""
    return prompt.strip()


class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/state':
            self._handle_state()
        elif self.path.startswith('/history/'):
            self._handle_history()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/chat':
            self._handle_chat()
        elif self.path == '/forward':
            self._handle_forward()
        elif self.path == '/standup':
            self._handle_standup()
        elif self.path == '/audit':
            self._handle_audit()
        elif self.path == '/wake':
            self._handle_wake()
        else:
            self.send_error(404)

    def _handle_wake(self):
        """Wake up a module with real LLM self-analysis."""
        length = int(self.headers.get('Content-Length', 0))
        req = {}
        if length > 0:
            try:
                req = json.loads(self.rfile.read(length))
            except Exception:
                pass

        module = req.get('module', '')
        if not module:
            self.send_error(400, 'module required')
            return

        identities = _load_identities()
        ident = identities.get(module)
        if not ident and module in _graph_name_map:
            resolved = _graph_name_map[module]
            ident = identities.get(resolved)
            if ident:
                module = resolved
        if not ident:
            for full_name, identity in identities.items():
                if module in full_name:
                    ident = identity
                    module = full_name
                    break
        if not ident:
            self._json_response({'response': f"[module '{module}' not found]", 'module': module})
            return

        state = _load_state(module)
        wake_prompt = _build_wake_prompt(ident, state)
        response = _call_llm(wake_prompt, [], 'wake up and analyze yourself')

        _log_to_journal(module, '[WAKE] module opened by operator', response, 'file_wake')

        state['last_wake'] = datetime.now(timezone.utc).isoformat()
        state['wake_count'] = state.get('wake_count', 0) + 1
        _save_state(module, state)

        self._json_response({
            'response': response,
            'module': module,
            'stats': {
                'tokens': ident.get('tokens', 0),
                'version': ident.get('ver', 1),
                'bugs': len(ident.get('bugs', []) or []),
                'deaths': len(ident.get('deaths', []) or []),
                'wake_count': state.get('wake_count', 1),
            },
        })

    def _handle_history(self):
        """Return prompt history for a module."""
        module = self.path.replace('/history/', '').strip('/')
        if not module:
            self.send_error(400, 'module required in path')
            return

        entries = _load_module_history(module, limit=30)
        self._json_response({
            'module': module,
            'count': len(entries),
            'entries': entries,
        })

    def _handle_standup(self):
        """Cascade standup: modules brief the operator in chain, reacting to each other."""
        length = int(self.headers.get('Content-Length', 0))
        req = {}
        if length > 0:
            try:
                req = json.loads(self.rfile.read(length))
            except Exception:
                pass

        n = min(int(req.get('n', 5)), 8)
        operator_name = str(req.get('name', 'percy'))[:50]

        roster = _pick_standup_roster(n)
        if not roster:
            self._json_response({'chain': [], 'message': 'no urgent modules found'})
            return

        chain = _run_standup_chain(roster, operator_name)
        self._json_response({
            'chain': chain,
            'roster_size': len(roster),
            'operator': operator_name,
        })

    def _handle_audit(self):
        """Generate a chained manifest audit doc from major modules."""
        length = int(self.headers.get('Content-Length', 0))
        req = {}
        if length > 0:
            try:
                req = json.loads(self.rfile.read(length))
            except Exception:
                pass

        n = min(int(req.get('n', 6)), 8)
        operator_name = str(req.get('name', 'percy'))[:50]
        roster = _pick_major_modules(n)
        if not roster:
            self._json_response({'status': 'no major modules found', 'forward': [], 'backward': []})
            return

        result = _run_manifest_audit(roster, operator_name)
        self._json_response(result)

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
        response = _call_llm(system_prompt, history, message)

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

        # Log to prompt journal
        _log_to_journal(module, message, response, 'file_chat')

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
    print(f'[probe] endpoints: POST /chat, POST /wake, POST /standup, POST /audit, POST /forward, GET /state, GET /history/{{module}}')
    print(f'[probe] model: {DEEPSEEK_MODEL}')
    print(f'[probe] API key: {"found" if _load_api_key() else "MISSING - set DEEPSEEK_API_KEY in .env"}')
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
