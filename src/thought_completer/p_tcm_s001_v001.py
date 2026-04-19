"""thought_completer_main_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 26 lines | ~309 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from src.tc_constants_seq001_v001 import DEFAULT_PAUSE_MS, DEFAULT_CORNER, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_OPACITY
from src.tc_gemini_seq001_v001 import _load_api_key
from src.tc_popup_seq001_v001 import run_popup
from src.tc_web_seq001_v001 import run_web
import os

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
