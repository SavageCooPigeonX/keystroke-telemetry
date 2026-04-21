"""context_select_agent — intent orchestrator. Fires on every prompt submission.

Assembles the copilot instruction layer dynamically using:
  - Intent keys: msg + deleted_words + rewrites → augmented intent string
  - Numeric encoding: predict_files(intent_keys) → ranked files
  - Stale block detection: flags pigeon blocks older than their max-age threshold
  - Copilot layer patch: live-rewrites pigeon:current-query block
  - TC steering: writes logs/tc_steer.json for thought_completer to load on next poll

Zero LLM calls. Pure numeric signal assembly.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 195 lines | ~1,814 tokens
# DESC:   intent_orchestrator_fires_on_every
# INTENT: feat_operator_state_daemon
# LAST:   2026-04-21 @ f9a3310
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-20T22:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  context select orchestration manager
# EDIT_AUTHOR: copilot
# EDIT_STATE: active
# ── /pulse ──
from __future__ import annotations
import json
import re
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

COPILOT_PATH   = '.github/copilot-instructions.md'
CS_PATH        = 'logs/context_selection.json'
STEER_PATH     = 'logs/tc_steer.json'

# Stale thresholds per block (seconds)
STALE_THRESHOLDS: dict[str, int] = {
    'current-query':   600,    # 10 min — this block should always be fresh
    'task-context':    3600,   # 1 hr
    'operator-state':  1800,   # 30 min
    'prompt-telemetry': 600,   # 10 min
    'task-queue':      3600,   # 1 hr
    'organism-health': 86400,  # 1 day
}

# Regex to find timestamps in block headers like: *Auto-injected 2026-04-14 02:49 UTC*
_TS_RE = re.compile(
    r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:\s*UTC)?',
)
_BLOCK_RE = re.compile(
    r'<!-- pigeon:([^/\s>]+) -->(.*?)<!-- /pigeon:\1 -->',
    re.DOTALL,
)


def compile_intent(msg: str, deleted_words: list, rewrites: list) -> str:
    """Build augmented intent string from msg + deleted signal."""
    parts = [msg]
    if deleted_words:
        parts.append(' '.join(str(w) for w in deleted_words[:15]))
    for rw in rewrites[:4]:
        if isinstance(rw, (list, tuple)) and len(rw) >= 2:
            parts.append(f'{rw[0]} {rw[1]}')
        elif isinstance(rw, str):
            parts.append(rw)
    return ' '.join(parts)


def detect_stale_blocks(root: Path) -> list[str]:
    """Return list of pigeon block names that are past their staleness threshold."""
    cp = root / COPILOT_PATH
    if not cp.exists():
        return []
    text = cp.read_text(encoding='utf-8', errors='ignore')
    now = datetime.now(timezone.utc)
    stale = []
    for m in _BLOCK_RE.finditer(text):
        name, body = m.group(1), m.group(2)
        thresh = STALE_THRESHOLDS.get(name)
        if thresh is None:
            continue
        ts_m = _TS_RE.search(body[:300])
        if not ts_m:
            stale.append(name)
            continue
        try:
            raw = ts_m.group().replace(' UTC', '+00:00').replace(' ', 'T')
            if '+' not in raw and 'Z' not in raw:
                raw += '+00:00'
            block_ts = datetime.fromisoformat(raw)
            if (now - block_ts).total_seconds() > thresh:
                stale.append(name)
        except Exception:
            stale.append(name)
    return stale


def _predict(root: Path, intent_text: str, top_n: int = 6) -> list[dict]:
    """Run predict_files via intent_numeric. Returns [{name, score}]."""
    try:
        matches = sorted(root.glob('src/intent_numeric_seq001*.py'), key=len)
        if not matches:
            return []
        spec = importlib.util.spec_from_file_location('_in', matches[0])
        if spec is None or spec.loader is None:
            return []
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        results = mod.predict_files(intent_text, top_n=top_n)
        return [{'name': r[0], 'score': round(r[1], 4)} for r in results if isinstance(r, (list, tuple))]
    except Exception:
        return []


def _patch_current_query(root: Path, buffer: str, files: list[dict],
                          stale_blocks: list[str]) -> None:
    """Rewrite pigeon:current-query block in copilot-instructions.md."""
    cp = root / COPILOT_PATH
    if not cp.exists():
        return
    text = cp.read_text(encoding='utf-8', errors='ignore')
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    file_list = ', '.join(f['name'] for f in files[:5]) or 'none'
    stale_str  = ', '.join(stale_blocks) if stale_blocks else 'none'
    new_body = (
        f'\n## What You Actually Mean Right Now\n\n'
        f'*Assembled {now} · context_select_agent · zero LLM calls*\n\n'
        f'**INTENT KEYS:** `{buffer[:200]}`\n\n'
        f'**FILES:** {file_list}\n\n'
        f'**STALE BLOCKS:** {stale_str}\n'
    )
    new_block = f'<!-- pigeon:current-query -->{new_body}<!-- /pigeon:current-query -->'
    updated = re.sub(
        r'<!-- pigeon:current-query -->.*?<!-- /pigeon:current-query -->',
        new_block,
        text,
        flags=re.DOTALL,
    )
    if updated != text:
        cp.write_text(updated, encoding='utf-8')


def run_assembly(root, msg: str, deleted_words: list, rewrites: list) -> dict:
    """Main entry — fires on every prompt submission via u_pj.log_enriched_entry."""
    root = Path(root)
    intent_keys = compile_intent(msg, deleted_words, rewrites)
    files        = _predict(root, intent_keys)
    stale_blocks = detect_stale_blocks(root)
    confidence   = round(files[0]['score'], 4) if files else 0.0
    ts           = datetime.now(timezone.utc).isoformat()

    result = {
        'ts':           ts,
        'buffer':       msg[:200],
        'intent_keys':  intent_keys[:300],
        'files':        files,
        'stale_blocks': stale_blocks,
        'confidence':   confidence,
    }

    # Write context_selection.json
    cs_path = root / CS_PATH
    cs_path.parent.mkdir(parents=True, exist_ok=True)
    cs_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    # Write tc_steer.json — TC polls this before Gemini call
    steer_path = root / STEER_PATH
    steer_path.write_text(json.dumps({
        'ts':         ts,
        'intent_keys': intent_keys[:300],
        'files':      [f['name'] for f in files[:5]],
        'stale_blocks': stale_blocks,
        'confidence': confidence,
    }, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    # Patch copilot-instructions.md current-query block
    _patch_current_query(root, intent_keys, files, stale_blocks)

    return result


if __name__ == '__main__':
    import sys
    _root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    _msg  = sys.argv[2] if len(sys.argv) > 2 else ''
    _dw   = json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
    _rw   = json.loads(sys.argv[4]) if len(sys.argv) > 4 else []
    out = run_assembly(_root, _msg, _dw, _rw)
    print(json.dumps({
        'intent_keys': out['intent_keys'][:100],
        'files': [f['name'] for f in out['files'][:3]],
        'stale_blocks': out['stale_blocks'],
        'confidence': out['confidence'],
    }, indent=2))
