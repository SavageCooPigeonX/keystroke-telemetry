"""pulse_watcher.py — Save-time pulse correlator.

Called by the VS Code extension on every .py save under src/.
Reads the saved file's pending pulse block, correlates with the latest
prompt_journal entry, writes paired record to edit_pairs.jsonl,
and marks the pulse as harvested without erasing the metadata.

Argv:   <repo_root> <saved_file_relpath>
Stdout: JSON  {"paired": true/false, "latency_ms": int, "file": str}
"""
import json
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"paired": False, "error": "missing args"}))
        return

    root = Path(sys.argv[1]).resolve()
    rel = sys.argv[2]
    filepath = root / rel

    sys.path.insert(0, str(root))

    import importlib.util
    matches = sorted(root.glob('src/pulse_harvest_seq015*.py'))
    if not matches:
        print(json.dumps({"paired": False, "error": "no pulse_harvest module"}))
        return
    spec = importlib.util.spec_from_file_location('_ph', matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pair_pulse_to_prompt = mod.pair_pulse_to_prompt

    rec = pair_pulse_to_prompt(root, filepath)
    if rec:
        print(json.dumps({"paired": True, "latency_ms": rec["latency_ms"],
                          "file": rec["file"], "edit_why": rec["edit_why"]}))
    else:
        print(json.dumps({"paired": False}))


if __name__ == '__main__':
    main()
