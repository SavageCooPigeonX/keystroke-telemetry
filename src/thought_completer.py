"""thought_completer.py — passive always-on-top code analysis overlay.

Watches your VS Code typing (via os_hook's keystroke log), shows real-time
code analysis in a corner popup when you pause. Catches bugs, suggests
next steps, spots missing pieces — not sentence completion.

Launch:  py src/thought_completer.py
         py src/thought_completer.py --corner tr --pause 1500
         py src/thought_completer.py --sim-buffer "audit stale data points"
         py src/thought_completer.py --web --port 8235  (Railway mode)

Split into modules: tc_constants_seq001_v001, tc_vscode_seq001_v001, tc_context_seq001_v001_agent_seq001_v001, tc_context_seq001_v001,
tc_gemini_seq001_v001, tc_buffer_watcher_seq001_v001, tc_popup_seq001_v001, tc_web_seq001_v001. This file is the entrypoint.

Hotkeys (global when popup is focused):
    Ctrl+Shift+C   — copy analysis to clipboard
    Ctrl+Shift+X   — dismiss analysis
    Ctrl+Q         — quit

The popup auto-detects which repo you're in from VS Code window titles
and switches context accordingly.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import os
import sys
import importlib

# ensure src/ is importable — but bypass src/__init__.py which has many
# pigeon-renamed imports that break. We only need tc_* modules.
_src_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_src_dir)
sys.path.insert(0, _root_dir)

# Prevent src/__init__.py from executing by marking the package as already loaded
import types
if 'src' not in sys.modules:
    _pkg = types.ModuleType('src')
    _pkg.__path__ = [_src_dir]
    _pkg.__package__ = 'src'
    sys.modules['src'] = _pkg

from src.tc_constants_seq001_v001 import DEFAULT_PAUSE_MS, DEFAULT_CORNER, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_OPACITY
from src.tc_gemini_seq001_v002_d0420__gemini_api_call_system_prompt_lc_chore_pigeon_rename_cascade import _load_api_key
from src.tc_popup_seq001_v003_d0420__passive_always_on_top_tkinter_lc_chore_pigeon_rename_cascade import run_popup
from src.tc_web_seq001_v001 import run_web


def main():
    import argparse
    p = argparse.ArgumentParser(description='thought completer — passive overlay')
    p.add_argument('--web', action='store_true', help='web server mode (Railway)')
    p.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8235')))
    p.add_argument('--sim-buffer', help='run a single tc pause sim for this buffer and exit')
    p.add_argument('--corner', default=DEFAULT_CORNER, choices=['tl', 'tr', 'bl', 'br'])
    p.add_argument('--pause', type=int, default=DEFAULT_PAUSE_MS)
    p.add_argument('--width', type=int, default=DEFAULT_WIDTH)
    p.add_argument('--height', type=int, default=DEFAULT_HEIGHT)
    p.add_argument('--opacity', type=float, default=DEFAULT_OPACITY)
    p.add_argument('--observatory', action='store_true', help='also launch pigeon observatory window')
    args = p.parse_args()

    if not _load_api_key():
        print('[completer] WARNING: no GEMINI_API_KEY in .env or environment')

    if args.sim_buffer:
        from src.intent_numeric_seq001_v003_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade import predict_files
        from src.tc_sim_engine_seq001_v003_d0420__intent_simulation_on_typing_pause_lc_create_sim_engine import run_sim as run_pause_sim

        buffer = args.sim_buffer.strip()
        if not buffer:
            print('[sim] empty buffer')
            return 1

        predictions = predict_files(buffer, top_n=5)
        winner = run_pause_sim(buffer)

        print(f'[sim] buffer: {buffer}')
        if predictions:
            print('[sim] numeric shortlist:')
            for name, score in predictions:
                print(f'  {score:.4f}  {name}')
        else:
            print('[sim] numeric shortlist: none')

        if winner:
            print(f'[sim] winner: {winner.name}  score={winner.score:.3f}')
            print(f'[sim] files: {", ".join(winner.files) if winner.files else "(none)"}')
            print(f'[sim] completion: {winner.completion or "(empty)"}')
        else:
            print('[sim] no winner')

        print(f'[sim] log: {os.path.join(_root_dir, "logs", "tc_sim_results.jsonl")}')
        print(f'[sim] reinjection: {os.path.join(_root_dir, "logs", "tc_intent_reinjection.json")}')
        return 0

    # Refresh numeric surface on startup — gate first completion until done
    import threading
    _surface_ready = threading.Event()
    def _refresh_surface():
        try:
            import subprocess as _sp
            _sp.run(
                [sys.executable, '-c',
                 'import sys; sys.path.insert(0,".")\n'
                 'from pathlib import Path\n'
                 'from src.numeric_surface_seq001_v001_seq001_v001 import generate_surface\n'
                 'generate_surface(Path("."))'],
                cwd=_root_dir, timeout=60, capture_output=True
            )
            print('[completer] numeric_surface_seq001_v001 refreshed')
        except Exception as _e:
            print(f'[completer] numeric_surface_seq001_v001 refresh failed: {_e}')
        finally:
            _surface_ready.set()
    threading.Thread(target=_refresh_surface, daemon=True).start()

    if args.web or os.environ.get('PORT'):
        run_web(args.port)
    else:
        if getattr(args, 'observatory', False):
            import subprocess as _sp
            import sys as _sys
            import os as _os
            _cwd = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            _sp.Popen([_sys.executable, '-m', 'src.tc_observatory_seq001_v001'],
                      cwd=_cwd)
        run_popup(args.corner, args.pause, args.width, args.height, args.opacity,
                  surface_ready=_surface_ready)


if __name__ == '__main__':
    raise SystemExit(main() or 0)
