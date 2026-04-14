"""tc_web_html_seq001_v001_html_const_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 29 lines | ~748 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json

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
