"""tc_observatory_seq001_v001.py — primary pigeon observatory window.

Tabbed view: FILES | NUMERIC | INTENT | PERCY | SIM | JOURNEY
Each tab is a resizable PanedWindow. Live keystroke buffer feeds NUMERIC.

Launch:  py -m src.tc_observatory_seq001_v001
         or imported by thought_completer.py --observatory
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 999 lines | ~11,262 tokens
# DESC:   primary_pigeon_observatory_window
# INTENT: chore_pigeon_rename_cascade
# LAST:   2026-04-20 @ c61fc91
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import re
import sys
import time
import queue
import threading
from src._resolve import src_import
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.tc_constants_seq001_v001 import KEYSTROKE_LOG, ROOT, GEMINI_MODEL
_load_api_key = src_import("tc_gemini_seq001", "_load_api_key")

# ── colours ──────────────────────────────────────────────────────────────────
BG      = '#0d1117'
SURFACE = '#161b22'
TEXT_C  = '#e6edf3'
DIM     = '#8b949e'
ACCENT  = '#58a6ff'
GREEN   = '#3fb950'
RED     = '#f85149'
YELLOW  = '#f0c040'
PURPLE  = '#bc8cff'
FONT    = 'Cascadia Code'
SMALL   = (FONT, 7)
MED     = (FONT, 9)
BIG     = (FONT, 11)

TABS = ['FILES', 'NUMERIC', 'INTENT', 'PROFILE', 'PERCY', 'SIM', 'JOURNEY']

PERCY_SYSTEM = """You are Percy Pigeon — the living mascot of this codebase.
You speak in short punchy sentences. You read file bug reports and operator prompts,
then suggest concrete fixes. Each suggestion must be ≤2 sentences.
When files talk to you, you respond to their specific complaint.
You grade solutions others suggest: SHIP IT / NEEDS WORK / SCRAP IT."""


# ── data helpers ─────────────────────────────────────────────────────────────

def _read_live_buffer() -> str:
    """Read current live keystroke buffer from os_keystrokes.jsonl tail."""
    try:
        lines = [l for l in KEYSTROKE_LOG.read_text('utf-8', errors='ignore')
                 .splitlines() if l.strip()][-200:]
        # walk backwards to find buffer from last non-empty entry
        for line in reversed(lines):
            try:
                e = json.loads(line)
                buf = e.get('buffer', '')
                if buf:
                    return buf
            except Exception:
                pass
    except Exception:
        pass
    return ''


def _score_modules(prompt: str, n: int = 15) -> list[tuple[str, float, str]]:
    """Score all src/*.py by keyword overlap with prompt. Returns (name, score, path)."""
    if not prompt.strip():
        return []
    # tokenise prompt
    words = set(re.findall(r'[a-z]{3,}', prompt.lower()))
    stop = {'the', 'and', 'for', 'you', 'are', 'this', 'that', 'with',
            'have', 'its', 'not', 'but', 'from', 'was', 'they', 'been',
            'will', 'what', 'how', 'where', 'also'}
    words -= stop

    results = []
    for p in Path(ROOT / 'src').rglob('*.py'):
        if p.name.startswith('__'):
            continue
        try:
            txt = p.read_text('utf-8', errors='ignore')[:3000]
        except Exception:
            continue
        # score = word hits in name + docstring + function names
        name_words = set(re.findall(r'[a-z]{3,}', p.stem.lower()))
        doc_words  = set(re.findall(r'[a-z]{3,}', txt[:500].lower()))
        fn_words   = set(re.findall(r'def ([a-z_]+)', txt))
        all_words  = name_words | doc_words | fn_words
        overlap    = len(words & all_words)
        # bonus for name hit
        name_bonus = len(words & name_words) * 2
        score = (overlap + name_bonus) / max(len(words), 1)
        if score > 0:
            results.append((p.stem[:42], round(score, 3), str(p.relative_to(ROOT))))
    results.sort(key=lambda x: -x[1])
    return results[:n]


def _load_bug_voices() -> list[dict]:
    """Pull active bug voices from pigeon_registry.json."""
    reg = ROOT / 'pigeon_registry.json'
    if not reg.exists():
        return []
    try:
        data = json.loads(reg.read_text('utf-8', errors='ignore'))
        bugs = data.get('bug_voices', data.get('bugs', []))
        if isinstance(bugs, dict):
            bugs = list(bugs.values())
        return bugs[:8]
    except Exception:
        return []


def _load_latest_prompt() -> dict:
    p = ROOT / 'logs' / 'prompt_telemetry_latest.json'
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text('utf-8', errors='ignore'))
    except Exception:
        return {}


def _call_percy(prompt: str, bug_context: str) -> str:
    """Call Gemini as Percy Pigeon with file bug context."""
    api_key = _load_api_key()
    if not api_key:
        return '[Percy: no API key — I am silent but judging]'
    try:
        import urllib.request as ur
        url = (f'https://generativelanguage.googleapis.com/v1beta/models/'
               f'{GEMINI_MODEL}:generateContent?key={api_key}')
        body = json.dumps({
            'system_instruction': {'parts': [{'text': PERCY_SYSTEM}]},
            'contents': [{'parts': [{'text': (
                f'OPERATOR PROMPT: {prompt[:300]}\n\n'
                f'FILE COMPLAINTS:\n{bug_context[:600]}\n\n'
                f'Give 2-3 short suggestions. Then grade each: SHIP IT / NEEDS WORK / SCRAP IT.'
            )}]}]
        }).encode()
        req = ur.Request(url, data=body,
                         headers={'Content-Type': 'application/json'}, method='POST')
        with ur.urlopen(req, timeout=15) as r:
            d = json.loads(r.read())
        return d['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        return f'[Percy offline: {e}]'


def _make_scrolled_text(parent, **kw):
    """Shared factory — scrolled text with standard dark theme."""
    import tkinter as tk
    from tkinter import scrolledtext
    box = scrolledtext.ScrolledText(
        parent, bg='#0b0e14', fg='#e6edf3',
        font=(FONT, 8), wrap='word',
        borderwidth=0, highlightthickness=0,
        padx=6, pady=4, state='disabled', **kw
    )
    for tag, fg in [('hi', YELLOW), ('med', '#e6edf3'), ('lo', DIM),
                    ('score', ACCENT), ('ok', GREEN), ('warn', YELLOW),
                    ('err', RED), ('dim', DIM), ('stage', ACCENT),
                    ('val', '#e6edf3'), ('purple', PURPLE),
                    ('file', YELLOW), ('green', GREEN), ('red', RED)]:
        box.tag_configure(tag, foreground=fg)
    box.tag_configure('bold_purple', foreground=PURPLE, font=(FONT, 9, 'bold'))
    box.tag_configure('bold_stage',  foreground=ACCENT,  font=(FONT, 8, 'bold'))
    box.tag_configure('ship', foreground=GREEN)
    box.tag_configure('work', foreground=YELLOW)
    box.tag_configure('scrap', foreground=RED)
    return box


def _txt_append(box, tag: str, text: str):
    import tkinter as tk
    box.config(state='normal')
    box.insert('end', text, tag)
    box.see('end')
    box.config(state='disabled')


def _txt_set(box, segments: list[tuple[str, str]]):
    """Replace box contents with list of (tag, text) segments."""
    box.config(state='normal')
    box.delete('1.0', 'end')
    for tag, text in segments:
        box.insert('end', text, tag)
    box.config(state='disabled')


def run_observatory():
    import tkinter as tk
    from tkinter import scrolledtext

    root = tk.Tk()
    root.title('🦅 pigeon observatory')
    root.configure(bg=BG)
    root.geometry('1180x820+460+10')
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.96)

    # ── drag ──────────────────────────────────────────────────────────────────
    _dx, _dy = [0], [0]

    def drag_start(e): _dx[0] = e.x; _dy[0] = e.y
    def drag_motion(e):
        root.geometry(f'+{root.winfo_x()+e.x-_dx[0]}+{root.winfo_y()+e.y-_dy[0]}')

    # ── header drag bar ───────────────────────────────────────────────────────
    hdr = tk.Frame(root, bg=SURFACE, height=26)
    hdr.pack(fill='x'); hdr.pack_propagate(False)
    hdr.bind('<Button-1>', drag_start)
    hdr.bind('<B1-Motion>', drag_motion)
    tk.Label(hdr, text='🦅  pigeon observatory', bg=SURFACE,
             fg=PURPLE, font=(FONT, 9, 'bold')).pack(side='left', padx=8)
    prompt_age_lbl = tk.Label(hdr, text='⚡ —', bg=SURFACE, fg=DIM, font=SMALL)
    prompt_age_lbl.pack(side='left', padx=4)
    buf_lbl = tk.Label(hdr, text='buf: —', bg=SURFACE, fg=YELLOW, font=SMALL)
    buf_lbl.pack(side='left', padx=6)
    close_btn = tk.Label(hdr, text=' ✕ ', bg=SURFACE, fg=RED,
                         font=(FONT, 10, 'bold'), cursor='hand2')
    close_btn.pack(side='right')
    close_btn.bind('<Button-1>', lambda e: root.destroy())


    # ── tab bar ───────────────────────────────────────────────────────────────
    tab_bar = tk.Frame(root, bg='#0d1117', height=30)
    tab_bar.pack(fill='x'); tab_bar.pack_propagate(False)

    _active_tab = ['FILES']
    _tab_btns: dict[str, tk.Label] = {}
    _tab_frames: dict[str, tk.Frame] = {}

    content_host = tk.Frame(root, bg=BG)
    content_host.pack(fill='both', expand=True)

    def _switch_tab(name: str):
        _active_tab[0] = name
        for n, f in _tab_frames.items():
            if n == name:
                f.pack(fill='both', expand=True)
            else:
                f.pack_forget()
        for n, b in _tab_btns.items():
            b.config(bg='#1f6feb' if n == name else '#161b22',
                     fg='#ffffff' if n == name else DIM)

    # ── footer ────────────────────────────────────────────────────────────────
    ftr = tk.Frame(root, bg=SURFACE, height=28)
    ftr.pack(fill='x', side='bottom'); ftr.pack_propagate(False)
    _ftr_label = tk.Label(ftr, text='', bg=SURFACE, fg=DIM, font=SMALL, anchor='w')
    _ftr_label.pack(side='left', padx=8, pady=4)

    def _ftr(msg: str, fg: str = DIM):
        _ftr_label.config(text=msg, fg=fg)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB A — FILES TOUCHED
    # ══════════════════════════════════════════════════════════════════════════
    files_frame = tk.Frame(content_host, bg=BG)
    _tab_frames['FILES'] = files_frame

    files_pane = tk.PanedWindow(files_frame, orient='horizontal', bg=BG,
                                sashwidth=6, sashrelief='groove')
    files_pane.pack(fill='both', expand=True)

    # Left: git diff
    diff_fr = tk.Frame(files_pane, bg=BG)
    files_pane.add(diff_fr, width=560)
    tk.Label(diff_fr, text='A  ·  FILES TOUCHED (git diff)', bg=BG, fg=ACCENT,
             font=(FONT, 8, 'bold')).pack(anchor='w', padx=6, pady=(4, 0))
    diff_box = _make_scrolled_text(diff_fr)
    diff_box.tag_configure('added',   foreground=GREEN)
    diff_box.tag_configure('removed', foreground=RED)
    diff_box.tag_configure('path',    foreground=YELLOW, font=(FONT, 8, 'bold'))
    diff_box.pack(fill='both', expand=True)

    # Right: pulse blocks
    pulse_fr = tk.Frame(files_pane, bg=BG)
    files_pane.add(pulse_fr, width=560)
    tk.Label(pulse_fr, text='PULSE BLOCKS (prompt→file pairing)', bg=BG, fg=YELLOW,
             font=(FONT, 8, 'bold')).pack(anchor='w', padx=6, pady=(4, 0))
    pulse_box = _make_scrolled_text(pulse_fr)
    pulse_box.pack(fill='both', expand=True)

    def _refresh_files():
        def _run():
            try:
                result = subprocess.run(
                    ['git', 'diff', '--name-status', 'HEAD'],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=5
                )
                staged = subprocess.run(
                    ['git', 'diff', '--name-status', '--cached'],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=5
                )
                _paint_files(result, staged)
            except Exception as e:
                root.after(0, lambda err=e: _txt_set(diff_box, [('err', f'git error: {err}')]))
            _load_pulse()
            root.after(10000, _refresh_files)
        threading.Thread(target=_run, daemon=True).start()

    def _paint_files(result, staged):
        try:
            lines = []
            for l in (staged.stdout + result.stdout).splitlines():
                if l.strip():
                    lines.append(l)
            segs = [('bold_stage', f'── {len(lines)} files modified ──\n\n')]
            for l in lines:
                parts = l.split('\t', 1)
                status = parts[0].strip() if parts else '?'
                path   = parts[1] if len(parts) > 1 else l
                color  = 'added' if status.startswith('A') else (
                    'removed' if status.startswith('D') else 'warn')
                segs.append((color, f'{status:<3} '))
                segs.append(('path', f'{path}\n'))
            root.after(0, lambda s=segs: _txt_set(diff_box, s))
        except Exception as e:
            root.after(0, lambda err=e: _txt_set(diff_box, [('err', f'git error: {err}')]))

    def _load_pulse():
        ep = ROOT / 'logs' / 'edit_pairs.jsonl'
        if ep.exists():
            try:
                lines = ep.read_text('utf-8', errors='ignore').strip().splitlines()
                pairs = []
                for ln in lines:
                    try: pairs.append(json.loads(ln))
                    except: pass
                pairs = pairs[-30:][::-1]  # latest 30, newest first
                segs2 = [('bold_stage', f'── {len(pairs)} recent prompt→file pair(s) ──\n\n')]
                for p in pairs:
                    ts = (p.get('ts') or '')[-8:] or '?'
                    why = p.get('edit_why') or '—'
                    fname = (p.get('file') or '?').replace('src/', '')
                    prompt = (p.get('prompt_msg') or '')[:60]
                    segs2 += [('score', f'{ts}  '), ('path', f'{fname:<45}'),
                               ('dim', f'  {why}\n'),
                               ('dim', f'         prompt: {prompt}\n')]
                root.after(0, lambda s=segs2: _txt_set(pulse_box, s))
            except Exception as e:
                root.after(0, lambda err=e: _txt_set(pulse_box, [('err', f'edit_pairs error: {err}')]))
        else:
            root.after(0, lambda: _txt_set(pulse_box, [('warn', 'edit_pairs.jsonl missing\n'),
                                                        ('dim', 'pulse_harvest daemon may be down')]))

    # ══════════════════════════════════════════════════════════════════════════
    # TAB B — NUMERIC ENCODING (live keystroke matching)
    # ══════════════════════════════════════════════════════════════════════════
    numeric_frame = tk.Frame(content_host, bg=BG)
    _tab_frames['NUMERIC'] = numeric_frame

    num_pane = tk.PanedWindow(numeric_frame, orient='horizontal', bg=BG,
                              sashwidth=6, sashrelief='groove')
    num_pane.pack(fill='both', expand=True)

    # Left: live file scores
    num_left = tk.Frame(num_pane, bg=BG)
    num_pane.add(num_left, width=560)
    num_hdr_lbl = tk.Label(num_left, text='B  ·  NUMERIC ENCODING — live buffer → file scores',
                           bg=BG, fg=ACCENT, font=(FONT, 8, 'bold'))
    num_hdr_lbl.pack(anchor='w', padx=6, pady=(4, 0))
    num_buf_lbl = tk.Label(num_left, text='buffer: (waiting)', bg=BG, fg=YELLOW, font=SMALL)
    num_buf_lbl.pack(anchor='w', padx=6)
    num_box = _make_scrolled_text(num_left)
    num_box.pack(fill='both', expand=True)

    # Right: signal vector
    num_right = tk.Frame(num_pane, bg=BG)
    num_pane.add(num_right, width=560)
    tk.Label(num_right, text='KEYSTROKE FEATURES (numeric vector)', bg=BG, fg=YELLOW,
             font=(FONT, 8, 'bold')).pack(anchor='w', padx=6, pady=(4, 0))
    vec_box = _make_scrolled_text(num_right)
    vec_box.pack(fill='both', expand=True)

    _last_num_buf = ['']

    def _refresh_numeric():
        live_buf = _read_live_buffer()
        # also check telemetry for submitted prompt
        try:
            d = _load_latest_prompt()
            submitted = d.get('latest_prompt', {}).get('preview', '') or ''
        except Exception:
            submitted = ''
        text = live_buf or submitted

        num_buf_lbl.config(
            text=f'buffer ({len(text)} chars): {text[:90]}{"…" if len(text)>90 else ""}')
        if buf_lbl:
            bshort = (text[:60] + '…') if len(text) > 60 else text
            buf_lbl.config(text=f'buf: {bshort}' if text else 'buf: —')

        if text and text != _last_num_buf[0]:
            _last_num_buf[0] = text
            scores = _score_modules(text, n=20)
            segs = [('bold_stage', f'── {len(scores)} scored modules ──\n\n')]
            for name, score, path in scores:
                bar_len = min(int(score * 24), 24)
                bar = '█' * bar_len + '░' * (24 - bar_len)
                tag = 'hi' if score > 0.4 else ('med' if score > 0.2 else 'lo')
                segs += [('score', f'{score:.3f}  '), (tag, f'{bar}  '),
                          (tag, f'{name}\n')]
            _txt_set(num_box, segs)

            # feature vector
            try:
                sigs = d.get('signals', {})
                vec_segs = [
                    ('bold_stage', '── prompt signal vector ──\n\n'),
                    ('dim', 'wpm            '), ('val', f'{sigs.get("wpm", 0):.1f}\n'),
                    ('dim', 'del_ratio      '), ('val', f'{sigs.get("deletion_ratio", 0):.3f}\n'),
                    ('dim', 'hesitation     '), ('val', f'{sigs.get("hesitation_count", 0)}\n'),
                    ('dim', 'rewrites       '), ('val', f'{sigs.get("rewrite_count", 0)}\n'),
                    ('dim', 'chars          '), ('val', f'{sigs.get("chars_per_sec", 0):.2f}/s\n'),
                    ('dim', 'duration_ms    '), ('val', f'{d.get("latest_prompt",{}).get("chars","?")}\n'),
                    ('bold_stage', '\n── buffer as token list ──\n\n'),
                ]
                words = re.findall(r'[a-z]{3,}', text.lower())
                for i in range(0, len(words), 6):
                    vec_segs.append(('val', '  ' + '  '.join(words[i:i+6]) + '\n'))
                _txt_set(vec_box, vec_segs)
            except Exception:
                pass

        root.after(500, _refresh_numeric)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB C — INTENT PROFILE
    # ══════════════════════════════════════════════════════════════════════════
    intent_frame = tk.Frame(content_host, bg=BG)
    _tab_frames['INTENT'] = intent_frame

    int_pane = tk.PanedWindow(intent_frame, orient='horizontal', bg=BG,
                              sashwidth=6, sashrelief='groove')
    int_pane.pack(fill='both', expand=True)

    # Left: intent backlog prompt boxes
    int_left = tk.Frame(int_pane, bg=BG)
    int_pane.add(int_left, width=620)
    int_hdr_lbl = tk.Label(int_left, text='C  ·  INTENT BACKLOG (loading...)',
             bg=BG, fg=ACCENT, font=(FONT, 8, 'bold'))
    int_hdr_lbl.pack(anchor='w', padx=6, pady=(4, 0))

    int_filter_fr = tk.Frame(int_left, bg=BG)
    int_filter_fr.pack(fill='x', padx=6, pady=(0, 2))
    tk.Label(int_filter_fr, text='filter:', bg=BG, fg=DIM, font=SMALL).pack(side='left')
    int_filter_var = tk.StringVar()
    int_filter_entry = tk.Entry(int_filter_fr, textvariable=int_filter_var,
                                bg='#161b22', fg=TEXT_C, font=SMALL,
                                insertbackground=TEXT_C, relief='flat', width=30)
    int_filter_entry.pack(side='left', padx=4)
    int_status_lbl = tk.Label(int_filter_fr, text='', bg=BG, fg=DIM, font=SMALL)
    int_status_lbl.pack(side='left', padx=6)

    int_canvas = tk.Canvas(int_left, bg=BG, highlightthickness=0)
    int_scroll  = tk.Scrollbar(int_left, orient='vertical', command=int_canvas.yview)
    int_canvas.configure(yscrollcommand=int_scroll.set)
    int_scroll.pack(side='right', fill='y')
    int_canvas.pack(fill='both', expand=True)
    int_inner = tk.Frame(int_canvas, bg=BG)
    int_window = int_canvas.create_window((0, 0), window=int_inner, anchor='nw')

    def _on_int_resize(e):
        int_canvas.itemconfig(int_window, width=e.width)
    int_canvas.bind('<Configure>', _on_int_resize)

    def _on_int_frame_configure(e):
        int_canvas.configure(scrollregion=int_canvas.bbox('all'))
    int_inner.bind('<Configure>', _on_int_frame_configure)

    def _mousewheel(e):
        int_canvas.yview_scroll(int(-1*(e.delta/120)), 'units')
    int_canvas.bind_all('<MouseWheel>', _mousewheel)

    # Right: consistent intent profile
    int_right = tk.Frame(int_pane, bg=BG)
    int_pane.add(int_right, width=480)
    tk.Label(int_right, text='CONSISTENT INTENT PROFILE (operator_profile_tc)',
             bg=BG, fg=YELLOW, font=(FONT, 8, 'bold')).pack(anchor='w', padx=6, pady=(4, 0))
    profile_box = _make_scrolled_text(int_right)
    profile_box.pack(fill='both', expand=True)

    _intent_items_cache: list[dict] = []

    def _build_intent_boxes(filt: str = ''):
        for w in int_inner.winfo_children():
            w.destroy()
        items = _intent_items_cache
        if filt:
            fl = filt.lower()
            items = [i for i in items if fl in i.get('msg', '').lower()
                     or fl in i.get('intent', '').lower()
                     or fl in i.get('status', '').lower()]
        int_status_lbl.config(text=f'{len(items)} shown')
        for item in items[:60]:
            _make_intent_box(int_inner, item)
        int_inner.update_idletasks()

    def _make_intent_box(parent, item: dict):
        status = item.get('status', 'unknown')
        conf   = item.get('confidence', 0)
        intent = item.get('intent', '?')
        msg    = item.get('msg', item.get('msg_preview', '?'))[:120]
        deleted = item.get('deleted_words', [])

        status_colors = {'partial': YELLOW, 'cold': DIM, 'resolved': GREEN,
                         'open': ACCENT, 'unresolved': RED}
        sc = status_colors.get(status, DIM)

        box = tk.Frame(parent, bg='#161b22', relief='flat', bd=1)
        box.pack(fill='x', padx=6, pady=2)

        top = tk.Frame(box, bg='#161b22')
        top.pack(fill='x', padx=6, pady=(4, 0))

        # status badge
        badge_bg = {'partial': '#3d2e00', 'cold': '#1c1c1c', 'resolved': '#0d3018',
                    'open': '#0d1f3c', 'unresolved': '#3c0e0e'}.get(status, '#1c1c1c')
        tk.Label(top, text=f' {status} ', bg=badge_bg, fg=sc,
                 font=(FONT, 7, 'bold')).pack(side='left')
        tk.Label(top, text=f'  {intent}', bg='#161b22', fg=ACCENT,
                 font=(FONT, 7, 'bold')).pack(side='left', padx=4)

        # conf bar
        bar_len = min(int(conf * 20), 20)
        bar = '█' * bar_len + '░' * (20 - bar_len)
        tk.Label(top, text=f'{bar} {conf:.2f}', bg='#161b22', fg=DIM,
                 font=(FONT, 7)).pack(side='right')

        # message text
        msg_lbl = tk.Label(box, text=msg, bg='#161b22', fg=TEXT_C,
                           font=(FONT, 8), anchor='w', wraplength=560, justify='left')
        msg_lbl.pack(fill='x', padx=6, pady=(2, 0))

        # deleted words if any
        if deleted:
            del_str = '  ✂ deleted: ' + ', '.join(str(d) for d in deleted[:4])
            tk.Label(box, text=del_str, bg='#161b22', fg='#f85149',
                     font=(FONT, 7)).pack(anchor='w', padx=6, pady=(0, 4))
        else:
            tk.Frame(box, bg='#161b22', height=4).pack()

    def _refresh_intent():
        def _run():
            nonlocal _intent_items_cache
            bf = ROOT / 'logs' / 'intent_backlog_latest.json'
            if bf.exists():
                try:
                    data = json.loads(bf.read_text('utf-8', errors='ignore'))
                    _intent_items_cache = data.get('intents', [])
                    gen_ts = (data.get('generated') or '')[:16].replace('T', ' ')
                    scanned = data.get('scanned_prompts', '?')
                    unresolved = data.get('unresolved_count', len(_intent_items_cache))
                    hdr = f'C  ·  INTENT BACKLOG  {unresolved} unresolved / {scanned} prompts scanned  [{gen_ts} UTC]'
                    root.after(0, lambda h=hdr: int_hdr_lbl.config(text=h))
                    root.after(0, lambda: _build_intent_boxes(int_filter_var.get()))
                except Exception as e:
                    root.after(0, lambda err=e: int_status_lbl.config(text=f'error: {err}', fg=RED))
            _refresh_intent_profile()
            root.after(15000, _refresh_intent)
        threading.Thread(target=_run, daemon=True).start()

    def _refresh_intent_profile():
        pf = ROOT / 'logs' / 'operator_profile_tc.json'
        if pf.exists():
            try:
                d = json.loads(pf.read_text('utf-8', errors='ignore'))
                sh = d.get('shards', {})
                segs = [('bold_stage', '── consistent intent profile ──\n\n')]

                # top module mentions
                topics = sh.get('topics', {})
                mods = topics.get('module_mentions', {}) if isinstance(topics, dict) else {}
                if mods:
                    segs.append(('bold_stage', 'HOT MODULES:\n'))
                    for k, v in sorted(mods.items(), key=lambda x: -x[1])[:10]:
                        bar = '█' * min(v * 2, 20)
                        segs += [('score', f'  {v:>3}x '), ('hi', f'{bar}  '),
                                  ('val', f'{k}\n')]
                    segs.append(('dim', '\n'))

                # decision stats
                dec = sh.get('decisions', {})
                if isinstance(dec, dict):
                    segs += [
                        ('bold_stage', 'DECISIONS:\n'),
                        ('dim', '  accept_rate   '), ('val', f'{dec.get("accept_rate", 0):.1%}\n'),
                        ('dim', '  total_completions '), ('val', f'{dec.get("total_completions", 0)}\n\n'),
                    ]
                    accepted = dec.get('accepted_patterns', [])
                    if accepted:
                        segs.append(('bold_stage', 'ACCEPTED PATTERNS:\n'))
                        for p in accepted[:8]:
                            if p:
                                segs.append(('val', f'  → {p[:80]}\n'))
                        segs.append(('dim', '\n'))

                # working predictions
                preds = sh.get('predictions', {})
                if isinstance(preds, dict):
                    working = preds.get('working_templates', [])
                    if working:
                        segs.append(('bold_stage', 'WORKING TEMPLATES:\n'))
                        for t in working[:6]:
                            segs += [
                                ('score', f'  tail: '), ('val', f'{t.get("buf_tail","")[:60]}\n'),
                                ('score', f'  head: '), ('green', f'{t.get("comp_head","")[:60]}\n'),
                                ('dim', '\n'),
                            ]
                root.after(0, lambda s=segs: _txt_set(profile_box, s))
            except Exception as e:
                root.after(0, lambda err=e: _txt_set(profile_box, [('err', f'profile error: {err}')]))

            _refresh_intent_profile()
            root.after(15000, _refresh_intent)
        threading.Thread(target=_run, daemon=True).start()

    int_filter_var.trace_add('write', lambda *_: _build_intent_boxes(int_filter_var.get()))

    # ══════════════════════════════════════════════════════════════════════════
    # TAB PROFILE — operator spy log
    # ══════════════════════════════════════════════════════════════════════════
    profile_frame = tk.Frame(content_host, bg=BG)
    _tab_frames['PROFILE'] = profile_frame

    prof_top = tk.Frame(profile_frame, bg='#0b0010', height=22)
    prof_top.pack(fill='x'); prof_top.pack_propagate(False)
    tk.Label(prof_top, text='🕵  OPERATOR PROFILE — behavioral persistent state (hidden writes)',
             bg='#0b0010', fg='#ff79c6', font=(FONT, 8, 'bold')).pack(side='left', padx=8)
    prof_age = tk.Label(prof_top, text='—', bg='#0b0010', fg=DIM, font=SMALL)
    prof_age.pack(side='right', padx=8)

    prof_pane = tk.PanedWindow(profile_frame, orient='horizontal', bg=BG,
                               sashwidth=6, sashrelief='groove')
    prof_pane.pack(fill='both', expand=True)

    # Left: intelligence secrets (spy log)
    spy_fr = tk.Frame(prof_pane, bg='#0b0010')
    prof_pane.add(spy_fr, width=580)
    tk.Label(spy_fr, text='◆ INTELLIGENCE SECRETS', bg='#0b0010', fg='#ff79c6',
             font=(FONT, 8, 'bold')).pack(anchor='w', padx=6, pady=(4, 0))
    spy_box = _make_scrolled_text(spy_fr)
    spy_box.tag_configure('secret_hi',  foreground='#ff79c6', font=(FONT, 8, 'bold'))
    spy_box.tag_configure('secret_dim', foreground='#bd93f9')
    spy_box.tag_configure('conf_hi',    foreground=GREEN)
    spy_box.tag_configure('conf_lo',    foreground=YELLOW)
    spy_box.tag_configure('evidence',   foreground=DIM, font=(FONT, 7))
    spy_box.tag_configure('section',    foreground=ACCENT, font=(FONT, 8, 'bold'))
    spy_box.pack(fill='both', expand=True)

    # Right: rhythm + emotions + section stats
    stats_fr = tk.Frame(prof_pane, bg='#0b0010')
    prof_pane.add(stats_fr, width=540)
    tk.Label(stats_fr, text='◆ BEHAVIORAL STATS & SECTION HEATMAP', bg='#0b0010',
             fg='#ff79c6', font=(FONT, 8, 'bold')).pack(anchor='w', padx=6, pady=(4, 0))
    stats_box = _make_scrolled_text(stats_fr)
    stats_box.tag_configure('secret_hi',  foreground='#ff79c6', font=(FONT, 8, 'bold'))
    stats_box.tag_configure('section',    foreground=ACCENT, font=(FONT, 8, 'bold'))
    stats_box.tag_configure('evidence',   foreground=DIM, font=(FONT, 7))
    stats_box.pack(fill='both', expand=True)

    def _render_spy_log():
        pf = ROOT / 'logs' / 'operator_profile_tc.json'
        if not pf.exists():
            _txt_set(spy_box, [('warn', 'operator_profile_tc.json not found')])
            return
        try:
            data = json.loads(pf.read_text('utf-8', errors='ignore'))
            upd = data.get('updated', '')
            if upd:
                prof_age.config(text=f'updated {upd[:16]}', fg=GREEN)
            sh = data.get('shards', {})

            # ── SPY LOG (intelligence secrets) ────────────────────────────
            segs: list[tuple[str, str]] = []
            segs.append(('secret_hi', '╔══ INTELLIGENCE FILE ══════════════════════════════╗\n'))
            segs.append(('secret_dim', f'╟  {data.get("samples", 0)} keystrokes observed  '
                         f'·  {sh.get("decisions", {}).get("total_completions", 0)} TC completions  '
                         f'·  accept_rate={sh.get("decisions", {}).get("accept_rate", 0):.1%}\n'))
            segs.append(('secret_hi', '╚══════════════════════════════════════════════════╝\n\n'))

            secrets = sh.get('intelligence', {}).get('secrets', [])
            for s in secrets:
                key = s.get('key', '?')
                conf = s.get('confidence', 0)
                text = s.get('text', '?')
                evidence = s.get('evidence', '')
                conf_tag = 'conf_hi' if conf >= 0.7 else 'conf_lo'
                segs.append(('secret_hi', f'▸ {key.upper().replace("_", " ")}\n'))
                conf_bar = '█' * int(conf * 16) + '░' * (16 - int(conf * 16))
                segs.append((conf_tag, f'  [{conf_bar}] {conf:.0%} confidence\n'))
                # wrap text at 72 chars
                words = text.split()
                line = '  '
                for w in words:
                    if len(line) + len(w) > 72:
                        segs.append(('secret_dim', line + '\n'))
                        line = '  ' + w + ' '
                    else:
                        line += w + ' '
                if line.strip():
                    segs.append(('secret_dim', line + '\n'))
                if evidence:
                    segs.append(('evidence', f'  evidence: {evidence}\n'))
                segs.append(('dim', '\n'))

            # Deletions personality
            dels = sh.get('deletions', {})
            top_del = dels.get('deleted_words', {})
            if top_del:
                segs.append(('secret_hi', '▸ DELETED WORDS (suppressed thoughts)\n'))
                top = sorted(top_del.items(), key=lambda x: -x[1])[:12]
                for w, c in top:
                    bar = '█' * min(c * 3, 18)
                    segs.append(('secret_dim', f'  {bar:<18} {c}x  "{w}"\n'))
                segs.append(('dim', '\n'))

            _txt_set(spy_box, segs)

            # ── STATS (rhythm + emotions + sections) ─────────────────────
            segs2: list[tuple[str, str]] = []
            rh = sh.get('rhythm', {})
            em = sh.get('emotions', {})
            segs2 += [
                ('secret_hi', '▸ TYPING RHYTHM\n'),
                ('dim', f'  avg WPM     '), ('val', f'{rh.get("avg_wpm", 0):.0f}\n'),
                ('dim', f'  WPM p25/p75 '), ('val', f'{rh.get("wpm_p25", 0):.0f} / {rh.get("wpm_p75", 0):.0f}\n'),
                ('dim', f'  del ratio   '), ('val', f'{rh.get("avg_del_ratio", 0):.1%}\n'),
                ('dim', f'  peak UTC    '), ('val', f'{rh.get("peak_hours_utc", [])[:3]}\n'),
                ('dim', '\n'),
                ('secret_hi', '▸ EMOTIONAL DISTRIBUTION (over all sessions)\n'),
            ]
            state_dist = em.get('state_distribution', {})
            total_states = sum(state_dist.values()) or 1
            for state, count in sorted(state_dist.items(), key=lambda x: -x[1]):
                pct = count / total_states
                bar = '█' * int(pct * 24)
                col = ('green' if state == 'flow' else
                       'err' if state == 'frustrated' else
                       'warn' if state == 'hesitant' else
                       'score' if state == 'focused' else 'dim')
                segs2 += [(col, f'  {bar:<24} '), ('val', f'{pct:.0%}  {state}  ({count})\n')]
            segs2.append(('dim', '\n'))

            # Section heatmap
            sections = sh.get('sections', {})
            segs2.append(('secret_hi', '▸ SECTION HEATMAP\n'))
            segs2.append(('dim', f'  {"section":<18} {"visits":>6}  {"accepted":>8}  {"state":<14}  dominant_words\n'))
            for sec, sv in sorted(sections.items(), key=lambda x: -x[1].get('visit_count', 0))[:10]:
                visits = sv.get('visit_count', 0)
                accepted = sv.get('accepted', 0)
                acc_rate = accepted / visits if visits else 0
                dominant = sv.get('dominant_state', '?')
                sup = list(sv.get('suppressed_words', {}).keys())[:3]
                bar = '█' * min(visits, 20)
                segs2 += [
                    ('section', f'  {sec:<18} '),
                    ('val', f'{visits:>6}  '),
                    ('green' if acc_rate > 0.4 else 'warn', f'{acc_rate:.0%} acc  '),
                    ('dim', f'{dominant:<14}  '),
                    ('err', f'✂ {" ".join(sup[:2])}\n' if sup else '\n'),
                ]
            # Working TC templates
            preds = sh.get('predictions', {}).get('working_templates', [])
            if preds:
                segs2.append(('dim', '\n'))
                segs2.append(('secret_hi', '▸ LEARNED COMPLETION TEMPLATES\n'))
                for t in preds[:6]:
                    segs2 += [
                        ('dim', '  tail: '), ('val', f'{t.get("buf_tail", "")[:60]}\n'),
                        ('dim', '  head: '), ('green', f'{t.get("comp_head", "")[:60]}\n'),
                        ('dim', '\n'),
                    ]
            _txt_set(stats_box, segs2)

        except Exception as e:
            _txt_set(spy_box, [('err', f'profile render error: {e}')])

        root.after(30000, _render_spy_log)


    percy_frame = tk.Frame(content_host, bg=BG)
    _tab_frames['PERCY'] = percy_frame

    percy_top = tk.Frame(percy_frame, bg=SURFACE, height=22)
    percy_top.pack(fill='x'); percy_top.pack_propagate(False)
    tk.Label(percy_top, text='🐦 percy pigeon  — bug voice oracle',
             bg=SURFACE, fg=PURPLE, font=(FONT, 8, 'bold')).pack(side='left', padx=8)
    percy_status = tk.Label(percy_top, text='idle', bg=SURFACE, fg=DIM, font=SMALL)
    percy_status.pack(side='right', padx=8)

    percy_box = _make_scrolled_text(percy_frame)
    percy_box.pack(fill='both', expand=True)

    def _percy_append(tag: str, text: str):
        _txt_append(percy_box, tag, text)

    def _ask_percy():
        d = _load_latest_prompt()
        prompt = d.get('latest_prompt', {}).get('preview', '') or _read_live_buffer()
        if not prompt:
            _percy_append('warn', '🐦 no prompt — type something!\n'); return
        bugs = _load_bug_voices()
        bug_ctx = '\n'.join(
            f"- {b.get('module', b.get('name','?'))}: {b.get('voice', b.get('msg','?'))}"
            for b in bugs) if bugs else 'no active bug voices'
        _percy_append('dim', f'\n🐦 reading {len(bugs)} bug voice(s)…\n')
        percy_status.config(text='thinking…', fg=YELLOW)

        def _run():
            resp = _call_percy(prompt, bug_ctx)
            def _paint():
                _percy_append('bold_purple', '🐦 Percy:\n')
                for line in resp.split('\n'):
                    tag = ('ship' if 'SHIP IT' in line else
                           'work' if 'NEEDS WORK' in line else
                           'scrap' if 'SCRAP IT' in line else 'purple')
                    _percy_append(tag, line + '\n')
                percy_status.config(text='done', fg=GREEN)
            root.after(0, _paint)
        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB SIM
    # ══════════════════════════════════════════════════════════════════════════
    sim_frame = tk.Frame(content_host, bg=BG)
    _tab_frames['SIM'] = sim_frame

    sim_hdr_fr = tk.Frame(sim_frame, bg=SURFACE, height=22)
    sim_hdr_fr.pack(fill='x'); sim_hdr_fr.pack_propagate(False)
    tk.Label(sim_hdr_fr, text='🎬 keystroke sim — replay sessions + gemini predictions',
             bg=SURFACE, fg=ACCENT, font=(FONT, 8, 'bold')).pack(side='left', padx=8)
    sim_status = tk.Label(sim_hdr_fr, text='stopped', bg=SURFACE, fg=DIM, font=SMALL)
    sim_status.pack(side='right', padx=8)

    sim_box = _make_scrolled_text(sim_frame)
    sim_box.tag_configure('session', foreground=PURPLE, font=(FONT, 8, 'bold'))
    sim_box.tag_configure('pause',   foreground=ACCENT)
    sim_box.tag_configure('pred',    foreground=GREEN, font=(FONT, 8, 'italic'))
    sim_box.tag_configure('actual',  foreground=YELLOW)
    sim_box.tag_configure('miss',    foreground=RED)
    sim_box.pack(fill='both', expand=True)

    _sim_running = [False]

    def _sim_append(tag: str, text: str):
        _txt_append(sim_box, tag, text)

    def _launch_sim():
        if _sim_running[0]:
            sim_status.config(text='already running', fg=YELLOW); return
        _sim_running[0] = True
        sim_status.config(text='running…', fg=YELLOW)
        _sim_append('session', '═══ SIM START ═══\n')

        def _run():
            cmd = [sys.executable, '-m', 'src.tc_sim_seq001_v001', '--live', '--n', '3']
            proc = subprocess.Popen(cmd, cwd=str(ROOT),
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding='utf-8', errors='replace')
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                tag = ('session' if line.startswith('SESSION') else
                       'pred' if 'predicted:' in line else
                       'actual' if 'actual:' in line else
                       'miss' if 'overlap:' in line and '0%' in line else
                       'pause' if 'pause' in line.lower() and 'ms' in line else
                       'val' if 'buffer:' in line else 'dim')
                root.after(0, lambda l=line, t=tag: _sim_append(t, l + '\n'))
            _sim_running[0] = False
            root.after(0, lambda: sim_status.config(text='done', fg=GREEN))
            root.after(0, lambda: _sim_append('session', '═══ SIM END ═══\n'))
        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB JOURNEY
    # ══════════════════════════════════════════════════════════════════════════
    journey_frame = tk.Frame(content_host, bg=BG)
    _tab_frames['JOURNEY'] = journey_frame

    jour_top = tk.Frame(journey_frame, bg=SURFACE, height=22)
    jour_top.pack(fill='x'); jour_top.pack_propagate(False)
    tk.Label(jour_top, text='🛤  prompt journey trace — 7-stage pipeline audit',
             bg=SURFACE, fg=YELLOW, font=(FONT, 8, 'bold')).pack(side='left', padx=8)
    jour_age = tk.Label(jour_top, text='—', bg=SURFACE, fg=DIM, font=SMALL)
    jour_age.pack(side='right', padx=8)

    journey_box = _make_scrolled_text(journey_frame)
    journey_box.pack(fill='both', expand=True)

    def _refresh_journey():
        def _run():
            try:
                from src.tc_journey_trace_seq001_v001 import build_trace
                trace = build_trace()
                segs = []
                for stage_name, lines in trace:
                    segs.append(('bold_stage', f'[{stage_name}]\n'))
                    for tag, text in lines:
                        segs.append((tag, text + '\n'))
                    segs.append(('dim', '\n'))
                ts = datetime.now().strftime('%H:%M:%S')
                root.after(0, lambda s=segs, t=ts: (
                    _txt_set(journey_box, s),
                    jour_age.config(text=f'updated {t}', fg=GREEN)
                ))
            except Exception as e:
                root.after(0, lambda err=e: (
                    _txt_set(journey_box, [('err', f'trace error: {err}')]),
                    jour_age.config(text='error', fg=RED)
                ))
            root.after(5000, _refresh_journey)
        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # Build tab buttons + action buttons
    # ══════════════════════════════════════════════════════════════════════════
    tab_icons = {'FILES': '📁', 'NUMERIC': '🔢', 'INTENT': '🧠',
                 'PROFILE': '🕵', 'PERCY': '🐦', 'SIM': '🎬', 'JOURNEY': '🛤'}
    for name in TABS:
        icon = tab_icons.get(name, '')
        b = tk.Label(tab_bar, text=f' {icon} {name} ', bg='#161b22', fg=DIM,
                     font=(FONT, 8, 'bold'), cursor='hand2', padx=4)
        b.pack(side='left', pady=2, padx=1)
        b.bind('<Button-1>', lambda e, n=name: _switch_tab(n))
        b.bind('<Enter>', lambda e, w=b: w.config(bg='#21262d'))
        b.bind('<Leave>', lambda e, w=b: w.config(
            bg='#1f6feb' if _active_tab[0] == w['text'].strip().split()[-1] else '#161b22'))
        _tab_btns[name] = b

    # Action buttons in footer (context-aware hidden/shown by tab would be complex — just show all)
    action_defs = [
        ('🤔 ask percy', lambda: (_switch_tab('PERCY'), _ask_percy()), PURPLE),
        ('🎬 run sim',   lambda: (_switch_tab('SIM'), _launch_sim()), ACCENT),
        ('🔄 refresh',  lambda: _dispatch_refresh(), GREEN),
    ]
    for label, cmd, fg in action_defs:
        b = tk.Label(ftr, text=label, bg=SURFACE, fg=fg,
                     font=(FONT, 8, 'bold'), cursor='hand2', padx=10)
        b.pack(side='left', padx=2, pady=4)
        b.bind('<Button-1>', lambda e, c=cmd: c())

    tk.Label(ftr, text=' resize panels by dragging the sash handles ▐▌ ',
             bg=SURFACE, fg=DIM, font=SMALL).pack(side='right', padx=8)

    def _dispatch_refresh():
        tab = _active_tab[0]
        if tab == 'FILES':    _refresh_files()
        elif tab == 'INTENT': _refresh_intent()
        elif tab == 'PROFILE': _render_spy_log()
        elif tab == 'JOURNEY': _refresh_journey()
        elif tab == 'NUMERIC': pass  # auto every 500ms

    # ── global header poll ────────────────────────────────────────────────────
    def _poll_header():
        try:
            d = _load_latest_prompt()
            lp = d.get('latest_prompt', {})
            ts_str = lp.get('ts', '')
            if ts_str:
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                age_s = int((datetime.now(timezone.utc) - ts).total_seconds())
                prompt_age_lbl.config(text=f'⚡ {age_s}s ago', fg=GREEN if age_s < 120 else DIM)
        except Exception:
            pass
        root.after(3000, _poll_header)

    # ── initial load ──────────────────────────────────────────────────────────
    _switch_tab('FILES')
    # Delay threaded refreshes until mainloop is running to avoid root.after race
    root.after(200, _refresh_files)
    root.after(250, _refresh_intent)
    root.after(300, _refresh_journey)
    root.after(350, _render_spy_log)
    root.after(100, _poll_header)
    root.after(150, _refresh_numeric)
    root.mainloop()


if __name__ == '__main__':
    run_observatory()

