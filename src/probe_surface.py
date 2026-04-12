"""probe_surface — structured uncertainty probes emitted by copilot during edits.

mirrors entropy:shed but bidirectional:
  emit: copilot writes <!-- probe:ask --> blocks when hitting a decision fork
  parse: downstream tooling extracts probes from ai_responses.jsonl
  resolve: probe_resolver auto-answers from telemetry or surfaces to operator
  inject: resolved probes fed back into copilot-instructions.md

probe lifecycle:
  1. copilot encounters ambiguity mid-edit
  2. emits <!-- probe:ask --> block with question + candidates + confidence threshold
  3. chat_response_reader captures response → logs/ai_responses.jsonl
  4. probe_surface.parse_probe_blocks() extracts pending probes
  5. probe_resolver resolves from: unsaid_recon, prompt_journal, composition signal
  6. resolved probes written to logs/probe_resolutions.jsonl
  7. next refresh_managed_prompt injects <!-- pigeon:probe-resolutions --> block
  8. copilot reads resolutions in context → edits with near-zero entropy

zero LLM calls in parse path. resolver may optionally call gemini for synthesis.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── PROBE FORMAT ─────────────────────────────────────────────────
# <!-- probe:ask
# module: flow_engine
# question: does get_surface_tensor return flat dict or nested?
# candidates: flat_dict | nested_object
# confidence: 0.45
# context: editing predictor.py line 88, contract unclear
# -->

PROBE_PATTERN = re.compile(
    r'<!-- probe:ask\s*\n(.*?)\n\s*-->', re.DOTALL
)

FIELD_PATTERN = re.compile(
    r'^(\w+)\s*:\s*(.+)$', re.MULTILINE
)

REQUIRED_FIELDS = {'module', 'question'}
OPTIONAL_FIELDS = {'candidates', 'confidence', 'context', 'priority'}


def _parse_single_probe(block: str) -> dict[str, Any] | None:
    """Parse one probe:ask block into a structured dict."""
    fields = {}
    for m in FIELD_PATTERN.finditer(block):
        key = m.group(1).strip().lower()
        val = m.group(2).strip()
        fields[key] = val

    if not REQUIRED_FIELDS.issubset(fields):
        return None

    probe = {
        'module': fields['module'],
        'question': fields['question'],
        'candidates': [c.strip() for c in fields.get('candidates', '').split('|')] if fields.get('candidates') else [],
        'confidence': float(fields['confidence']) if fields.get('confidence') else 0.0,
        'context': fields.get('context', ''),
        'priority': fields.get('priority', 'medium'),
    }
    return probe


def parse_probe_blocks(text: str) -> list[dict[str, Any]]:
    """Extract all probe:ask blocks from a copilot response."""
    probes = []
    for match in PROBE_PATTERN.finditer(text):
        probe = _parse_single_probe(match.group(1))
        if probe:
            probes.append(probe)
    return probes


def harvest_pending_probes(root: Path, limit: int = 20) -> list[dict[str, Any]]:
    """Scan ai_responses.jsonl for unresolved probes.

    Cross-references against probe_resolutions.jsonl to skip already-resolved.
    Returns newest-first up to limit.
    """
    root = Path(root)
    responses_path = root / 'logs' / 'ai_responses.jsonl'
    resolutions_path = root / 'logs' / 'probe_resolutions.jsonl'

    if not responses_path.exists():
        return []

    # load existing resolution fingerprints for dedup
    resolved_fps = set()
    if resolutions_path.exists():
        try:
            for line in resolutions_path.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    entry = json.loads(line)
                    resolved_fps.add(entry.get('probe_fp', ''))
        except Exception:
            pass

    pending = []
    try:
        lines = responses_path.read_text(encoding='utf-8').splitlines()
    except Exception:
        return []

    # scan newest first
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue

        response_text = entry.get('response', '')
        probes = parse_probe_blocks(response_text)

        for probe in probes:
            fp = _probe_fingerprint(probe)
            if fp in resolved_fps:
                continue
            probe['source_ts'] = entry.get('ts', '')
            probe['probe_fp'] = fp
            pending.append(probe)

            if len(pending) >= limit:
                return pending

    return pending


def _probe_fingerprint(probe: dict) -> str:
    """Stable fingerprint for dedup — module + question hash."""
    import hashlib
    raw = f"{probe['module']}:{probe['question']}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def write_resolution(root: Path, probe: dict, resolution: dict) -> None:
    """Append a resolved probe to probe_resolutions.jsonl."""
    root = Path(root)
    out_path = root / 'logs' / 'probe_resolutions.jsonl'
    out_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'probe_fp': probe.get('probe_fp', _probe_fingerprint(probe)),
        'module': probe['module'],
        'question': probe['question'],
        'candidates': probe.get('candidates', []),
        'resolution': resolution.get('answer', ''),
        'source': resolution.get('source', 'unknown'),
        'confidence': resolution.get('confidence', 0.0),
    }

    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def build_resolution_block(root: Path, max_items: int = 8) -> str:
    """Build the <!-- pigeon:probe-resolutions --> managed block content.

    Shows recent resolutions so copilot can read them on next prompt.
    """
    root = Path(root)
    resolutions_path = root / 'logs' / 'probe_resolutions.jsonl'

    if not resolutions_path.exists():
        return _empty_block()

    entries = []
    try:
        for line in resolutions_path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                entries.append(json.loads(line))
    except Exception:
        return _empty_block()

    if not entries:
        return _empty_block()

    # newest first, limited
    entries = entries[-max_items:]
    entries.reverse()

    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        f'## Probe Resolutions',
        f'',
        f'*{len(entries)} resolved · {ts}*',
        f'',
        f'**Read these before editing the referenced modules:**',
        f'',
    ]

    for e in entries:
        conf = e.get('confidence', 0)
        src = e.get('source', '?')
        lines.append(f"- **`{e['module']}`**: {e['question']}")
        lines.append(f"  - → {e['resolution']} (conf={conf:.2f}, via {src})")
        lines.append('')

    # also show pending count
    pending = harvest_pending_probes(root, limit=50)
    if pending:
        lines.append(f'**{len(pending)} probe(s) still pending resolution.**')
        for p in pending[:3]:
            lines.append(f"  - `{p['module']}`: {p['question']}")

    return '\n'.join(lines)


def _empty_block() -> str:
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    return (
        f'## Probe Resolutions\n\n'
        f'*No probes yet · {ts}*\n\n'
        f'Emit `<!-- probe:ask -->` blocks when uncertain during edits. '
        f'Probes auto-resolve from telemetry or surface to operator.'
    )
