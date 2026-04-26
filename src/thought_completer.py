"""thought_completer.py — passive always-on-top code analysis overlay.

Watches your VS Code typing (via os_hook's keystroke log), shows real-time
code analysis in a corner popup when you pause. Catches bugs, suggests
next steps, spots missing pieces — not sentence completion.

Launch:  py src/thought_completer.py
         py src/thought_completer.py --corner tr --pause 1500
         py src/thought_completer.py --compose
         py src/thought_completer.py --intent-key "wire manifest intent keys"
         py src/thought_completer.py --prompt-brain "typing buffer to assemble"
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
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from src._resolve import src_import
import os
import sys
import importlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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
_load_api_key = src_import("tc_gemini_seq001", "_load_api_key")
run_popup = src_import("tc_popup_seq001", "run_popup")
run_web = src_import("tc_web_seq001", "run_web")


def _launch_observatory():
    import subprocess as _sp
    from pathlib import Path as _Path
    target_matches = sorted((_Path(_root_dir) / "src").glob("tc_observatory*.py"))
    if not target_matches:
        print("[completer] observatory not found")
        return None
    flags = getattr(_sp, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    module_name = f"src.{target_matches[-1].stem}"
    return _sp.Popen([sys.executable, "-m", module_name], cwd=_root_dir,
                     creationflags=flags)


def main():
    import argparse
    p = argparse.ArgumentParser(description='thought completer — passive overlay')
    p.add_argument('--web', action='store_true', help='web server mode (Railway)')
    p.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8235')))
    p.add_argument('--sim-buffer', help='run a single tc pause sim for this buffer and exit')
    p.add_argument('--intent-key', help='generate a manifest-backed intent key for this prompt and exit')
    p.add_argument('--prompt-brain', help='assemble full watcher context bundle for this prompt and exit')
    p.add_argument('--compose', action='store_true', help='open controlled prompt composer with pre-prompt injection')
    p.add_argument('--compose-sim-timeout', type=int, default=20, help='seconds to wait for composer sim')
    p.add_argument('--compose-auto-clear', action='store_true', help='clear composer after successful inject+copy')
    p.add_argument('--corner', default=DEFAULT_CORNER, choices=['tl', 'tr', 'bl', 'br'])
    p.add_argument('--pause', type=int, default=DEFAULT_PAUSE_MS)
    p.add_argument('--width', type=int, default=DEFAULT_WIDTH)
    p.add_argument('--height', type=int, default=DEFAULT_HEIGHT)
    p.add_argument('--opacity', type=float, default=DEFAULT_OPACITY)
    p.add_argument('--observatory', action='store_true', help='also launch pigeon observatory window')
    p.add_argument('--onboard', action='store_true', help='10-question onboarding → operator baseline + write mode')
    p.add_argument('--write', action='store_true', help='interactive write-with-it loop (no VS Code needed)')
    p.add_argument('--no-gemini', action='store_true', help='skip Gemini API (heat map only, use with --write/--onboard)')
    args = p.parse_args()

    if args.intent_key:
        import json as _json
        from pathlib import Path as _Path
        from src.tc_intent_keys_seq001_v001 import generate_intent_key
        result = generate_intent_key(_Path(_root_dir), args.intent_key, emit_prompt_box=True, inject=True)
        print(_json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if args.prompt_brain:
        import json as _json
        from pathlib import Path as _Path
        from src.tc_prompt_brain_seq001_v001 import assemble_prompt_brain
        result = assemble_prompt_brain(
            _Path(_root_dir),
            args.prompt_brain,
            source="thought_completer_cli",
            trigger="manual",
            emit_prompt_box=False,
            inject=True,
        )
        print(_json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # ── interactive modes (no popup, no tkinter) ──
    if args.onboard or args.write:
        from src.tc_onboard_seq001_v001 import run_onboard, run_write
        use_gemini = not args.no_gemini
        if use_gemini and not _load_api_key():
            print('[completer] WARNING: no GEMINI_API_KEY — completions disabled')
            use_gemini = False
        if args.onboard:
            run_onboard(use_gemini=use_gemini)
        else:
            run_write(use_gemini=use_gemini)
        return 0

    if args.compose:
        if args.observatory:
            _launch_observatory()
        from src.tc_prompt_composer_seq001_v001 import run_prompt_composer
        run_prompt_composer(root=_root_dir, sim_timeout_s=args.compose_sim_timeout,
                            auto_clear=args.compose_auto_clear)
        return 0

    if not _load_api_key():
        print('[completer] WARNING: no GEMINI_API_KEY in .env or environment')

    if args.sim_buffer:
        predict_files = src_import("intent_numeric_seq001", "predict_files")
        run_pause_sim = src_import("tc_sim_engine_seq001", "run_sim")

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
            _launch_observatory()
        run_popup(args.corner, args.pause, args.width, args.height, args.opacity,
                  surface_ready=_surface_ready)


if __name__ == '__main__':
    raise SystemExit(main() or 0)
