"""generate_intent_tests — scaffold failing tests for every pending task_queue item.

Per FIX_PLAN.md §5: intents that have no generated test evaporate into cold backlog.
Giving each pending task a failing test file makes the intent mechanically tracked.

Run: py scripts\generate_intent_tests.py

Uses ONLY deterministic templates. No LLM calls. User explicitly said: "the model
is what's risky." Intent compiler via LLM is deferred until these skeletons stabilize.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK_QUEUE = ROOT / "task_queue.json"
OUT_DIR = ROOT / "tests" / "generated"


TEMPLATE = '''"""Intent: {title}
   Task ID: {tid}
   Status at scaffold: {status}
   Notes: {notes}

This is a SKELETON test. It fails until the intent is implemented.
When it passes, the task auto-closes via task_queue.mark_done().
"""

SKIP_REASON = {skip_reason!r}
TASK_ID = {tid!r}


def test_intent_has_acceptance_criteria():
    """Replace this body with a concrete, measurable assertion of the intent.

    Current state: no acceptance criteria defined. Until a human or the intent
    compiler fills this in, the intent is tracked as failing.
    """
    import pytest
    if SKIP_REASON:
        pytest.skip(SKIP_REASON)
    assert False, "acceptance criteria not yet defined for {tid}"
'''


def _slug(tid: str) -> str:
    return tid.replace("-", "_")


def _safe(text: str, limit: int = 200) -> str:
    text = (text or "").strip()
    text = re.sub(r"[^\x20-\x7e]+", " ", text)  # ascii-only
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "..."
    return text


def main() -> int:
    if not TASK_QUEUE.exists():
        print(f"no task_queue at {TASK_QUEUE}")
        return 1
    data = json.loads(TASK_QUEUE.read_text(encoding="utf-8"))
    tasks = data if isinstance(data, list) else data.get("tasks", [])
    pending = [t for t in tasks if t.get("status") == "pending"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "__init__.py").write_text("", encoding="utf-8")

    created = skipped = 0
    for t in pending:
        tid = t.get("id", "unknown")
        out = OUT_DIR / f"test_intent_{_slug(tid)}.py"
        if out.exists():
            skipped += 1
            continue
        title = _safe(t.get("title") or t.get("intent") or t.get("text") or "(no title)")
        notes = _safe(t.get("notes") or "")
        skip_reason = ""
        # Research-style intents get skipped with a reason (can't be mechanically verified)
        lowered = (title + " " + notes).lower()
        if any(kw in lowered for kw in ["research", "godel", "christ", "write report", "strip all"]):
            skip_reason = "research intent — requires human evaluation, not mechanical test"
        body = TEMPLATE.format(
            title=title,
            tid=tid,
            status=t.get("status", "?"),
            notes=notes,
            skip_reason=skip_reason,
        )
        out.write_text(body, encoding="utf-8")
        created += 1

    print(f"generated {created} intent tests, skipped {skipped} existing, out of {len(pending)} pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
