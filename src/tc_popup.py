"""Desktop popup — passive always-on-top tkinter overlay."""
from __future__ import annotations
import json
import time
import threading

from .tc_constants import (ROOT, KEYSTROKE_LOG, LOG_PATH, GEMINI_MODEL,
                           POLL_INTERVAL_MS)
from .tc_vscode import _detect_repo_from_title
from .tc_context import invalidate_context_cache
from .tc_gemini import ThoughtBuffer, call_gemini, log_completion
from .tc_buffer_watcher import BufferWatcher
from .tc_profile import update_profile_from_completion, update_profile_from_composition
from .tc_grader import grade_completion, log_grade, update_grade_summary


def run_popup(corner='br', pause_ms=1500, width=520, height=220, opacity=0.92):
    import tkinter as tk

    BG = '#0d1117'
    SURFACE = '#161b22'
    TEXT_C = '#e6edf3'
    GHOST_C = '#6e7681'
    ACCENT = '#58a6ff'
    GREEN = '#3fb950'
    RED = '#f85149'
    DIM = '#8b949e'
    FONT = 'Cascadia Code'

    class App:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title('thought completer')
            self.root.overrideredirect(True)
            self.root.configure(bg=BG)
            self.root.attributes('-topmost', True)
            self.root.attributes('-alpha', opacity)
            self.root.protocol('WM_DELETE_WINDOW', self._quit)

            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            pad = 12
            pos = {
                'br': (sw - width - pad, sh - height - pad - 48),
                'bl': (pad, sh - height - pad - 48),
                'tr': (sw - width - pad, pad),
                'tl': (pad, pad),
            }
            x, y = pos.get(corner, pos['br'])
            self.root.geometry(f'{width}x{height}+{x}+{y}')

            self.watcher = BufferWatcher(KEYSTROKE_LOG)
            self.thought_buffer = ThoughtBuffer()
            self.completion = ''
            self.completion_buffer = ''
            self.n_accepted = 0
            self.n_rejected = 0
            self._grade_counter = 0
            self._comp_line_count = 0  # tracks last-seen composition line
            self.pause_after_id = None
            self.completing = False
            self.current_repo = _detect_repo_from_title() or ROOT.name
            self._completed_buffer = None
            self._last_nonempty_buf = ''
            self._last_fire_time = 0.0
            self._fire_cooldown = 2.0
            self.drag_x = 0
            self.drag_y = 0

            self._build_ui()
            self._bind_keys()
            self._start_polling()

        def _build_ui(self):
            r = self.root
            small = (FONT, 8)

            hdr = tk.Frame(r, bg=SURFACE, height=22)
            hdr.pack(fill='x')
            hdr.pack_propagate(False)
            hdr.bind('<Button-1>', self._drag_start)
            hdr.bind('<B1-Motion>', self._drag_motion)

            tk.Label(hdr, text='\U0001f9e0 thought completer', bg=SURFACE,
                     fg=ACCENT, font=(FONT, 8, 'bold')).pack(side='left', padx=6)
            self.repo_lbl = tk.Label(hdr, text=self.current_repo, bg=SURFACE,
                                     fg=DIM, font=small)
            self.repo_lbl.pack(side='left', padx=4)
            self.stats_lbl = tk.Label(hdr, text='\u2713 0  \u2717 0', bg=SURFACE,
                                      fg=DIM, font=small)
            self.stats_lbl.pack(side='right', padx=2)
            self.status_lbl = tk.Label(hdr, text='watching', bg=SURFACE,
                                       fg=DIM, font=small)
            self.status_lbl.pack(side='right', padx=4)

            close_btn = tk.Label(hdr, text=' \u2715 ', bg=SURFACE, fg=RED,
                                 font=(FONT, 10, 'bold'), cursor='hand2')
            close_btn.pack(side='right', padx=0)
            close_btn.bind('<Button-1>', lambda e: self._quit())
            close_btn.bind('<Enter>', lambda e: close_btn.config(bg='#da3633'))
            close_btn.bind('<Leave>', lambda e: close_btn.config(bg=SURFACE))

            min_btn = tk.Label(hdr, text=' \u2500 ', bg=SURFACE, fg=DIM,
                               font=(FONT, 10), cursor='hand2')
            min_btn.pack(side='right', padx=0)
            min_btn.bind('<Button-1>', lambda e: self.root.iconify())
            min_btn.bind('<Enter>', lambda e: min_btn.config(bg='#30363d'))
            min_btn.bind('<Leave>', lambda e: min_btn.config(bg=SURFACE))

            self.text_box = tk.Text(r, bg=BG, fg=TEXT_C, font=(FONT, 11),
                                    wrap='word', borderwidth=0, highlightthickness=0,
                                    padx=10, pady=8, cursor='arrow',
                                    state='disabled', spacing1=2, spacing3=2)
            self.text_box.pack(fill='both', expand=True)
            self.text_box.tag_configure('buffer', foreground=TEXT_C)
            self.text_box.tag_configure('completion', foreground=GREEN,
                                        font=(FONT, 11, 'italic'))
            self.text_box.tag_bind('completion', '<Button-1>', self._accept)

            thought_sep = tk.Frame(r, bg='#30363d', height=1)
            thought_sep.pack(fill='x')
            thought_hdr = tk.Frame(r, bg=SURFACE, height=16)
            thought_hdr.pack(fill='x')
            thought_hdr.pack_propagate(False)

            self._panel_mode = 'history'
            self.panel_title = tk.Label(thought_hdr, text='\U0001f4ad thought history',
                                        bg=SURFACE, fg=DIM, font=(FONT, 7, 'bold'))
            self.panel_title.pack(side='left', padx=6)
            self.toggle_btn = tk.Label(thought_hdr, text='\U0001f50d inspector', bg=SURFACE,
                                       fg=GHOST_C, font=(FONT, 7), cursor='hand2')
            self.toggle_btn.pack(side='right', padx=6)
            self.toggle_btn.bind('<Button-1>', lambda e: self._toggle_panel())
            self.toggle_btn.bind('<Enter>', lambda e: self.toggle_btn.config(fg=ACCENT))
            self.toggle_btn.bind('<Leave>', lambda e: self.toggle_btn.config(fg=GHOST_C))

            self.thought_box = tk.Text(r, bg='#0b0e14', fg=DIM, font=(FONT, 9),
                                       wrap='word', borderwidth=0, highlightthickness=0,
                                       padx=8, pady=4, cursor='arrow',
                                       state='disabled', height=6, spacing1=1, spacing3=1)
            self.thought_box.pack(fill='both', expand=True)
            for tag, fg in [('rewarded', '#f0c040'), ('accepted', GREEN),
                            ('dismissed', RED), ('ignored', '#484f58'),
                            ('superseded', '#8b949e'), ('outcome_icon', ACCENT)]:
                self.thought_box.tag_configure(tag, foreground=fg)
            self.thought_box.tag_configure('topic', foreground=ACCENT, font=(FONT, 8, 'italic'))
            for tag, fg, extra in [('insp_ts', '#484f58', {}), ('insp_buf', TEXT_C, {}),
                                   ('insp_comp', GREEN, {'font': (FONT, 8, 'italic')}),
                                   ('insp_reward', '#f0c040', {'font': (FONT, 8, 'bold')}),
                                   ('insp_ctx', '#8b949e', {'font': (FONT, 7)}),
                                   ('insp_sep', '#30363d', {})]:
                self.thought_box.tag_configure(tag, foreground=fg, **extra)
            self._refresh_thought_history()

            ftr = tk.Frame(r, bg=SURFACE, height=18)
            ftr.pack(fill='x')
            ftr.pack_propagate(False)
            tk.Label(ftr, text='ctrl+z paste \u00b7 ctrl+shift+x dismiss \u00b7 type in VS Code',
                     bg=SURFACE, fg=GHOST_C, font=(FONT, 7)).pack(side='left', padx=6)
            self.ctx_lbl = tk.Label(ftr, text='editor', bg=SURFACE, fg=DIM, font=(FONT, 7))
            self.ctx_lbl.pack(side='right', padx=6)
            self.toast_lbl = tk.Label(r, text='', bg=GREEN, fg='#000', font=(FONT, 9, 'bold'))

        def _bind_keys(self):
            self.root.bind('<Control-Shift-KeyPress-C>', self._accept)
            self.root.bind('<Control-Shift-KeyPress-c>', self._accept)
            self.root.bind('<Control-Shift-KeyPress-X>', self._dismiss)
            self.root.bind('<Control-Shift-KeyPress-x>', self._dismiss)
            self.root.bind('<Control-z>', self._accept)
            self.root.bind('<Control-Z>', self._accept)
            self.root.bind('<Control-q>', lambda e: self._quit())
            # Global hotkeys — fire even when popup is not focused
            try:
                import keyboard as _kb
                _kb.add_hotkey('ctrl+z', lambda: self.root.after(0, self._accept), suppress=False)
                _kb.add_hotkey('ctrl+shift+x', lambda: self.root.after(0, self._dismiss), suppress=False)
            except Exception as _e:
                print(f'[completer] global hotkeys unavailable: {_e}')

        def _drag_start(self, event):
            self.drag_x = event.x
            self.drag_y = event.y

        def _drag_motion(self, event):
            x = self.root.winfo_x() + event.x - self.drag_x
            y = self.root.winfo_y() + event.y - self.drag_y
            self.root.geometry(f'+{x}+{y}')

        def _start_polling(self):
            self._poll_tick()
            self._repo_tick()
            self._composition_tick()
            # rebuild grade summary at startup so self-learning prompt has fresh data
            threading.Thread(target=update_grade_summary, daemon=True).start()

        def _poll_tick(self):
            changed = self.watcher.poll()
            buf = self.watcher.buffer.strip()
            ctx = self.watcher.context
            now = time.time()
            now_ms = now * 1000
            self.ctx_lbl.config(text=ctx)

            if changed and self.watcher.last_event_type == 'undo' and self.completion:
                self._reward()
                self.root.after(POLL_INTERVAL_MS, self._poll_tick)
                return

            if changed:
                if buf:
                    self._last_nonempty_buf = buf
                if not buf:
                    self._completed_buffer = None
                elif self._completed_buffer and len(buf) > len(self._completed_buffer) + 15:
                    self._completed_buffer = None
                if not buf and self.completion:
                    self.thought_buffer.record(self.completion_buffer, self.completion, 'ignored')
                    update_profile_from_completion(self.completion_buffer, self.completion, 'ignored')
                    self._grade_and_log(self.completion_buffer, self.completion, 'ignored')
                    self._log(False, buf)
                    self.completion = ''
                    self.completion_buffer = ''
                    self._refresh_thought_history()
                self._refresh_display(buf)
                if self.pause_after_id:
                    self.root.after_cancel(self.pause_after_id)
                    self.pause_after_id = None
                self.completing = False
                self.status_lbl.config(text='typing...', fg=DIM)
            else:
                check_buf = buf or self._last_nonempty_buf
                last_key_ts = self.watcher.last_ts
                since_key_ms = (now_ms - last_key_ts) if last_key_ts > 0 else 0
                since_fire = now - self._last_fire_time
                cooldown_ok = since_fire >= self._fire_cooldown
                buf_ok = check_buf and len(check_buf) >= 4
                not_busy = not self.completing
                not_dup = self._completed_buffer != check_buf
                not_pending = self.pause_after_id is None

                if not hasattr(self, '_dbg_t') or now - self._dbg_t > 5:
                    self._dbg_t = now
                    if since_key_ms > 1000:
                        why = []
                        if not buf_ok: why.append(f'buf_short({len(check_buf) if check_buf else 0})')
                        if not not_busy: why.append('busy')
                        if not not_dup: why.append('dup')
                        if not not_pending: why.append('pending')
                        if not cooldown_ok: why.append(f'cd({self._fire_cooldown - since_fire:.0f}s)')
                        if self.completion: why.append('has_completion')
                        blk = '|'.join(why) if why else 'none'
                        tail = repr(check_buf[-30:]) if check_buf else 'empty'
                        print(f'[dbg] age={since_key_ms:.0f}ms can={buf_ok and not_busy and not_dup and not_pending and cooldown_ok} '
                              f'block={blk} buf={tail}')

                can_complete = (buf_ok and not_busy and last_key_ts > 0
                                and not_pending and cooldown_ok and not_dup)
                if can_complete and since_key_ms >= pause_ms:
                    print(f'[poll] FIRE key_age={since_key_ms:.0f}ms buf={check_buf[-40:]!r}')
                    self._last_fire_time = now
                    self._completed_buffer = check_buf
                    self.status_lbl.config(text='thinking...', fg=ACCENT)
                    self.pause_after_id = self.root.after(
                        0, lambda b=check_buf: self._request_completion(b))
                elif last_key_ts > 0 and since_key_ms < pause_ms and since_key_ms > 0:
                    self.status_lbl.config(text='typing...', fg=DIM)
                elif can_complete and since_key_ms > 500:
                    secs_left = max(0, (pause_ms - since_key_ms) / 1000)
                    self.status_lbl.config(text=f'pause {secs_left:.1f}s', fg=DIM)
                elif not cooldown_ok and not self.completion:
                    cd_left = max(0, self._fire_cooldown - since_fire)
                    self.status_lbl.config(text=f'cooldown {cd_left:.0f}s', fg=DIM)
                elif not can_complete and not self.completion and not self.completing:
                    self.status_lbl.config(text='watching', fg=DIM)

            self.root.after(POLL_INTERVAL_MS, self._poll_tick)

        def _repo_tick(self):
            repo = _detect_repo_from_title()
            if repo and repo != self.current_repo:
                self.current_repo = repo
                self.repo_lbl.config(text=repo)
                invalidate_context_cache()
            self.root.after(3000, self._repo_tick)

        def _composition_tick(self):
            """Poll chat_compositions.jsonl for new entries → feed to profile."""
            try:
                comp_path = ROOT / 'logs' / 'chat_compositions.jsonl'
                if comp_path.exists():
                    lines = comp_path.read_text('utf-8', errors='ignore').strip().splitlines()
                    total = len(lines)
                    if self._comp_line_count == 0:
                        # first run — start from current position, don't backfill
                        self._comp_line_count = total
                    elif total > self._comp_line_count:
                        new_lines = lines[self._comp_line_count:]
                        self._comp_line_count = total
                        for line in new_lines[-5:]:  # max 5 at a time
                            try:
                                entry = json.loads(line)
                                update_profile_from_composition(entry)
                            except Exception:
                                continue
            except Exception as ex:
                print(f'[comp-watch] error: {ex}')
            self.root.after(5000, self._composition_tick)

        def _refresh_display(self, buf):
            self.text_box.config(state='normal')
            self.text_box.delete('1.0', 'end')
            display = buf[-300:] if buf else 'waiting for input in VS Code...'
            self.text_box.insert('end', display, 'buffer')
            if self.completion:
                self.text_box.insert('end', self.completion, 'completion')
            self.text_box.config(state='disabled')
            self.text_box.see('end')

        def _refresh_thought_history(self):
            if self._panel_mode == 'inspector':
                self._refresh_inspector()
                return
            self.thought_box.config(state='normal')
            self.thought_box.delete('1.0', 'end')
            entries = self.thought_buffer.entries[-8:]
            if not entries:
                self.thought_box.insert('end', '  no thoughts yet \u2014 completions will appear here\n', 'ignored')
            else:
                for e in entries:
                    outcome = e.get('outcome', '?')
                    icon = {'rewarded': '\u2b50', 'accepted': '\u2713', 'dismissed': '\u2717',
                            'ignored': '\u00b7', 'superseded': '\u21bb'}.get(outcome, '?')
                    tag = outcome if outcome in ('rewarded', 'accepted', 'dismissed', 'ignored', 'superseded') else 'ignored'
                    self.thought_box.insert('end', f'{icon} ', 'outcome_icon')
                    self.thought_box.insert('end', e.get('buf', '')[-30:], 'ignored')
                    self.thought_box.insert('end', ' \u2192 ', 'outcome_icon')
                    self.thought_box.insert('end', e.get('comp', '')[:50], tag)
                    self.thought_box.insert('end', '\n')
            if self.thought_buffer.topics:
                self.thought_box.insert('end', '\u2022 ', 'outcome_icon')
                self.thought_box.insert('end', ', '.join(self.thought_buffer.topics[-3:]), 'topic')
            self.thought_box.config(state='disabled')
            self.thought_box.see('end')

        def _toggle_panel(self):
            if self._panel_mode == 'history':
                self._panel_mode = 'inspector'
                self.panel_title.config(text='\U0001f50d completion inspector')
                self.toggle_btn.config(text='\U0001f4ad history')
                self._refresh_inspector()
            else:
                self._panel_mode = 'history'
                self.panel_title.config(text='\U0001f4ad thought history')
                self.toggle_btn.config(text='\U0001f50d inspector')
                self._refresh_thought_history()

        def _refresh_inspector(self):
            self.thought_box.config(state='normal')
            self.thought_box.delete('1.0', 'end')
            if not LOG_PATH.exists():
                self.thought_box.insert('end', '  no completions logged yet\n', 'ignored')
                self.thought_box.config(state='disabled')
                return
            try:
                lines = LOG_PATH.read_text('utf-8', errors='ignore').strip().splitlines()
                entries = []
                for line in lines[-15:]:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        continue
                if not entries:
                    self.thought_box.insert('end', '  no completions logged yet\n', 'ignored')
                    self.thought_box.config(state='disabled')
                    return
                for e in reversed(entries[-10:]):
                    ts = e.get('ts', '?')
                    if len(ts) > 19:
                        ts = ts[11:19]
                    accepted = e.get('accepted', False)
                    reward = e.get('reward', False)
                    buf = e.get('buffer', '')[-50:]
                    comp = e.get('completion', '')[:80]
                    ctx_name = e.get('context', '?')
                    repo = e.get('repo', '?')
                    if reward:
                        icon, tag = '\u2b50', 'insp_reward'
                    elif accepted:
                        icon, tag = '\u2713', 'accepted'
                    else:
                        icon, tag = '\u2717', 'dismissed'
                    self.thought_box.insert('end', f'{ts} ', 'insp_ts')
                    self.thought_box.insert('end', f'{icon} ', tag)
                    self.thought_box.insert('end', buf, 'insp_buf')
                    self.thought_box.insert('end', '\n')
                    self.thought_box.insert('end', f'  \u2192 {comp}', 'insp_comp')
                    self.thought_box.insert('end', '\n')
                    self.thought_box.insert('end', f'  [{ctx_name} \u00b7 {repo}]', 'insp_ctx')
                    self.thought_box.insert('end', '\n')
                    self.thought_box.insert('end', '\u2500' * 40 + '\n', 'insp_sep')
            except Exception as ex:
                self.thought_box.insert('end', f'  error reading log: {ex}\n', 'dismissed')
            self.thought_box.config(state='disabled')
            self.thought_box.see('1.0')

        def _request_completion(self, buf):
            self.pause_after_id = None
            if self.completing:
                return
            current = self.watcher.buffer.strip()
            if current != buf or len(buf) < 4:
                return
            self.completing = True
            self.status_lbl.config(text='analyzing...', fg=ACCENT)

            def _do():
                t0 = time.time()
                result, ctx_files = call_gemini(buf, self.thought_buffer)
                lat = int((time.time() - t0) * 1000)
                print(f'[completer] latency={lat}ms len={len(result) if result else 0}')
                self.root.after(0, lambda: self._show(buf, result, lat, ctx_files))

            threading.Thread(target=_do, daemon=True).start()

        def _show(self, buf, completion, latency_ms=0, context_files=None):
            self.completing = False
            self.pause_after_id = None
            self._last_latency_ms = latency_ms
            self._last_context_files = context_files or []
            current = self.watcher.buffer.strip()
            if not completion or current != buf:
                self.status_lbl.config(text='watching', fg=DIM)
                return
            if self.completion and self.completion_buffer:
                self.thought_buffer.record(self.completion_buffer, self.completion, 'superseded')
                update_profile_from_completion(self.completion_buffer, self.completion, 'superseded')
                self._grade_and_log(self.completion_buffer, self.completion, 'superseded')
            self.completion = completion
            self.completion_buffer = buf
            self._refresh_display(buf)
            self._refresh_thought_history()
            self.status_lbl.config(text='ctrl+z reward', fg=GREEN)

        def _accept(self, event=None):
            if not self.completion:
                return
            full_text = self.completion
            self.root.clipboard_clear()
            self.root.clipboard_append(full_text)
            self.root.update()
            self._log(True, self.watcher.buffer)
            self.thought_buffer.record(self.completion_buffer, full_text, 'accepted')
            update_profile_from_completion(self.completion_buffer, full_text, 'accepted')
            self._grade_and_log(self.completion_buffer, full_text, 'accepted')
            self.n_accepted += 1
            self._update_stats()
            self._toast('copied!', GREEN)
            self.completion = ''
            self.completion_buffer = ''
            self._refresh_display(self.watcher.buffer.strip())
            self._refresh_thought_history()
            self.status_lbl.config(text='watching', fg=DIM)

        def _reward(self):
            if not self.completion:
                return
            full_text = self.completion
            self.root.clipboard_clear()
            self.root.clipboard_append(full_text)
            self.root.update()
            log_completion({
                'buffer': self.completion_buffer[:2000],
                'completion': self.completion[:500],
                'accepted': True,
                'reward': True,
                'reward_source': 'ctrl_z',
                'final_text': (self.watcher.buffer or '')[:2000],
                'repo': self.current_repo,
                'context': self.watcher.context,
                'latency_ms': int((time.time() - self._last_fire_time) * 1000) if self._last_fire_time else 0,
            })
            self.thought_buffer.record(self.completion_buffer, full_text, 'rewarded')
            update_profile_from_completion(self.completion_buffer, full_text, 'rewarded')
            self._grade_and_log(self.completion_buffer, full_text, 'rewarded')
            self.n_accepted += 1
            self._update_stats()
            self._toast('\u2705 rewarded!', GREEN)
            print(f'[reward] ctrl+z accepted: {self.completion[:60]!r}')
            self.completion = ''
            self.completion_buffer = ''
            self._refresh_display(self.watcher.buffer.strip())
            self._refresh_thought_history()
            self.status_lbl.config(text='rewarded \u2713', fg=GREEN)

        def _dismiss(self, event=None):
            if not self.completion:
                return
            self.thought_buffer.record(self.completion_buffer, self.completion, 'dismissed')
            update_profile_from_completion(self.completion_buffer, self.completion, 'dismissed')
            self._grade_and_log(self.completion_buffer, self.completion, 'dismissed')
            self._log(False, self.watcher.buffer)
            self.n_rejected += 1
            self._update_stats()
            self.completion = ''
            self.completion_buffer = ''
            self._refresh_display(self.watcher.buffer.strip())
            self._refresh_thought_history()
            self.status_lbl.config(text='dismissed', fg=RED)

        def _log(self, accepted, final_text):
            if not self.completion:
                return
            log_completion({
                'buffer': self.completion_buffer[:2000],
                'completion': self.completion[:500],
                'accepted': accepted,
                'final_text': (final_text or '')[:2000],
                'repo': self.current_repo,
                'context': self.watcher.context,
                'context_files': getattr(self, '_last_context_files', []),
                'latency_ms': getattr(self, '_last_latency_ms', 0),
            })

        def _grade_and_log(self, buf, completion, outcome):
            """Grade completion and log to grades file. Runs summary every 10."""
            try:
                ctx_files = getattr(self, '_last_context_files', [])
                latency = getattr(self, '_last_latency_ms', 0)
                g = grade_completion(buf, completion, outcome,
                                     context_files=ctx_files,
                                     latency_ms=latency)
                log_grade(g)
                self._grade_counter += 1
                if self._grade_counter % 10 == 0:
                    threading.Thread(target=update_grade_summary, daemon=True).start()
            except Exception as ex:
                print(f'[grader] error: {ex}')

        def _update_stats(self):
            self.stats_lbl.config(text=f'\u2713 {self.n_accepted}  \u2717 {self.n_rejected}')

        def _toast(self, msg, color):
            self.toast_lbl.config(text=f'  {msg}  ', bg=color)
            self.toast_lbl.place(relx=0.5, rely=0.5, anchor='center')
            self.root.after(1200, lambda: self.toast_lbl.place_forget())

        def _quit(self):
            self.root.destroy()

        def run(self):
            self.root.mainloop()

    print(f'[thought completer] passive overlay | corner={corner} pause={pause_ms}ms')
    print(f'[thought completer] model: {GEMINI_MODEL}')
    print(f'[thought completer] watching: {KEYSTROKE_LOG}')
    print(f'[thought completer] log: {LOG_PATH}')
    app = App()
    app.run()
