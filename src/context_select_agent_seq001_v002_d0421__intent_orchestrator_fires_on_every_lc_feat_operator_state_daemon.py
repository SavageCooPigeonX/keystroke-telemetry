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
# EDIT_TS:   2026-04-23T17:05:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  add symbol keys and core routing
# EDIT_AUTHOR: copilot
# EDIT_STATE: active
# ── /pulse ──
from __future__ import annotations
import hashlib
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


def _normalize_raw_deleted(raw: str) -> str:
    """Best-effort decode of interleaved keydown/keyup chars from keystroke hook.

    The hook fires on both keydown and keyup, producing interleaved pairs.
    We collapse consecutive repeated characters as a heuristic approximation.
    """
    import re as _re
    s = raw.strip()
    if not s:
        return ''
    # Collapse runs of 2+ identical adjacent chars to 1
    cleaned = _re.sub(r'(.)\1+', r'\1', s)
    # Remove isolated digits (keyboard noise)
    cleaned = _re.sub(r'\b\d+\b', '', cleaned)
    cleaned = _re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _load_latest_unsaid(root: Path) -> tuple[str, str]:
    """Read the most recent composition + unsaid entry.

    Returns (deleted_summary, reconstructed_intent):
      - deleted_summary: human-readable description of what was removed
        (derived from peak_buffer vs final_text, not the garbled raw chars)
      - reconstructed_intent: LLM interpretation of the deleted signal
    """
    recon_path = root / 'logs' / 'unsaid_reconstructions.jsonl'
    comp_path  = root / 'logs' / 'chat_compositions.jsonl'
    recon_intent = ''
    deleted_summary = ''

    # Get LLM-reconstructed intent from unsaid log
    if recon_path.exists():
        try:
            lines = recon_path.read_text('utf-8', errors='ignore').strip().splitlines()
            if lines:
                entry = json.loads(lines[-1])
                recon_intent = (entry.get('reconstructed_intent', '')
                                or entry.get('thought_completion', '')).strip()
        except Exception:
            pass

    # Get deleted summary from composition: peak_buffer had MORE text than final
    # The difference shows what the operator originally typed then removed
    if comp_path.exists():
        try:
            lines = comp_path.read_text('utf-8', errors='ignore').strip().splitlines()
            # Find most recent entry with actual deletions
            for line in reversed(lines[-20:]):
                try:
                    entry = json.loads(line)
                    raw_words = entry.get('intent_deleted_words') or entry.get('deleted_words', [])
                    if not raw_words:
                        continue
                    n_deleted = len(raw_words)
                    del_ratio = entry.get('intent_deletion_ratio', entry.get('deletion_ratio', 0))
                    total_chars = entry.get('total_keystrokes', 0)
                    # Show count + ratio as the summary (raw chars are undecodable)
                    if n_deleted > 0:
                        deleted_summary = (
                            f'{n_deleted} intentional deletion(s) '
                            f'({del_ratio:.0%} of keystrokes)'
                        )
                    break
                except Exception:
                    continue
        except Exception:
            pass

    return deleted_summary, recon_intent


def compile_intent(msg: str, deleted_words: list, rewrites: list) -> str:
    """Build augmented intent string from msg + deleted signal."""
    parts = [msg]
    if deleted_words:
        # Normalize doubled-char raw keystrokes before including in intent
        normalized = [_normalize_raw_deleted(str(w)) for w in deleted_words[:15]]
        parts.append(' '.join(w for w in normalized if len(w) > 1))
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
        matches = sorted(root.glob('src/intent_numeric_seq001*.py'), key=lambda p: len(p.name))
        if not matches:
            return []
        spec = importlib.util.spec_from_file_location('_in', matches[0])
        if spec is None or spec.loader is None:
            return []
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        results = mod.predict_files(intent_text, top_n=top_n)
        # predict_files returns list[dict] with 'name'/'score' keys
        out = []
        for r in results:
            if isinstance(r, dict):
                out.append({'name': r.get('name', ''), 'score': round(float(r.get('score', 0)), 4)})
            elif isinstance(r, (list, tuple)) and len(r) >= 2:
                out.append({'name': r[0], 'score': round(float(r[1]), 4)})
        return out
    except Exception:
        return []


def _symbol_keys(intent_text: str, max_n: int = 48) -> list[str]:
    """Extract normalized symbol keys that help routing and sim targeting."""
    keys = []
    seen = set()
    for raw in re.findall(r'[A-Za-z_][A-Za-z0-9_\-]{2,}', intent_text.lower()):
        key = raw.strip('_-')
        if not key or key in seen:
            continue
        seen.add(key)
        keys.append(key)
        if len(keys) >= max_n:
            break
    return keys


def _template_mode(root: Path) -> str:
    """Match template mode to active bug + commit signal."""
    try:
        dossier = json.loads((root / 'logs' / 'active_dossier.json').read_text('utf-8'))
        if dossier.get('focus_bugs'):
            return 'debug'
    except Exception:
        pass
    return 'build'


def _pending_intents(root: Path, n: int = 10) -> list[str]:
    """Collect pending intent ids from task queue for closure loops."""
    path = root / 'task_queue.json'
    if not path.exists():
        return []
    try:
        queue = json.loads(path.read_text('utf-8'))
    except Exception:
        return []
    out = []
    for task in queue.get('tasks', []):
        if task.get('status') == 'done':
            continue
        tid = str(task.get('id', '')).strip()
        if tid:
            out.append(tid)
        if len(out) >= n:
            break
    return out


def _priority_files(root: Path, files: list[dict], n: int = 10) -> list[str]:
    """Prioritize stems for sim/deepseek by selector score + known bug pressure."""
    ranked = []
    for f in files:
        stem = str(f.get('name', '')).strip()
        if stem:
            ranked.append((stem, float(f.get('score', 0.0))))

    reg_path = root / 'pigeon_registry.json'
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text('utf-8'))
            entries = reg if isinstance(reg, list) else reg.get('files', [])
            for e in entries:
                stem = str(e.get('name', '') or e.get('stem', '')).strip()
                if not stem:
                    continue
                bugs = e.get('bugs', [])
                if not bugs:
                    continue
                bug_boost = 0.0
                if any(b in ('oc', 'over_hard_cap') for b in bugs):
                    bug_boost += 0.35
                if any(b in ('hi', 'hardcoded_import') for b in bugs):
                    bug_boost += 0.30
                if any(b in ('de', 'dead_export') for b in bugs):
                    bug_boost += 0.15
                ranked.append((stem, bug_boost))
        except Exception:
            pass

    merged: dict[str, float] = {}
    for stem, score in ranked:
        merged[stem] = merged.get(stem, 0.0) + score

    ordered = sorted(merged.items(), key=lambda x: x[1], reverse=True)
    return [stem for stem, _ in ordered[:n]]


def _core_routing(root: Path, intent_keys: str, files: list[dict], stale_blocks: list[str], symbol_keys: list[str]) -> dict:
    """Build routing payload consumed by copilot + sim loops."""
    mode = _template_mode(root)
    pending = _pending_intents(root)
    priority = _priority_files(root, files)
    intent_hash = hashlib.sha256(intent_keys.encode('utf-8', errors='ignore')).hexdigest()[:12]
    return {
        'selector_version': 'context_select_v003',
        'intent_hash': intent_hash,
        'template_mode': mode,
        'symbol_keys': symbol_keys,
        'stale_blocks': stale_blocks,
        'sim_inputs': {
            'priority_files': priority,
            'top_files': [f.get('name', '') for f in files[:8]],
            'pending_intent_ids': pending,
        },
        'artifacts': {
            'context_selection': CS_PATH,
            'tc_steer': STEER_PATH,
            'intent_jobs': 'logs/intent_jobs.jsonl',
            'sim_results': 'logs/sim_results.jsonl',
            'task_queue': 'task_queue.json',
        },
        'closure_loop': {
            'goal': 'drive priority files to 10q/interlinked sleep state',
            'driver': 'scripts/priority_closure_loop.py',
            'max_files_per_cycle': 10,
        },
    }


def _patch_current_query(root: Path, buffer: str, files: list[dict],
                          stale_blocks: list[str], symbol_keys: list[str],
                          core_routing: dict) -> None:
    """Rewrite pigeon:current-query block in copilot-instructions.md."""
    cp = root / COPILOT_PATH
    if not cp.exists():
        return
    text = cp.read_text(encoding='utf-8', errors='ignore')
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    file_list = ', '.join(f['name'] for f in files[:5]) or 'none'
    stale_str  = ', '.join(stale_blocks) if stale_blocks else 'none'
    symbol_str = ', '.join(symbol_keys[:12]) if symbol_keys else 'none'
    route_files = core_routing.get('sim_inputs', {}).get('priority_files', [])
    route_str = ', '.join(route_files[:8]) if route_files else 'none'
    route_mode = core_routing.get('template_mode', 'build')
    deleted_readable, recon_intent = _load_latest_unsaid(root)
    unsaid_line = recon_intent.strip() if recon_intent else 'none'
    deleted_line = deleted_readable if deleted_readable else 'none'
    new_body = (
        f'\n## What You Actually Mean Right Now\n\n'
        f'*Assembled {now} · context_select_agent · zero LLM calls*\n\n'
        f'**INTENT KEYS:** `{buffer[:200]}`\n\n'
        f'**FILES:** {file_list}\n\n'

        f'**SYMBOL KEYS:** {symbol_str}\n\n'

        f'**CORE ROUTING:** mode={route_mode} | sim_priority={route_str}\n\n'

        f'**STALE BLOCKS:** {stale_str}\n\n'
        f'**DELETED WORDS (reconstructed):** {deleted_line}\n\n'
        f'**UNSAID_RECONSTRUCTION:** {unsaid_line}\n'
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
    symbol_keys  = _symbol_keys(intent_keys)
    stale_blocks = detect_stale_blocks(root)
    core_routing = _core_routing(root, intent_keys, files, stale_blocks, symbol_keys)
    confidence   = round(files[0]['score'], 4) if files else 0.0
    ts           = datetime.now(timezone.utc).isoformat()

    result = {
        'ts':           ts,
        'buffer':       msg[:200],
        'intent_keys':  intent_keys[:300],
        'symbol_keys':  symbol_keys,
        'files':        files,
        'stale_blocks': stale_blocks,
        'core_routing': core_routing,
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
        'symbol_keys': symbol_keys,
        'files':      [f['name'] for f in files[:5]],
        'stale_blocks': stale_blocks,
        'template_mode': core_routing.get('template_mode', 'build'),
        'sim_priority_files': core_routing.get('sim_inputs', {}).get('priority_files', []),
        'pending_intent_ids': core_routing.get('sim_inputs', {}).get('pending_intent_ids', []),
        'confidence': confidence,
    }, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    # Patch copilot-instructions.md current-query block
    _patch_current_query(root, intent_keys, files, stale_blocks, symbol_keys, core_routing)

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
