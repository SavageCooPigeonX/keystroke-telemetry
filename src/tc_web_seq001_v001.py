"""Web server mode for thought completer (Railway deploy)."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json

from .tc_constants_seq001_v001 import GEMINI_MODEL
from .tc_context_seq001_v001 import load_context
from .tc_gemini_seq001_v001 import call_gemini, log_completion

WEB_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>thought completer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0d1117;color:#e6edf3;font-family:'Cascadia Code',monospace;font-size:14px;height:100vh;display:flex;flex-direction:column}
#h{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid #30363d;background:#161b22;font-size:12px;color:#8b949e}
#h .t{color:#58a6ff;font-weight:600}
#w{flex:1;position:relative}
#g{position:absolute;inset:0;padding:16px;white-space:pre-wrap;font:inherit;pointer-events:none;z-index:1;line-height:1.6}
.ty{color:transparent}.co{color:#484f58;font-style:italic}
#i{position:absolute;inset:0;padding:16px;background:transparent;color:#e6edf3;border:none;outline:none;resize:none;font:inherit;line-height:1.6;z-index:2;caret-color:#58a6ff}
#b{padding:6px 12px;border-top:1px solid #30363d;background:#161b22;font-size:11px;color:#8b949e;display:flex;justify-content:space-between}
</style></head><body>
<div id="h"><span class="t">&#x1f9e0; thought completer</span><span id="s">ready</span></div>
<div id="w"><div id="g"><span class="ty"></span><span class="co"></span></div>
<textarea id="i" placeholder="start typing..." spellcheck="false" autofocus></textarea></div>
<div id="b"><span>tab accept · esc dismiss · ctrl+enter copy</span><span id="st">✓0 ✗0</span></div>
<script>
let pt,cc='',cb='',na=0,nr=0;
const i=document.getElementById('i'),gt=document.querySelector('.ty'),gc=document.querySelector('.co'),s=document.getElementById('s'),st=document.getElementById('st');
function ug(){gt.textContent=i.value;gc.textContent=(cc&&i.value===cb)?cc:'';if(cc&&i.value!==cb){lg(0);cc=cb=''}}
function lg(a){if(!cc)return;fetch('/log',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({buffer:cb,completion:cc,accepted:!!a,final_text:i.value.slice(0,2e3)})}).catch(()=>{});a?na++:nr++;st.textContent='\u2713'+na+' \u2717'+nr}
async function rq(){const b=i.value.trim();if(b.length<8)return;s.textContent='...';try{const r=await(await fetch('/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({buffer:b})})).json();if(r.completion&&i.value.trim()===b){cc=r.completion;cb=i.value;ug();s.textContent='tab'}else s.textContent='ready'}catch(e){s.textContent='err'}}
i.addEventListener('input',()=>{ug();clearTimeout(pt);s.textContent='typing';pt=setTimeout(rq,2e3)});
i.addEventListener('keydown',e=>{if(e.key==='Tab'&&cc){e.preventDefault();i.value=cb+cc;lg(1);cc=cb='';ug();s.textContent='ready';clearTimeout(pt);pt=setTimeout(rq,2e3)}if(e.key==='Escape'&&cc){e.preventDefault();lg(0);cc=cb='';ug()}if(e.key==='Enter'&&e.ctrlKey){e.preventDefault();const t=i.value.trim();t&&navigator.clipboard.writeText(t).then(()=>{i.value='';cc=cb='';ug()})}});
</script></body></html>"""


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
