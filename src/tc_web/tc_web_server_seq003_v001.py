"""tc_web_server_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 49 lines | ~614 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from ..tc_constants import GEMINI_MODEL
from ..tc_context import load_context
from ..tc_gemini import call_gemini, log_completion
import json

def run_web(port=8235):
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _c(self):
            for h, v in [('Access-Control-Allow-Origin', '*'),
                         ('Access-Control-Allow-Methods', 'GET,POST,OPTIONS'),
                         ('Access-Control-Allow-Headers', 'Content-Type')]:
                self.send_header(h, v)
        def _j(self, d, s=200):
            b = json.dumps(d, ensure_ascii=False).encode()
            self.send_response(s); self.send_header('Content-Type', 'application/json')
            self._c(); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
        def do_OPTIONS(self):
            self.send_response(204); self._c(); self.end_headers()
        def do_GET(self):
            if self.path in ('/', '/index.html'):
                b = WEB_HTML.encode()
                self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
                self._c(); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
            elif self.path == '/health': self._j({'status': 'ok', 'model': GEMINI_MODEL})
            elif self.path == '/context': self._j(load_context())
            else: self.send_error(404)
        def do_POST(self):
            ln = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(ln) if ln else b'{}'
            try: data = json.loads(raw)
            except Exception: self._j({'error': 'bad json'}, 400); return
            if self.path == '/complete':
                buf = data.get('buffer', '').strip()
                text, _ = call_gemini(buf) if len(buf) >= 8 else ('', [])
                self._j({'completion': text})
            elif self.path == '/log':
                log_completion(data); self._j({'ok': True})
            else: self.send_error(404)

    class S(ThreadingMixIn, HTTPServer): daemon_threads = True
    srv = S(('0.0.0.0', port), H)
    print(f'[thought completer] web on http://localhost:{port}')
    try: srv.serve_forever()
    except KeyboardInterrupt: srv.shutdown()
