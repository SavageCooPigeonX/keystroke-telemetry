"""thought_completer.py — passive always-on-top code analysis overlay.

Watches your VS Code typing (via os_hook's keystroke log), shows real-time
code analysis in a corner popup when you pause. Catches bugs, suggests
next steps, spots missing pieces — not sentence completion.

Launch:  py src/thought_completer.py
         py src/thought_completer.py --corner tr --pause 1500
         py src/thought_completer.py --web --port 8235  (Railway mode)

Split into modules: tc_constants, tc_vscode, tc_context_agent, tc_context,
tc_gemini, tc_buffer_watcher, tc_popup, tc_web. This file is the entrypoint.

Hotkeys (global when popup is focused):
    Ctrl+Shift+C   — copy analysis to clipboard
    Ctrl+Shift+X   — dismiss analysis
    Ctrl+Q         — quit

The popup auto-detects which repo you're in from VS Code window titles
and switches context accordingly.
"""
from __future__ import annotations
import os
import sys

# ensure src/ is importable as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tc_constants import DEFAULT_PAUSE_MS, DEFAULT_CORNER, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_OPACITY
from src.tc_gemini import _load_api_key
from src.tc_popup import run_popup
from src.tc_web import run_web


def main():
    import argparse
    p = argparse.ArgumentParser(description='thought completer — passive overlay')
    p.add_argument('--web', action='store_true', help='web server mode (Railway)')
    p.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8235')))
    p.add_argument('--corner', default=DEFAULT_CORNER, choices=['tl', 'tr', 'bl', 'br'])
    p.add_argument('--pause', type=int, default=DEFAULT_PAUSE_MS)
    p.add_argument('--width', type=int, default=DEFAULT_WIDTH)
    p.add_argument('--height', type=int, default=DEFAULT_HEIGHT)
    p.add_argument('--opacity', type=float, default=DEFAULT_OPACITY)
    args = p.parse_args()

    if not _load_api_key():
        print('[completer] WARNING: no GEMINI_API_KEY in .env or environment')

    if args.web or os.environ.get('PORT'):
        run_web(args.port)
    else:
        run_popup(args.corner, args.pause, args.width, args.height, args.opacity)


if __name__ == '__main__':
    main()
