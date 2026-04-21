"""operator_state_daemon.py — Independent operator state capture + COoikit file pairing.

Fully decoupled from Copilot/LLM. Runs via watchdog.py or extension spawn.

CAPTURE SOURCES (read-only, written by other daemons):
  - logs/os_keystrokes.jsonl     (os_hook.py — raw keystrokes)
  - logs/vscdb_drafts.jsonl      (vscdb_poller.py — draft composition snapshots)

OUTPUTS:
  - logs/operator_state_realtime.jsonl  — one entry per composition event
  - logs/operator_state_current.json    — rolling live state (always fresh)

File pairing via COoikit (intent_numeric.predict_files) — pure math, zero LLM.
This daemon runs 24/7. The LLM reads its output. It NEVER waits for LLM.

Future capture sources: webcam eye-tracking, active tab monitor, audio.
Each source plugs into _read_signals() — daemon handles fusion.

Usage: py client/operator_state_daemon.py <project_root>
"""
import importlib.util
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).parent.parent
DRAFT_LOG = ROOT / "logs" / "vscdb_drafts.jsonl"
KEYS_LOG = ROOT / "logs" / "os_keystrokes.jsonl"
OUT_LOG = ROOT / "logs" / "operator_state_realtime.jsonl"
CURRENT = ROOT / "logs" / "operator_state_current.json"
POLL_S = 1.0
TAIL_LINES = 2000
PROMPT_DENSITY_WINDOWS_MIN = (5, 15, 60)


# ── COoikit loader ──────────────────────────────────────────────────────────

def _load_predict_files():
    """Load predict_files from intent_numeric — pure numeric, no LLM."""
    try:
        candidates = sorted((ROOT / "src").glob("intent_numeric_seq001*.py"))
        if not candidates:
            return None
        spec = importlib.util.spec_from_file_location("intent_numeric", candidates[-1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, "predict_files", None)
    except Exception:
        return None


# ── Signal readers ──────────────────────────────────────────────────────────

def _tail(path: Path, n: int) -> list[str]:
    if not path.exists():
        return []
    try:
        return path.read_text("utf-8", "ignore").splitlines()[-n:]
    except OSError:
        return []


def _os_hook_signals(key_lines: list[str]) -> dict:
    """Extract os_hook health + recent chat keystroke count."""
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    last_ts = 0
    chat_count = 0
    for raw in key_lines[-300:]:
        try:
            e = json.loads(raw)
            ts = e.get("ts", 0)
            if ts > last_ts:
                last_ts = ts
            if e.get("context") == "chat":
                chat_count += 1
        except Exception:
            pass
    age_s = (now_ms - last_ts) / 1000 if last_ts else 99999
    return {
        "active": age_s < 120,
        "age_s": round(age_s, 1),
        "chat_events": chat_count,
    }


def _parse_iso_ts(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _prompt_density(history_lines: list[str], reference_ts: str | None = None) -> dict:
    ref = _parse_iso_ts(reference_ts) or datetime.now(timezone.utc)
    timestamps: list[datetime] = []
    for raw in history_lines:
        try:
            entry = json.loads(raw)
        except Exception:
            continue
        if entry.get("event") != "composition":
            continue
        ts = _parse_iso_ts(entry.get("ts") or entry.get("captured_at"))
        if ts is not None:
            timestamps.append(ts)

    extra_ts = _parse_iso_ts(reference_ts)
    if extra_ts is not None:
        timestamps.append(extra_ts)

    if not timestamps:
        return {}

    timestamps.sort()
    density = {}
    for minutes in PROMPT_DENSITY_WINDOWS_MIN:
        cutoff = ref - timedelta(minutes=minutes)
        count = sum(1 for ts in timestamps if cutoff <= ts <= ref)
        density[f"last_{minutes}m"] = {
            "count": count,
            "per_hour": round(count * 60 / minutes, 2),
        }

    gaps = [
        max((timestamps[idx] - timestamps[idx - 1]).total_seconds(), 0.0)
        for idx in range(1, len(timestamps))
    ]
    if gaps:
        recent_gaps = gaps[-5:]
        density["latest_gap_s"] = round(gaps[-1], 1)
        density["avg_gap_s"] = round(sum(recent_gaps) / len(recent_gaps), 1)

    return density


# ── Draft composition tracker ───────────────────────────────────────────────

class _DraftTracker:
    """Stateful: watches vscdb_drafts.jsonl for submit events."""

    def __init__(self, initial_lines: int = 0):
        # Start at current end of file — don't replay history on startup
        self._seen = initial_lines
        self._ins = 0
        self._dels = 0
        self._deleted_texts: list[str] = []
        self._start_ts: Optional[str] = None

    def poll(self, lines: list[str]) -> Optional[dict]:
        new_lines = lines[self._seen:]
        self._seen = len(lines)
        result = None
        for raw in new_lines:
            try:
                e = json.loads(raw)
            except Exception:
                continue
            if e.get("event") != "draft_changed":
                continue
            if not self._start_ts:
                self._start_ts = e.get("ts")
            self._ins += max(0, e.get("chars_added", 0))
            self._dels += max(0, e.get("chars_deleted", 0))
            dt = e.get("deleted_text", "")
            if dt and len(dt.strip()) > 2:
                self._deleted_texts.append(dt.strip())
            # submit = prev text non-empty AND new text empty
            prev = e.get("prev_text", "")
            nxt = e.get("new_text", "")
            if prev.strip() and not nxt.strip() and self._ins > 0:
                result = self._build(prev, e.get("ts", ""))
                self._reset()
        return result

    def _build(self, final_text: str, ts: str) -> dict:
        total = self._ins + self._dels
        del_ratio = round(self._dels / max(total, 1), 3)
        dur_s = _dur_s(self._start_ts, ts)
        net = max(0, self._ins - self._dels)
        wpm = round((net / 5) / max(dur_s / 60, 0.01), 1)
        return {
            "final_text": final_text[:500],
            "ts": ts,
            "session_start_ts": self._start_ts,
            "wpm": wpm,
            "deletion_ratio": del_ratio,
            "total_inserts": self._ins,
            "total_deletes": self._dels,
            "deleted_texts": list(dict.fromkeys(self._deleted_texts))[:15],
        }

    def _reset(self):
        self._ins = self._dels = 0
        self._deleted_texts = []
        self._start_ts = None


def _dur_s(ts0: Optional[str], ts1: Optional[str]) -> float:
    try:
        t0 = datetime.fromisoformat(str(ts0).replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(str(ts1).replace("Z", "+00:00"))
        return max(1.0, (t1 - t0).total_seconds())
    except Exception:
        return 1.0


# ── Output ──────────────────────────────────────────────────────────────────

def _write_event(entry: dict):
    entry["captured_at"] = datetime.now(timezone.utc).isoformat()
    with OUT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    CURRENT.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Main loop ────────────────────────────────────────────────────────────────

def main():
    predict_files = _load_predict_files()
    # Initialize tracker at current file end — skip historical events
    initial_draft_lines = len(_tail(DRAFT_LOG, TAIL_LINES))
    tracker = _DraftTracker(initial_lines=initial_draft_lines)
    heartbeat_n = 0

    while True:
        draft_lines = _tail(DRAFT_LOG, TAIL_LINES)
        key_lines = _tail(KEYS_LOG, 500)
        history_lines = _tail(OUT_LOG, TAIL_LINES)
        ks = _os_hook_signals(key_lines)
        composition = tracker.poll(draft_lines)

        if composition:
            # COoikit pairing — intent_numeric, pure math, no LLM
            query = composition["final_text"]
            if composition["deleted_texts"]:
                query += " " + " ".join(composition["deleted_texts"][:5])
            file_preds = []
            density = _prompt_density(history_lines, composition.get("ts"))
            if predict_files:
                try:
                    file_preds = [
                        {"file": f, "score": round(s, 4)}
                        for f, s in (predict_files(query, top_n=8) or [])
                    ]
                except Exception:
                    pass
            _write_event({
                "event": "composition",
                **composition,
                "file_predictions": file_preds,
                "prompt_density": density,
                "os_hook": ks,
            })
        elif heartbeat_n % 30 == 0:
            # Heartbeat every 30s — keeps current.json fresh for health checks
            density = _prompt_density(history_lines)
            CURRENT.write_text(json.dumps({
                "event": "heartbeat",
                "ts": datetime.now(timezone.utc).isoformat(),
                "prompt_density": density,
                "os_hook": ks,
                "draft_lines_seen": len(draft_lines),
            }, indent=2, ensure_ascii=False), encoding="utf-8")

        heartbeat_n += 1
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
