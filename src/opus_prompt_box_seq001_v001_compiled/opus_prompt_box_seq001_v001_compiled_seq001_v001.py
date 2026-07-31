"""opus_prompt_box_seq001_v001_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq003_v001 import render_opus_prompt_box
from .opus_prompt_box_seq001_v001_compiled_seq004_v001 import _merge_problems
from .opus_prompt_box_seq001_v001_compiled_seq005_v001 import _apply_tax
from .opus_prompt_box_seq001_v001_compiled_seq006_v001 import _boost_for_prompt
from .opus_prompt_box_seq001_v001_compiled_seq006_v001 import _cap_open
from .opus_prompt_box_seq001_v001_compiled_seq007_v001 import _intent_routes
from .opus_prompt_box_seq001_v001_compiled_seq007_v001 import _routing_note
from .opus_prompt_box_seq001_v001_compiled_seq010_v001 import _absorb_legacy_tasks
from .opus_prompt_box_seq001_v001_compiled_seq010_v001 import _bug_candidates
from .opus_prompt_box_seq001_v001_compiled_seq011_v001 import _intent_graph
from .opus_prompt_box_seq001_v001_compiled_seq011_v001 import _write_task_queue
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _latest_prompt
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _load_candidates
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _truncate_candidates
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import CANDIDATES_LOG
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import DONE_STATUSES
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import HISTORY_JSONL
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import LATEST_JSON
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import LATEST_MD
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import MAX_OPEN_PROBLEMS
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import SCHEMA
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _append_jsonl
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _now
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import re

def refine_opus_prompt_box(
    root: Path,
    prompt: str = "",
    *,
    write: bool = True,
    max_open: int = MAX_OPEN_PROBLEMS,
) -> dict[str, Any]:
    """Merge candidates + intent routes, tax stale items, cap open problems."""
    root = Path(root)
    prompt = str(prompt or _latest_prompt(root)).strip()
    now = _now()
    intent_graph = _intent_graph(root, prompt)
    bugs = _bug_candidates(root)
    candidates = _load_candidates(root)
    absorbed = _absorb_legacy_tasks(root)
    merged = _merge_problems(prompt, intent_graph, bugs, candidates, absorbed, now)
    taxed = _apply_tax(merged, now)
    boosted = _boost_for_prompt(taxed, prompt, intent_graph)
    open_rows, dropped = _cap_open(boosted, max_open=max_open)
    done_rows = [row for row in boosted if row.get("status") in DONE_STATUSES]
    result = {
        "schema": SCHEMA,
        "ts": now,
        "writer": "claude-opus",
        "operator_prompt": prompt,
        "max_open": max_open,
        "open_count": len(open_rows),
        "dropped_count": len(dropped),
        "intent_routes": _intent_routes(intent_graph),
        "open_problems": open_rows,
        "tax_dropped": dropped,
        "done_problems": done_rows[:12],
        "routing_note": _routing_note(prompt, intent_graph, open_rows),
        "paths": {
            "latest_json": LATEST_JSON,
            "latest_md": LATEST_MD,
            "candidates": CANDIDATES_LOG,
            "task_queue": "task_queue.json",
        },
    }
    if write:
        _write_task_queue(root, open_rows + done_rows + dropped)
        _write_json(root / LATEST_JSON, result)
        _append_jsonl(root / HISTORY_JSONL, result)
        (root / LATEST_MD).write_text(render_opus_prompt_box(result), encoding="utf-8")
        _truncate_candidates(root)
    return result
