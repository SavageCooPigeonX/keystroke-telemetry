"""classify_bridge.py — VS Code extension ↔ Python classifier bridge.

Reads keystroke events from stdin, computes message metrics, classifies
cognitive state using the existing operator_stats classifiers, updates
operator_profile.md, and refreshes copilot-instructions.md in-place.

No git commit required — the operator-state block updates immediately.

Stdin:  {"events": [...], "submitted": bool}
Argv:   <repo_root>
Stdout: {"state": str, "hesitation": float, "wpm": float}
"""
import sys
import json
import importlib.util
from pathlib import Path
from datetime import datetime, timezone


def _load_pigeon_module(root: Path, pattern: str):
    """Dynamic import for pigeon files (filename mutates on every commit)."""
    matches = sorted(root.glob(pattern))
    if not matches:
        return None
    spec = importlib.util.spec_from_file_location('_pigeonmod', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _compute_metrics(events: list, submitted: bool) -> dict:
    inserts = [e for e in events if e.get('type') == 'insert']
    deletes = [e for e in events if e.get('type') == 'backspace']
    pauses  = [e for e in events if e.get('type') == 'pause']
    total   = max(len(events), 1)

    pause_ms_list = [e.get('duration_ms', 0) for e in pauses]
    total_pause_ms = sum(pause_ms_list)

    timestamps = [e['ts'] for e in events if 'ts' in e]
    start_ms = min(timestamps) if timestamps else 0.0
    end_ms   = max(timestamps) if timestamps else 1.0
    duration_ms = max(end_ms - start_ms, 1.0)

    del_ratio   = len(deletes) / total
    pause_ratio = total_pause_ms / duration_ms
    hes = min(1.0, round(del_ratio * 0.6 + pause_ratio * 0.4, 3))
    wpm = round((len(inserts) / 5) / max(duration_ms / 60_000, 0.001), 1)

    return {
        'total_keystrokes': len(events),
        'total_inserts':    len(inserts),
        'total_deletions':  len(deletes),
        'typing_pauses':    [{'duration_ms': d} for d in pause_ms_list],
        'start_time_ms':    int(start_ms),
        'end_time_ms':      int(end_ms),
        'hesitation_score': hes,
        'deleted':          not submitted,
        'ts':               datetime.now(timezone.utc).isoformat(),
    }, wpm


def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.').resolve()
    payload   = json.loads(sys.stdin.read())
    events    = payload.get('events', [])
    submitted = payload.get('submitted', True)

    metrics, wpm = _compute_metrics(events, submitted)

    # Load operator_stats — pigeon name mutates, use glob
    stats_mod = _load_pigeon_module(root, 'src/operator_stats_seq008*.py')
    state = 'neutral'
    if stats_mod:
        state = stats_mod.classify_state(metrics)
        metrics['state'] = state
        try:
            stats_mod.OperatorStats(
                str(root / 'operator_profile.md'), write_every=8
            ).ingest(metrics)
        except Exception:
            pass

    # Refresh copilot-instructions.md operator-state block immediately
    # (no git commit required — writes direct to disk)
    try:
        sys.path.insert(0, str(root))
        from pigeon_compiler.git_plugin import _refresh_operator_state
        _refresh_operator_state(root)
    except Exception:
        pass

    print(json.dumps({
        'state':     state,
        'hesitation': metrics['hesitation_score'],
        'wpm':        wpm,
    }))


if __name__ == '__main__':
    main()
