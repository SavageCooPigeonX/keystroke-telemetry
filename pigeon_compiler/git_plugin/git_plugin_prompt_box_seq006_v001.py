"""git_plugin_prompt_box_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from pigeon_compiler.session_logger import log_session, count_sessions
import ast
import re

def _build_box(entry: dict, h: str, lines: int, tokens: int = 0,
               sessions: int = 0) -> str:
    return (
        f'# ── pigeon ────────────────────────────────────\n'
        f'# SEQ: {entry["seq"]:03d} | VER: v{entry["ver"]:03d} | {lines} lines | ~{tokens:,} tokens\n'
        f'# DESC:   {entry.get("desc") or "(none)"}\n'
        f'# INTENT: {entry.get("intent") or "(none)"}\n'
        f'# LAST:   {datetime.now(timezone.utc).strftime("%Y-%m-%d")} @ {h}\n'
        f'# SESSIONS: {sessions}\n'
        f'# ──────────────────────────────────────────────\n'
    )


def _inject_box(fp: Path, entry: dict, h: str, root: Path | None = None):
    try:
        text = fp.read_text(encoding='utf-8')
    except Exception:
        return
    tokens = _estimate_tokens(text)
    sessions = 0
    if root:
        sessions = count_sessions(root, entry.get('name', ''), entry.get('seq', 0))
    box = _build_box(entry, h, len(text.splitlines()), tokens, sessions)
    if '# ── pigeon ─' in text:
        text = BOX_RE.sub(box, text, count=1)
    else:
        end = _ds_end(text)
        if end >= 0:
            text = text[:end] + '\n' + box + text[end:]
        else:
            text = box + text
    fp.write_text(text, encoding='utf-8')


def _ds_end(text: str) -> int:
    """Character index right after the module docstring."""
    try:
        tree = ast.parse(text)
        if not tree.body:
            return -1
        n = tree.body[0]
        if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str)):
            return sum(len(l) + 1 for l in text.split('\n')[:n.end_lineno])
    except SyntaxError:
        pass
    return -1
