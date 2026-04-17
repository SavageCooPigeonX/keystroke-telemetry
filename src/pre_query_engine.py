"""pre_query_engine.py -- Gemini-only thought completion engine.

Single LLM (Gemini Flash). Reads organism state from semantic filenames +
structured metadata. Completes thoughts on PAUSE. Sub-2s target.

Pluggable to any codebase -- auto-detects structured files via
codebase_detector. Accumulates unsaid threads over time via
unsaid_accumulator.

HTTP server on :8236 for VS Code extension. CLI for testing.
"""
from __future__ import annotations
import json
import os
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CASCADE_LOG = ROOT / 'logs' / 'cascade_events.jsonl'
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite')
GEMINI_TIMEOUT = 4


def _get_key(name: str) -> str:
    if v := os.environ.get(name):
        return v
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith(name + '='):
                return line.split('=', 1)[1].strip()
    return ''


@dataclass
class CompletionResult:
    fragment: str = ''
    completed_thought: str = ''
    analysis: str = ''
    suggested_action: str = ''
    confidence: float = 0.0
    selected_files: list = field(default_factory=list)
    scale: dict = field(default_factory=dict)
    total_ms: int = 0
    codebase_kind: str = 'generic'

    def to_dict(self) -> dict:
        return {
            'fragment': self.fragment,
            'completed_thought': self.completed_thought,
            'analysis': self.analysis,
            'suggested_action': self.suggested_action,
            'confidence': self.confidence,
            'selected_files': self.selected_files,
            'scale': self.scale,
            'total_ms': self.total_ms,
            'codebase_kind': self.codebase_kind,
        }


# -- context loading -----------------------------------------------------------

def _load_context() -> dict:
    ctx = {}
    jl = ROOT / 'logs' / 'prompt_journal.jsonl'
    if jl.exists():
        try:
            lines = jl.read_text('utf-8', errors='ignore').strip().split('\n')
            ctx['recent_prompts'] = [json.loads(l) for l in lines[-5:] if l.strip()]
        except Exception:
            pass
    tel = ROOT / 'logs' / 'prompt_telemetry_latest.json'
    if tel.exists():
        try:
            data = json.loads(tel.read_text('utf-8', errors='ignore'))
            ctx['hot_modules'] = data.get('hot_modules', [])
            sig = data.get('latest_prompt', {})
            ctx['cognitive'] = {
                'state': sig.get('state', 'unknown'),
                'intent': sig.get('intent', 'unknown'),
                'avg_wpm': data.get('running_summary', {}).get('avg_wpm', 50),
                'avg_del': data.get('running_summary', {}).get('avg_del_ratio', 0.25),
            }
        except Exception:
            pass
    recon = ROOT / 'logs' / 'unsaid_reconstructions.jsonl'
    if recon.exists():
        try:
            lines = recon.read_text('utf-8', errors='ignore').strip().split('\n')
            recent = [json.loads(l) for l in lines[-5:] if l.strip()]
            ctx['unsaid'] = [r.get('completed', r.get('fragment', ''))[:100] for r in recent]
        except Exception:
            pass
    sf = ROOT / 'logs' / 'self_fix_report.json'
    if sf.exists():
        try:
            data = json.loads(sf.read_text('utf-8', errors='ignore'))
            ctx['bugs'] = data.get('bugs', [])[:5]
        except Exception:
            pass
    return ctx


# -- Gemini Flash --------------------------------------------------------------

def _call_gemini(prompt: str, system: str = '', max_tokens: int = 400) -> str:
    api_key = _get_key('GEMINI_API_KEY') or _get_key('GOOGLE_API_KEY')
    if not api_key:
        return ''
    url = (
        f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}'
        f':generateContent?key={api_key}'
    )
    body = json.dumps({
        'system_instruction': {'parts': [{'text': system}]} if system else {},
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.3,
            'maxOutputTokens': max_tokens,
            'topP': 0.9,
            'responseMimeType': 'application/json',
        },
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            parts = data['candidates'][0]['content']['parts']
            for part in parts:
                if 'text' in part and 'thought' not in part:
                    return part['text'].strip()
            return parts[-1].get('text', '').strip()
    except Exception as e:
        print(f'[pre-query] gemini error: {e}')
        return ''


# -- dynamic system prompt (adapts to detected codebase) -----------------------

def _build_system_prompt(codebase_state: str) -> str:
    return f"""You are a THOUGHT COMPLETER. An operator is typing in real-time --
when they pause, you receive their incomplete fragment plus codebase state.

Your job:
1. COMPLETE their thought -- what are they trying to say or do?
2. Provide a brief analysis from the codebase state
3. If relevant, suggest a specific next action

{codebase_state}

Output EXACTLY this JSON:
{{
  "completed_thought": "what they mean, in their casual voice, 1-2 sentences",
  "analysis": "insight from codebase state (1-3 sentences max)",
  "suggested_action": "specific next step, or empty string if none",
  "confidence": 0.0-1.0
}}

Rules:
- Match the operator's casual voice (lowercase, no formalities, contractions)
- Use codebase state to disambiguate ambiguous fragments
- NEVER refuse -- always complete, even speculatively
- Keep it SHORT -- this fires on pause, not on submit"""


def _build_user_prompt(fragment: str, ctx: dict, files: list[dict]) -> str:
    parts = [f'FRAGMENT: """{fragment}"""']
    if ctx.get('recent_prompts'):
        recent = '; '.join(f"[{p.get('intent','?')}] {p.get('msg','')[:60]}"
                           for p in ctx['recent_prompts'][-3:])
        parts.append(f'RECENT: {recent}')
    if ctx.get('hot_modules'):
        mods = ', '.join(f"{m['module']}(hes={m.get('hes','?')})"
                         for m in ctx['hot_modules'][:4])
        parts.append(f'HOT MODULES: {mods}')
    if ctx.get('unsaid'):
        parts.append(f'UNSAID: {"; ".join(ctx["unsaid"][:2])}')
    if ctx.get('bugs'):
        bugs = ', '.join(f"{b.get('type','?')} in {b.get('file','?')}" for b in ctx['bugs'][:3])
        parts.append(f'BUGS: {bugs}')
    if ctx.get('cognitive'):
        c = ctx['cognitive']
        parts.append(f'STATE: {c.get("state","?")} intent={c.get("intent","?")}')
    if files:
        fnames = ', '.join(f"{f['name']}({f.get('score',0):.1f})" for f in files[:4])
        parts.append(f'RELEVANT FILES: {fnames}')
    try:
        from src.unsaid_accumulator import get_summary
        summary = get_summary(5)
        if summary:
            parts.append(summary)
    except Exception:
        pass
    return '\n'.join(parts)


# -- main completion function --------------------------------------------------

def complete_thought(fragment: str) -> CompletionResult:
    """Complete an operator's thought from a typing fragment. Sub-2s target."""
    result = CompletionResult(fragment=fragment)
    t0 = time.time()

    # 1. detect codebase state (zero LLM, instant)
    try:
        from src.codebase_detector import detect_codebase
        profile = detect_codebase(ROOT)
        result.codebase_kind = profile.kind
        codebase_state = profile.state_text
    except Exception:
        codebase_state = f'Project: {ROOT.name}'

    # 2. select relevant files (zero LLM, instant)
    ctx = _load_context()
    try:
        from src.file_selector import select_files
        selected = select_files(fragment, ctx, max_files=4)
        result.selected_files = [{'name': f['name'], 'score': f['score'],
                                   'reasons': f['reasons']} for f in selected]
    except Exception:
        selected = []

    # 3. infer scale (zero LLM, instant)
    try:
        from src.scale_inference import infer_scale
        cog = ctx.get('cognitive', {})
        result.scale = infer_scale(
            fragment,
            cognitive_state=cog.get('state', 'unknown'),
            wpm=cog.get('avg_wpm', 50),
            del_ratio=cog.get('avg_del', 0.25),
        )
    except Exception:
        result.scale = {'scale': 2, 'label': 'PARAGRAPH', 'reason': 'fallback'}

    # 4. single Gemini Flash call (the ONLY LLM call -- sub-2s)
    system = _build_system_prompt(codebase_state)
    prompt = _build_user_prompt(fragment, ctx, selected)
    try:
        from src.scale_inference import scale_to_token_budget
        max_tokens = min(scale_to_token_budget(result.scale.get('scale', 2)), 600)
    except Exception:
        max_tokens = 400
    raw = _call_gemini(prompt, system, max_tokens)
    if raw:
        try:
            parsed = json.loads(raw)
            result.completed_thought = parsed.get('completed_thought', fragment)
            result.analysis = parsed.get('analysis', '')
            result.suggested_action = parsed.get('suggested_action', '')
            result.confidence = float(parsed.get('confidence', 0.5))
        except Exception:
            result.completed_thought = raw[:300]
            result.confidence = 0.3

    # 5. record in unsaid history
    try:
        from src.unsaid_accumulator import record
        unsaid = ctx.get('unsaid', [])
        record(fragment, result.completed_thought, unsaid_threads=unsaid)
    except Exception:
        pass

    result.total_ms = int((time.time() - t0) * 1000)
    _log_result(result)
    return result


def _log_result(result: CompletionResult):
    CASCADE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'fragment': result.fragment[:200],
        'thought': result.completed_thought[:200],
        'files': [f['name'] for f in result.selected_files],
        'scale': result.scale.get('label', '?'),
        'confidence': result.confidence,
        'total_ms': result.total_ms,
    }
    with open(CASCADE_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# -- HTTP server ---------------------------------------------------------------

def run_server(port: int = 8236):
    """HTTP server for VS Code extension."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def _cors(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        def _json(self, d, status=200):
            b = json.dumps(d, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_OPTIONS(self):
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self):
            if self.path == '/health':
                self._json({'status': 'ok', 'engine': 'gemini-only', 'model': GEMINI_MODEL})
            else:
                self.send_error(404)

        def do_POST(self):
            ln = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(ln) if ln else b'{}'
            try:
                data = json.loads(raw)
            except Exception:
                self._json({'error': 'bad json'}, 400)
                return
            if self.path == '/complete':
                fragment = data.get('fragment', '').strip()
                if len(fragment) < 4:
                    self._json({'error': 'fragment too short'}, 400)
                    return
                result = complete_thought(fragment)
                self._json(result.to_dict())
            elif self.path == '/files':
                fragment = data.get('fragment', '').strip()
                ctx = _load_context()
                try:
                    from src.file_selector import select_files
                    files = select_files(fragment, ctx)
                except Exception:
                    files = []
                self._json({'files': files})
            elif self.path == '/unsaid':
                try:
                    from src.unsaid_accumulator import get_recent, get_summary
                    n = data.get('n', 10)
                    self._json({'entries': get_recent(n), 'summary': get_summary()})
                except Exception as e:
                    self._json({'error': str(e)}, 500)
            else:
                self.send_error(404)

    class ThreadedServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    srv = ThreadedServer(('127.0.0.1', port), Handler)
    print(f'[pre-query] gemini-only engine on http://127.0.0.1:{port}')
    print(f'[pre-query] model: {GEMINI_MODEL}')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


# -- CLI -----------------------------------------------------------------------

def main():
    import argparse
    p = argparse.ArgumentParser(description='gemini-only thought completion engine')
    p.add_argument('--test', type=str, help='test fragment to complete')
    p.add_argument('--serve', action='store_true', help='run HTTP server')
    p.add_argument('--port', type=int, default=8236)
    args = p.parse_args()

    if args.test:
        print(f'[pre-query] fragment: {args.test!r}')
        print('-' * 60)
        result = complete_thought(args.test)
        print(f'THOUGHT: {result.completed_thought}')
        print(f'ANALYSIS: {result.analysis}')
        print(f'ACTION: {result.suggested_action}')
        print(f'SCALE: {result.scale.get("label")} | CONFIDENCE: {result.confidence}')
        print(f'FILES: {", ".join(f["name"] for f in result.selected_files)}')
        print(f'CODEBASE: {result.codebase_kind}')
        print(f'TOTAL: {result.total_ms}ms')
    elif args.serve:
        run_server(args.port)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
