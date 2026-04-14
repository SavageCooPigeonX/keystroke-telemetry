"""u_pj_s019_v003_d0404_λNU_βoc_gemini_enricher_seq027_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 027 | VER: v001 | 52 lines | ~575 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import sys

def _log_enriched_entry_run_gemini_enricher(root: Path, msg: str, deleted_words: list, cog_state: str, signals: dict) -> None:
    try:
        import subprocess as _sp
        _matches = sorted(root.glob('src/u_pe_s024*.py'))
        if _matches:
            _enricher_path = str(_matches[-1])
            _cog_json = json.dumps({
                'state': cog_state,
                'wpm': signals.get('wpm', 0),
                'del_ratio': signals.get('deletion_ratio', 0),
                'hes': signals.get('hesitation_count', 0),
            })
            _del_json = json.dumps(deleted_words)
            _script = (
                f'import importlib.util, json, sys; '
                f'spec = importlib.util.spec_from_file_location("_e", r"{_enricher_path}"); '
                f'mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); '
                f'mod.inject_query_block(sys.argv[1], sys.argv[2], '
                f'deleted_words=json.loads(sys.argv[3]), '
                f'cognitive_state=json.loads(sys.argv[4]))'
            )
            _proc = _sp.run(
                [sys.executable, '-c', _script, str(root), msg, _del_json, _cog_json],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            if _proc.returncode != 0:
                _err = (_proc.stderr or _proc.stdout or '').strip()
                if not _err:
                    _err = f'enricher exited with code {_proc.returncode}'
                raise RuntimeError(_trim_text(_err, 400))
    except Exception as _enrich_err:
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
