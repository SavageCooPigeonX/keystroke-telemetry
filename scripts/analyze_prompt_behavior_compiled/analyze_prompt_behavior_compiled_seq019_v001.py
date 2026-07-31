"""analyze_prompt_behavior_compiled_seq019_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq001_v001 import _load_jsonl
from .analyze_prompt_behavior_compiled_seq002_v001 import _prepare
from .analyze_prompt_behavior_compiled_seq003_v001 import _bucket_by_day
from .analyze_prompt_behavior_compiled_seq004_v001 import _theme_reinforcement
from .analyze_prompt_behavior_compiled_seq005_v001 import _cooccurrence_graph
from .analyze_prompt_behavior_compiled_seq006_v001 import _shift_points
from .analyze_prompt_behavior_compiled_seq007_v001 import _emergent_threads
from .analyze_prompt_behavior_compiled_seq010_v001 import _behavioral_events
from .analyze_prompt_behavior_compiled_seq011_v001 import _internal_event_log
from .analyze_prompt_behavior_compiled_seq015_v001 import _correction_chains
from .analyze_prompt_behavior_compiled_seq016_v001 import _role_models
from .analyze_prompt_behavior_compiled_seq017_v001 import _internal_logs
from .analyze_prompt_behavior_compiled_seq023_v001 import SCHEMA
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def analyze(root: Path, since: str | None, window: int) -> dict[str, Any]:
    journal = root / "logs" / "prompt_journal.jsonl"
    rows = _prepare(_load_jsonl(journal), since)
    internal_events = _internal_event_log(rows)
    report = {
        "schema": SCHEMA,
        "generated_ts": datetime.now(timezone.utc).isoformat(),
        "source": str(journal),
        "since": since,
        "prompt_count": len(rows),
        "daily": _bucket_by_day(rows),
        "theme_reinforcement": _theme_reinforcement(rows),
        "cooccurrence_graph": _cooccurrence_graph(rows),
        "shift_points": _shift_points(rows, max(5, window)),
        "emergent_threads": _emergent_threads(rows),
        "behavioral_events": _behavioral_events(rows),
        "correction_chains": _correction_chains(rows),
        "role_models": _role_models(rows),
        "internal_event_log_path": str(root / "logs" / "operator_behavior_events.jsonl"),
        "internal_event_count": len(internal_events),
        "internal_event_sample": internal_events[-20:],
    }
    report["_internal_events"] = internal_events
    report["internal_logs"] = _internal_logs(report)
    return report


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
