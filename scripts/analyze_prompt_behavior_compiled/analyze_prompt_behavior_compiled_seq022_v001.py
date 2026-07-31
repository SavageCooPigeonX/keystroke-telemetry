"""analyze_prompt_behavior_compiled_seq022_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq018_v001 import _deepseek_prompt
from .analyze_prompt_behavior_compiled_seq019_v001 import _write_json
from .analyze_prompt_behavior_compiled_seq019_v001 import analyze
from .analyze_prompt_behavior_compiled_seq020_v001 import _write_md
from .analyze_prompt_behavior_compiled_seq021_v001 import _queue_deepseek
from .analyze_prompt_behavior_compiled_seq021_v001 import _write_internal_events
from pathlib import Path
import argparse
import json
import re

def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze prompt-journal behavior and cognitive shift patterns.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--since", default=None, help="ISO timestamp/date lower bound, e.g. 2026-04-25")
    parser.add_argument("--window", type=int, default=25, help="Prompt window for shift detection.")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-md", type=Path, default=None)
    parser.add_argument("--queue-deepseek", action="store_true", help="Append a DeepSeek research job using the generated artifact.")
    args = parser.parse_args()

    root = args.root.resolve()
    report = analyze(root, args.since, args.window)
    report["deepseek_prompt"] = _deepseek_prompt(report)

    out_json = args.out_json or root / "logs" / "prompt_behavior_analysis_latest.json"
    out_md = args.out_md or root / "logs" / "prompt_behavior_analysis.md"
    event_log = root / "logs" / "operator_behavior_events.jsonl"
    internal_events = report.pop("_internal_events", [])
    _write_json(out_json, report)
    _write_md(out_md, report)
    _write_internal_events(event_log, internal_events)
    queued = _queue_deepseek(root, report) if args.queue_deepseek else None

    print(json.dumps({
        "schema": report["schema"],
        "prompt_count": report["prompt_count"],
        "json": str(out_json),
        "markdown": str(out_md),
        "operator_behavior_events": str(event_log),
        "operator_behavior_event_count": len(internal_events),
        "deepseek_job": queued.get("job_id") if queued else None,
        "top_negative_themes": [
            [theme, stats["negative"]]
            for theme, stats in sorted(report["theme_reinforcement"].items(), key=lambda kv: kv[1]["negative"], reverse=True)[:6]
        ],
        "shift_count": len(report["shift_points"]),
    }, indent=2))
    return 0
