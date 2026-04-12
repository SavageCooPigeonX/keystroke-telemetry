"""Interrogation Room — problematic modules question the operator.

Launch:  py src/interrogation_room.py
         py src/interrogation_room.py --port 8236 --top 10
         py src/interrogation_room.py --list  (print queue, no server)

Modules ranked by urgency (escalation level × passes ignored × chronic status).
Each asks pointed questions referencing prompt history, deleted words, fears.
Answers feed back into thought_completer context via reinjection pipeline.

Reinjection loop:
  prompt_journal → interrogation answers → tc_context.py →
  thought_completer predictions → better operator prompts →
  copilot reads enriched context → generates code →
  escalation checks remaining bugs → back to interrogation room
"""
from __future__ import annotations
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ir_loader import (load_suspects, load_prompt_history, load_unsaid,
                           generate_questions, record_answer, get_answers)

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-11T21:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  create interrogation room server
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

IR_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>interrogation room</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#e0e0e0;font-family:'Cascadia Code','Fira Code',monospace;height:100vh;display:flex;overflow:hidden}
#room{flex:1;display:flex;flex-direction:column;padding:32px 40px;max-width:70%}
#sidebar{width:30%;border-left:1px solid #1a1a1a;overflow-y:auto;padding:16px;background:#080808}
.mn{color:#ff4444;font-size:26px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;text-shadow:0 0 20px rgba(255,68,68,0.3)}
.st{color:#444;font-size:11px;margin-bottom:28px;line-height:1.8}
.st span{margin-right:10px}
.bd{display:inline-block;padding:2px 6px;border-radius:3px;font-size:10px;margin-right:4px}
.bd-a{background:#ff444430;color:#ff4444;border:1px solid #ff444450}
.bd-c{background:#ff880030;color:#ff8800;border:1px solid #ff880050}
.bd-b{background:#ffffff10;color:#888;border:1px solid #ffffff20}
#q{font-size:17px;line-height:1.7;color:#ccc;font-style:italic;margin-bottom:28px;min-height:80px}
#q::after{content:'_';animation:bl 1s infinite;color:#ff4444}
@keyframes bl{0%,50%{opacity:1}51%,100%{opacity:0}}
#a{width:100%;background:#0f0f0f;border:1px solid #222;color:#e0e0e0;font:14px/1.6 inherit;padding:12px;resize:none;height:100px;border-radius:4px;outline:none}
#a:focus{border-color:#ff4444;box-shadow:0 0 8px rgba(255,68,68,0.15)}
#c{display:flex;justify-content:space-between;align-items:center;margin-top:12px}
#nb{background:#ff444420;color:#ff4444;border:1px solid #ff444450;padding:8px 20px;cursor:pointer;font:inherit;border-radius:4px}
#nb:hover{background:#ff444440}
#pr{color:#444;font-size:12px}
.sbt{color:#555;font-size:11px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
.pe{padding:8px;border-bottom:1px solid #111;margin-bottom:4px}
.pe .ti{color:#333;font-size:10px}
.pe .it{font-size:9px;padding:1px 4px;border-radius:2px;background:#ffffff08;color:#666}
.pe .mg{color:#777;font-size:12px;margin-top:4px;word-break:break-word}
.pe .dl{color:#ff444488;font-size:11px;font-style:italic;margin-top:2px}
#su{display:none;padding:32px;overflow-y:auto;height:100vh}
#su h2{color:#ff4444;margin-bottom:16px}
.ac{background:#0f0f0f;border:1px solid #1a1a1a;border-radius:4px;padding:12px;margin-bottom:8px}
.ac .aq{color:#888;font-style:italic;margin-bottom:8px}
.ac .aa{color:#ccc}
.ac .am{color:#ff4444;font-size:12px;margin-bottom:4px}
</style></head><body>
<div id="room">
<div class="mn" id="mn">loading...</div>
<div class="st" id="ms"></div>
<div id="q"></div>
<textarea id="a" placeholder="your answer... (ctrl+enter to submit)"></textarea>
<div id="c"><span id="pr"></span><button id="nb">next &rarr;</button></div>
</div>
<div id="sidebar">
<div class="sbt">your prompt history</div>
<div id="hi"></div>
</div>
<div id="su">
<h2>interrogation complete</h2>
<div id="sc"></div>
<p style="color:#444;margin-top:16px">answers logged to logs/interrogation_answers.jsonl<br>
reinjection active &mdash; thought_completer reads these next cycle</p>
</div>
<script>
let S={m:[],i:0,ans:[]};
async function init(){
  const r=await(await fetch('/api/state')).json();
  S.m=r.modules;rH(r.history);
  S.m.length?show(0):(document.getElementById('q').textContent='no problematic modules. organism is clean.');
}
function show(i){
  S.i=i;S.qi=0;const m=S.m[i];
  document.getElementById('mn').textContent=m.name;
  let s=`<span class="bd bd-${m.level>=4?'a':'b'}">${m.level_name}</span>`;
  if(m.chronic_reports>5)s+='<span class="bd bd-c">chronic</span>';
  s+=`<span class="bd bd-b">${m.bug_type}</span>`;
  s+=`<br><span>${m.tokens} tok</span><span>v${m.version}</span>`;
  s+=`<span>conf: ${(m.confidence*100).toFixed(0)}%</span>`;
  s+=`<span>ignored: ${m.passes_ignored}&times;</span>`;
  if(m.fears&&m.fears.length)s+=`<br><span>fears: ${m.fears.join(', ')}</span>`;
  if(m.fix_failed)s+=`<br><span style="color:#ff6644">self-fix failed: ${m.fix_desc}</span>`;
  document.getElementById('ms').innerHTML=s;
  showQ();
  document.getElementById('a').value='';document.getElementById('a').focus();
}
function showQ(){
  const m=S.m[S.i],q=m.questions[S.qi]||'speak.';
  tT(document.getElementById('q'),q);
  document.getElementById('pr').textContent=`${S.i+1}/${S.m.length} \u00b7 q${S.qi+1}/${m.questions.length}`;
}
function tT(el,t){el.textContent='';let i=0;const iv=setInterval(()=>{el.textContent=t.slice(0,++i);if(i>=t.length)clearInterval(iv)},18);}
function rH(entries){
  document.getElementById('hi').innerHTML=entries.map(e=>{
    let d='';
    if(e.deleted_words&&e.deleted_words.length)d=`<div class="dl">deleted: ${e.deleted_words.slice(0,3).join(', ')}</div>`;
    return `<div class="pe"><span class="ti">${(e.ts||'').slice(11,19)}</span> <span class="it">${e.intent||'?'}</span><div class="mg">${(e.msg||'').slice(0,120)}</div>${d}</div>`;
  }).reverse().join('');
}
document.getElementById('nb').addEventListener('click',async()=>{
  const m=S.m[S.i],v=document.getElementById('a').value.trim(),q=m.questions[S.qi]||'';
  if(v){
    await fetch('/api/answer',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({module:m.name,question:q,answer:v})});
    S.ans.push({module:m.name,question:q,answer:v});
  }
  // advance to next question for same module, or next module
  if(S.qi<m.questions.length-1){
    S.qi++;document.getElementById('a').value='';showQ();
  } else {
    S.i<S.m.length-1?show(S.i+1):done();
  }
});
document.getElementById('a').addEventListener('keydown',e=>{
  if(e.key==='Enter'&&e.ctrlKey){e.preventDefault();document.getElementById('nb').click();}
});
function done(){
  document.getElementById('room').style.display='none';
  document.getElementById('sidebar').style.display='none';
  const s=document.getElementById('su');s.style.display='block';
  document.getElementById('sc').innerHTML=S.ans.map(a=>
    `<div class="ac"><div class="am">${a.module}</div><div class="aq">"${a.question}"</div><div class="aa">${a.answer}</div></div>`
  ).join('');
}
init();
</script></body></html>"""


def run_web(port: int = 8236, top_n: int = 15):
    from http.server import HTTPServer, BaseHTTPRequestHandler
    suspects = load_suspects(top_n)
    history = load_prompt_history(30)
    unsaid = load_unsaid()
    for i, m in enumerate(suspects):
        m['questions'] = generate_questions(m, history, unsaid, position=i)
    hist_json = [{'ts': e.get('ts', ''), 'msg': e.get('msg', '')[:150],
                  'intent': e.get('intent', ''),
                  'deleted_words': e.get('deleted_words', [])[:5]} for e in history]

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def _j(self, d, s=200):
            b = json.dumps(d, ensure_ascii=False).encode()
            self.send_response(s)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers(); self.wfile.write(b)

        def do_GET(self):
            if self.path in ('/', '/index.html'):
                b = IR_HTML.encode()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(b)))
                self.end_headers(); self.wfile.write(b)
            elif self.path == '/api/state':
                self._j({'modules': suspects, 'history': hist_json})
            elif self.path == '/api/answers':
                self._j(get_answers())
            else:
                self.send_error(404)

        def do_POST(self):
            ln = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(ln) if ln else b'{}'
            try:
                data = json.loads(raw)
            except Exception:
                self._j({'error': 'bad json'}, 400); return
            if self.path == '/api/answer':
                record_answer(data.get('module', ''),
                              data.get('question', ''), data.get('answer', ''))
                self._j({'ok': True})
            else:
                self.send_error(404)

    srv = HTTPServer(('127.0.0.1', port), H)
    print(f'[interrogation room] http://localhost:{port}')
    print(f'[interrogation room] {len(suspects)} suspects loaded')
    for i, s in enumerate(suspects[:5], 1):
        print(f'  {i}. {s["name"]} — {s["level_name"]} | {s["bug_type"]} | urgency={s["urgency"]:.0f}')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


def list_suspects(top_n: int = 15):
    suspects = load_suspects(top_n)
    history = load_prompt_history(30)
    unsaid = load_unsaid()
    print(f'=== INTERROGATION QUEUE ({len(suspects)} suspects) ===\n')
    for i, s in enumerate(suspects, 1):
        qs = generate_questions(s, history, unsaid, position=i - 1)
        print(f'{i}. {s["name"]}')
        print(f'   {s["level_name"]} | {s["bug_type"]} | urgency={s["urgency"]:.0f}')
        print(f'   tokens={s["tokens"]} v={s["version"]} ignored={s["passes_ignored"]}x')
        if s['fix_failed']:
            print(f'   FAILED: {s["fix_desc"]}')
        for q in qs[:2]:
            print(f'   Q: "{q}"')
        print()


def main():
    import argparse
    p = argparse.ArgumentParser(description='interrogation room')
    p.add_argument('--port', type=int, default=8236)
    p.add_argument('--top', type=int, default=15)
    p.add_argument('--list', action='store_true', help='print queue only')
    args = p.parse_args()
    if args.list:
        list_suspects(args.top)
    else:
        run_web(args.port, args.top)


if __name__ == '__main__':
    main()
