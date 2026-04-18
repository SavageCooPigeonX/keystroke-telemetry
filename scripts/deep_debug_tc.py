"""Deep debug pass on thought_completer.

Trace end-to-end: params, prompt length, raw Gemini response, finish_reason,
parts count, echo-strip behavior, training trigger.
"""
import sys, json, urllib.request
from pathlib import Path
sys.path.insert(0, '.')

from src.tc_grader_seq001_v001_seq001_v001 import compute_adaptive_params
from src.tc_gemini_seq001_v001_seq001_v001 import _load_api_key, SYSTEM_PROMPT, _build_user_prompt, _strip_signal_echo, _is_buffer_echo
from src.tc_constants_seq001_v001_seq001_v001 import GEMINI_MODEL, GEMINI_TIMEOUT
from src.tc_context_seq001_v001_seq001_v001 import load_context
from src.tc_context_seq001_v001_seq001_v001_agent_seq001_v001_seq001_v001 import select_context_ensemble
from src.tc_trajectory_seq001_v001_seq001_v001 import build_trajectory

print('=' * 70)
print('DEEP DEBUG PASS — thought_completer')
print('=' * 70)

# 1. Params
params = compute_adaptive_params()
print(f'\n[1] ADAPTIVE PARAMS')
print(f'  {params}')

# Check grade summary
gs = Path('logs/completion_grade_summary.json')
if gs.exists():
    summary = json.loads(gs.read_text('utf-8'))
    r50 = summary.get('recent_50', {})
    lp = summary.get('length_profile', {})
    print(f'  recent_50: relevance={r50.get("avg_relevance", 0):.3f} echo={r50.get("avg_echo", 0):.3f} accept_rate={r50.get("accept_rate", 0):.3f}')
    print(f'  length_profile: accepted_avg={lp.get("accepted_avg", 0)} rejected_avg={lp.get("rejected_avg", 0)}')
    print(f'  total_graded: {summary.get("total_graded", 0)}')
    print(f'  trend: {summary.get("trend", {})}')

# 2. Build full prompt for a real buffer
api_key = _load_api_key()
print(f'\n[2] API KEY: {"present" if api_key else "MISSING"} (len={len(api_key) if api_key else 0})')

buf = "write a joke about a python developer who renames his files compulsively"
ctx = load_context()
trajectory = build_trajectory()
selected_files = select_context_ensemble(buf, ctx)
user_prompt = _build_user_prompt(buf, ctx, thought_buffer=None,
                                 code_ctx='', trajectory=trajectory,
                                 selected_files=selected_files)

print(f'\n[3] PROMPT SIZES')
print(f'  SYSTEM_PROMPT: {len(SYSTEM_PROMPT)} chars (~{len(SYSTEM_PROMPT)//4} tokens)')
print(f'  user_prompt  : {len(user_prompt)} chars (~{len(user_prompt)//4} tokens)')
print(f'  TOTAL in    : ~{(len(SYSTEM_PROMPT)+len(user_prompt))//4} tokens')
print(f'  maxOutputTokens: {params["maxOutputTokens"]}')

print(f'\n[4] USER PROMPT (first 400 chars):')
print('    ' + user_prompt[:400].replace('\n', '\n    '))
print('    ...')
print(f'\n[4b] USER PROMPT (last 200 chars):')
print('    ' + user_prompt[-200:].replace('\n', '\n    '))

# 3. RAW Gemini call — capture the full response
print(f'\n[5] RAW GEMINI CALL')
url = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}'
body = json.dumps({
    'system_instruction': {'parts': [{'text': SYSTEM_PROMPT}]},
    'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
    'generationConfig': {
        'temperature': params['temperature'],
        'maxOutputTokens': params['maxOutputTokens'],
        'topP': params['topP'],
        'thinkingConfig': {'thinkingBudget': 0},
    },
}).encode('utf-8')

try:
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
        data = json.loads(resp.read().decode('utf-8'))
except Exception as e:
    print(f'  ERROR: {e}')
    sys.exit(1)

# Dump the full response structure
print(f'\n[6] RAW RESPONSE STRUCTURE')
print(f'  top-level keys: {list(data.keys())}')
candidates = data.get('candidates', [])
print(f'  candidates: {len(candidates)}')
if candidates:
    c0 = candidates[0]
    print(f'  candidate[0] keys: {list(c0.keys())}')
    print(f'  finishReason: {c0.get("finishReason")}')
    print(f'  avgLogprobs: {c0.get("avgLogprobs")}')
    content = c0.get('content', {})
    parts = content.get('parts', [])
    print(f'  parts: {len(parts)}')
    for i, p in enumerate(parts):
        keys = list(p.keys())
        has_thought = 'thought' in p
        text_len = len(p.get('text', ''))
        print(f'    part[{i}]: keys={keys} thought={has_thought} text_len={text_len}')
        if 'text' in p:
            preview = p['text'][:200].replace('\n', '\\n')
            print(f'       text: "{preview}"')

um = data.get('usageMetadata', {})
print(f'  usageMetadata: prompt={um.get("promptTokenCount")} output={um.get("candidatesTokenCount")} thought={um.get("thoughtsTokenCount")} total={um.get("totalTokenCount")}')

# 7. Simulate the extraction logic from tc_gemini_seq001_v001
print(f'\n[7] EXTRACTION LOGIC (mirrors tc_gemini_seq001_v001)')
text = ''
if candidates:
    parts = candidates[0].get('content', {}).get('parts', [])
    for part in parts:
        if 'text' in part and 'thought' not in part:
            text = part['text'].strip()
            break
    if not text and parts:
        text = parts[-1].get('text', '').strip()
print(f'  raw text (pre-strip): "{text[:200]}" (len={len(text)})')

stripped = _strip_signal_echo(text, buf)
print(f'  after _strip_signal_echo: "{stripped[:200]}" (len={len(stripped)})')

is_echo = _is_buffer_echo(stripped, buf)
print(f'  _is_buffer_echo: {is_echo}')

print('\n' + '=' * 70)
print('DIAGNOSIS')
print('=' * 70)
if um.get('thoughtsTokenCount', 0) > 0:
    print(f'⚠ Model is using {um["thoughtsTokenCount"]} THINKING tokens — this is Gemini 2.5 reasoning mode.')
    print('  Thinking eats the output budget. If maxOutputTokens is too low, actual text gets truncated.')
if candidates and candidates[0].get('finishReason') == 'MAX_TOKENS':
    print('⚠ Finished due to MAX_TOKENS — completion was cut off mid-generation.')
if len(text) < 50:
    print(f'⚠ Output is very short ({len(text)} chars). Check finishReason + thinking budget.')
