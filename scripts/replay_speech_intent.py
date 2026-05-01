"""Replay a transcript through the IRT field-profile simulator.

Usage:
  py scripts/replay_speech_intent.py --transcript path.txt --label elon_musk_podcast --chunk-seconds 30
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.irt_field_profile_seq001_v001 import (  # noqa: E402
    build_irt_profile,
    chunk_transcript,
    process_speech_chunk,
    render_field_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay transcript chunks into an IRT field profile.")
    parser.add_argument("--transcript", required=True, help="Path to a plain-text transcript.")
    parser.add_argument("--label", default="", help="Human label for the source, e.g. elon_musk_podcast.")
    parser.add_argument("--chunk-seconds", type=int, default=30, help="Simulated seconds per chunk.")
    parser.add_argument("--words-per-minute", type=int, default=150, help="Replay chunk sizing estimate.")
    parser.add_argument("--run-id", default="", help="Optional explicit run id.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root. Defaults to this checkout.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    transcript_path = Path(args.transcript).resolve()
    text = transcript_path.read_text(encoding="utf-8", errors="ignore")
    label = args.label or transcript_path.stem
    run_id = args.run_id or _run_id(label, text, args.chunk_seconds)
    run_dir = root / "logs" / "irt_field" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    chunks = chunk_transcript(
        text,
        chunk_seconds=args.chunk_seconds,
        words_per_minute=args.words_per_minute,
    )
    profile = build_irt_profile(root, run_id, {
        "label": label,
        "transcript": str(transcript_path),
        "chunk_seconds": args.chunk_seconds,
        "words_per_minute": args.words_per_minute,
        "chunk_count": len(chunks),
    })

    pulses = []
    for chunk in chunks:
        pulse = process_speech_chunk(root, profile, chunk)
        pulses.append(pulse)

    _write_json(run_dir / "chunks.json", chunks)
    _write_json(run_dir / "profile.json", _public_profile(profile))
    _write_json(run_dir / "latest_pulse.json", pulses[-1] if pulses else {})
    _write_jsonl(run_dir / "pulses.jsonl", pulses)
    (run_dir / "report.md").write_text(render_field_report(profile), encoding="utf-8")

    print(f"IRT field replay complete: {run_dir}")
    print(f"chunks={len(chunks)} graph_stability={profile['metrics']['graph_stability']} "
          f"unknown_rate={profile['metrics']['unknown_rate']} probe_rate={profile['metrics']['probe_rate']}")
    return 0


def _run_id(label: str, text: str, chunk_seconds: int) -> str:
    import hashlib

    digest = hashlib.sha256(f"{label}|{chunk_seconds}|{text[:2000]}".encode("utf-8")).hexdigest()[:10]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_label = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in label.lower())[:48]
    return f"{safe_label}_{stamp}_{digest}"


def _public_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in profile.items() if not key.startswith("_")}


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
