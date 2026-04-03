"""u_pj_s019_v002_d0402_λC_log_enriched_decomposed_seq016_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re

def log_enriched_entry(root: Path, msg: str, files_open: list[str],
                       session_n: int) -> dict:
    """Build and append one fully-enriched journal entry. Returns the entry.

    Signal/narrative separation:
    1. Write raw measured signal to prompt_signal_raw.jsonl (ground truth)
    2. Build enriched entry with interpretation (intent, state, predictions)
    3. Enriched entry is tagged with provenance markers
    """
    now = datetime.now(timezone.utc)
    _force_fresh_composition(root)
    _refresh_prompt_compositions(root)
    comp_match = _select_composition(root, now, msg, session_n=session_n)
    comp = comp_match['entry'] if comp_match else None

    # Extract signals from composition if available
    signals = {}
    deleted_words = []
    rewrites = []
    cog_state = 'unknown'
    binding = {
        'matched': False,
        'source': None,
        'age_ms': None,
        'key': None,
    }
    if comp_match and comp:
        binding = {
            'matched': True,
            'source': comp_match['source'],
            'age_ms': comp_match['age_ms'],
            'key': comp_match['key'],
            'match_score': round(comp_match['match_score'], 3),
        }
        cs = comp.get('chat_state', comp.get('signals', {}))
        sigs = cs.get('signals', cs) if isinstance(cs, dict) else {}
        signals = {
            'wpm':                sigs.get('wpm', 0),
            'chars_per_sec':      sigs.get('chars_per_sec', 0),
            'deletion_ratio':     sigs.get('deletion_ratio', comp.get('deletion_ratio', 0)),
            'hesitation_count':   sigs.get('hesitation_count', 0),
            'rewrite_count':      sigs.get('rewrite_count', 0),
            'typo_corrections':   comp.get('typo_corrections', sigs.get('typo_corrections', 0)),
            'intentional_deletions': comp.get('intentional_deletions', sigs.get('intentional_deletions', 0)),
            'total_keystrokes':   comp.get('total_keystrokes', 0),
            'duration_ms':        comp.get('duration_ms', 0),
        }
        cog_state = cs.get('state', 'unknown') if isinstance(cs, dict) else 'unknown'
        deleted_words = [w.get('word', w) if isinstance(w, dict) else w
                         for w in comp.get('deleted_words', [])]
        rewrites = comp.get('rewrites', [])

    # ── STEP 1: Write raw signal (measured truth only) ──
    try:
        import importlib.util
        _sig_matches = sorted(root.glob('src/片w_sm_s026*.py'))
        if _sig_matches:
            _sig_spec = importlib.util.spec_from_file_location('_prompt_signal', _sig_matches[-1])
            if _sig_spec and _sig_spec.loader:
                _sig_mod = importlib.util.module_from_spec(_sig_spec)
                _sig_spec.loader.exec_module(_sig_mod)
                _sig_mod.log_raw_signal(
                    root=root, msg=msg, files_open=files_open,
                    session_n=session_n, signals=signals,
                    deleted_words=deleted_words, rewrites=rewrites,
                    composition_binding=binding,
                )
    except Exception:
        pass  # raw signal write is best-effort — journal still works without it

    # ── STEP 2: Build enriched entry (raw + interpretation) ──
    entry = {
        'ts':               now.isoformat(),
        'session_n':        session_n,
        'msg':              msg,
        'msg_len':          len(msg),
        'files_open':       files_open,
        # ── classification (DERIVED — not in raw signal) ──
        'intent':           _classify_intent(msg),
        'module_refs':      _extract_module_refs(msg),
        'cognitive_state':  cog_state,
        # ── typing signals (MEASURED — also in raw signal) ──
        'signals':          signals,
        'composition_binding': binding,
        'deleted_words':    deleted_words,
        'rewrites':         rewrites,
        # ── context snapshot (DERIVED — point-in-time system state) ──
        'task_queue':       _active_tasks(root),
        'hot_modules':      _hot_modules(root),
        'prompt_mutations': _mutation_count(root),
        # ── running stats (DERIVED — aggregated from history) ──
        'running':          _running_stats(root),
        # ── provenance tag ──
        'provenance': {
            'measured': ['ts', 'session_n', 'msg', 'msg_len', 'files_open',
                         'signals', 'deleted_words', 'rewrites', 'composition_binding'],
            'derived':  ['intent', 'module_refs', 'cognitive_state',
                         'task_queue', 'hot_modules', 'prompt_mutations', 'running'],
        },
    }

    # Append
    journal_path = root / JOURNAL_PATH
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with open(journal_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    entry['_root'] = root  # transient — used by _build_snapshot for coaching bullets
    snapshot = _build_snapshot(entry)
    entry.pop('_root', None)  # don't persist in journal
    _write_latest_snapshot(root, snapshot)
    _refresh_copilot_instructions(root, snapshot)

    # ── Gemini prompt enrichment — inject what operator actually means ──
    # NOTE: classify_bridge also fires this on every submit (primary path).
    # This is the fallback path — fires from the journal command.
    try:
        import importlib.util as _ilu, glob as _g
        _matches = sorted(root.glob('src/u_pe_s024*.py'))
        if _matches:
            _spec = _ilu.spec_from_file_location('_enricher', _matches[-1])
            if _spec is not None and _spec.loader is not None:
                _mod = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)
                _mod.inject_query_block(
                    root, msg,
                    deleted_words=deleted_words,
                    cognitive_state={
                        'state': cog_state,
                        'wpm': signals.get('wpm', 0),
                        'del_ratio': signals.get('deletion_ratio', 0),
                        'hes': signals.get('hesitation_count', 0),
                    },
                )
    except Exception as _enrich_err:
        # Log enricher failures so they're not invisible
        try:
            _err_path = root / 'logs' / 'enricher_errors.jsonl'
            _err_path.parent.mkdir(parents=True, exist_ok=True)
            with open(_err_path, 'a', encoding='utf-8') as _ef:
                _ef.write(json.dumps({
                    'ts': datetime.now(timezone.utc).isoformat(),
                    'error': str(_enrich_err),
                    'msg_preview': msg[:80],
                }) + '\n')
        except Exception:
            pass

    # ── Training pair (prompt-side) — response backfilled by rework detector ──
    try:
        import importlib.util as _tw_ilu
        _tw_matches = sorted(root.glob('src/训w_trwr_s028*.py'))
        if _tw_matches:
            _tw_spec = _tw_ilu.spec_from_file_location('_tw', _tw_matches[-1])
            if _tw_spec is not None and _tw_spec.loader is not None:
                _tw_mod = _tw_ilu.module_from_spec(_tw_spec)
                _tw_spec.loader.exec_module(_tw_mod)
                _tw_mod.write_training_pair(
                    root,
                    prompt=msg[:500],
                    response='(pending — response not yet captured)',
                    verdict='pending',
                )
    except Exception:
        pass

    # ── Staleness alert — detect stale managed blocks ──
    try:
        import importlib.util as _sa_ilu
        _sa_matches = sorted(root.glob('src/警p_sa_s030*.py'))
        if _sa_matches:
            _sa_spec = _sa_ilu.spec_from_file_location('_staleness', _sa_matches[-1])
            if _sa_spec is not None and _sa_spec.loader is not None:
                _sa_mod = _sa_ilu.module_from_spec(_sa_spec)
                _sa_spec.loader.exec_module(_sa_mod)
                _sa_mod.inject_staleness_alert(root)
    except Exception:
        pass

    return entry
