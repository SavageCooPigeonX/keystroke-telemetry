"""probe_resolver — auto-answer copilot uncertainty probes from live telemetry.

resolution sources (in priority order):
  1. prompt_journal — operator's recent messages carry explicit intent
  2. unsaid_recon — deleted thoughts often answer the exact question copilot has
  3. composition_signal — hesitation/rewrite patterns reveal decision direction
  4. file_consciousness — module profiles carry known fears + contracts
  5. push_narrative — recent commit messages describe actual changes made
  6. operator fallback — if nothing resolves, surface to streaming layer

zero LLM calls in fast path. optional gemini synthesis for ambiguous probes.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .probe_surface import write_resolution, _probe_fingerprint


# ── SIGNAL LOADERS ───────────────────────────────────────────────

def _load_recent_prompts(root: Path, limit: int = 20) -> list[dict]:
    """Load recent prompt journal entries."""
    journal = root / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return []
    entries = []
    try:
        for line in journal.read_text(encoding='utf-8').splitlines():
            if line.strip():
                entries.append(json.loads(line))
    except Exception:
        return []
    return entries[-limit:]


def _load_unsaid_threads(root: Path, limit: int = 10) -> list[dict]:
    """Load recent unsaid reconstructions."""
    unsaid = root / 'logs' / 'unsaid_reconstructions.jsonl'
    if not unsaid.exists():
        return []
    entries = []
    try:
        for line in unsaid.read_text(encoding='utf-8').splitlines():
            if line.strip():
                entries.append(json.loads(line))
    except Exception:
        return []
    return entries[-limit:]


def _load_file_profiles(root: Path) -> dict:
    """Load module profiles with contracts and fears."""
    fp = root / 'file_profiles.json'
    if not fp.exists():
        return {}
    try:
        return json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _load_push_narratives(root: Path, limit: int = 5) -> list[str]:
    """Load recent push narrative summaries."""
    narr_dir = root / 'build' / 'narrative'
    if not narr_dir.exists():
        return []
    files = sorted(narr_dir.glob('*.md'), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for f in files[:limit]:
        try:
            results.append(f.read_text(encoding='utf-8')[:500])
        except Exception:
            pass
    return results


# ── RESOLUTION STRATEGIES ────────────────────────────────────────

def _try_prompt_journal(probe: dict, prompts: list[dict]) -> dict | None:
    """Check if operator's recent messages directly answer the probe."""
    module = probe['module'].lower()
    question_words = set(w for w in probe['question'].lower().split() if len(w) > 3)

    for entry in reversed(prompts):
        msg = entry.get('msg', entry.get('preview', '')).lower()
        # direct module mention + relevant content (word boundary for short modules)
        module_in_msg = (
            (len(module) > 4 and module in msg)
            or bool(re.search(r'\b' + re.escape(module) + r'\b', msg))
        )
        if module_in_msg:
            # check for keyword overlap with question
            msg_words = set(msg.split())
            overlap = question_words & msg_words
            if len(overlap) >= 2:
                return {
                    'answer': f"Operator said: \"{entry.get('msg', entry.get('preview', ''))[:200]}\"",
                    'source': 'prompt_journal',
                    'confidence': min(0.7 + len(overlap) * 0.05, 0.95),
                }
    return None


def _parse_candidates(raw) -> list[str]:
    """Normalize candidates from string or list to clean list."""
    if isinstance(raw, list):
        return [c.strip().lower() for c in raw if len(c.strip()) > 3]
    if isinstance(raw, str):
        return [c.strip().lower() for c in raw.split('|') if len(c.strip()) > 3]
    return []


def _try_unsaid_recon(probe: dict, threads: list[dict]) -> dict | None:
    """Check if deleted thoughts answer the probe."""
    module = probe['module'].lower()
    candidates = _parse_candidates(probe.get('candidates', []))

    for thread in reversed(threads):
        intent = thread.get('reconstructed_intent', '').lower()
        deleted_phrases = thread.get('deleted_words', [])
        deleted = ' '.join(deleted_phrases).lower()

        # module must appear as a whole word, not a substring match on 2-char modules
        module_in_text = (
            (len(module) > 4 and (module in intent or module in deleted))
            or re.search(r'\b' + re.escape(module) + r'\b', intent + ' ' + deleted)
        )

        if module_in_text:
            return {
                'answer': f"Unsaid intent: \"{thread.get('reconstructed_intent', '')[:200]}\"",
                'source': 'unsaid_recon',
                'confidence': 0.65,
            }

        # if candidates appear in deleted words (whole-word match, min 4 chars)
        for candidate in candidates:
            if re.search(r'\b' + re.escape(candidate) + r'\b', intent + ' ' + deleted):
                return {
                    'answer': f"Operator deleted reference to '{candidate}' — likely intended: {thread.get('reconstructed_intent', '')[:150]}",
                    'source': 'unsaid_recon',
                    'confidence': 0.60,
                }
    return None


def _try_file_profile(probe: dict, profiles: dict) -> dict | None:
    """Check if module's known contracts/fears answer the probe."""
    module = probe['module'].lower()

    # search profiles for matching module (require significant overlap)
    for key, profile in profiles.items():
        key_lower = key.lower()
        # require at least 4-char module name for substring match, else exact
        match = (len(module) > 4 and (module in key_lower or key_lower in module)) or key_lower == module
        if not match:
            continue
            fears = profile.get('fears', [])
            contracts = profile.get('contracts', [])
            known = profile.get('known_issues', [])

            # check if question keywords appear in profile
            q_lower = probe['question'].lower()
            for contract in contracts:
                if any(w in contract.lower() for w in q_lower.split() if len(w) > 3):
                    return {
                        'answer': f"Contract from profile: {contract}",
                        'source': 'file_consciousness',
                        'confidence': 0.80,
                    }
            for fear in fears:
                if any(w in fear.lower() for w in q_lower.split() if len(w) > 3):
                    return {
                        'answer': f"Known fear: {fear}",
                        'source': 'file_consciousness',
                        'confidence': 0.70,
                    }
    return None


def _try_push_narrative(probe: dict, narratives: list[str]) -> dict | None:
    """Check if recent commits describe the answer."""
    module = probe['module'].lower()
    for narr in narratives:
        if module in narr.lower():
            # extract the relevant sentence
            sentences = re.split(r'[.!?\n]', narr)
            for s in sentences:
                if module in s.lower() and len(s.strip()) > 20:
                    return {
                        'answer': f"From push narrative: {s.strip()[:200]}",
                        'source': 'push_narrative',
                        'confidence': 0.55,
                    }
    return None


def _try_organism_directive(probe: dict, root: Path) -> dict | None:
    """Check if the organism health directive or self-fix reports provide signal."""
    module = probe['module'].lower()
    candidates = _parse_candidates(probe.get('candidates', []))

    # 1. check self-fix report for module-specific bugs
    selffix = root / 'logs' / 'self_fix_report.json'
    if selffix.exists():
        try:
            report = json.loads(selffix.read_text(encoding='utf-8'))
            issues = report.get('issues', report.get('problems', []))
            module_issues = [i for i in issues
                            if isinstance(i, dict) and module in str(i).lower()]
            if module_issues:
                bug_types = [i.get('type', i.get('bug', '')) for i in module_issues[:3]]
                # if bug is oversize/over_cap and "split" is a candidate, prefer split
                for bt in bug_types:
                    bt_lower = str(bt).lower()
                    if 'over' in bt_lower or 'cap' in bt_lower or 'size' in bt_lower:
                        if any('split' in c for c in candidates):
                            return {
                                'answer': f"Self-fix reports {module} is over-cap ({', '.join(str(b) for b in bug_types)}). Pigeon convention: split.",
                                'source': 'organism_directive',
                                'confidence': 0.75,
                            }
                    if 'dead' in bt_lower or 'orphan' in bt_lower:
                        if any('delete' in c or 'remove' in c for c in candidates):
                            return {
                                'answer': f"Self-fix reports {module} has dead/orphan issues ({', '.join(str(b) for b in bug_types)}). Consider removal.",
                                'source': 'organism_directive',
                                'confidence': 0.65,
                            }
        except Exception:
            pass

    # 2. check codebase pattern — decomposition is the norm (260+ modules)
    clot_keywords = ['clot', 'oversize', 'over_cap', 'bloat', 'dead_import']
    q_lower = probe['question'].lower()
    if any(kw in q_lower for kw in clot_keywords):
        if any('split' in c for c in candidates):
            return {
                'answer': "Codebase pattern: 260+ modules, all decomposed by pigeon compiler. Split is the convention.",
                'source': 'organism_directive',
                'confidence': 0.60,
            }

    return None


# ── MAIN RESOLVER ────────────────────────────────────────────────

def resolve_probe(root: Path, probe: dict) -> dict | None:
    """Try to auto-resolve a probe from telemetry signals.

    Returns resolution dict or None if needs operator input.
    Resolution sources tried in priority order.
    """
    prompts = _load_recent_prompts(root)
    threads = _load_unsaid_threads(root)
    profiles = _load_file_profiles(root)
    narratives = _load_push_narratives(root)

    strategies = [
        ('prompt_journal', lambda: _try_prompt_journal(probe, prompts)),
        ('unsaid_recon', lambda: _try_unsaid_recon(probe, threads)),
        ('file_consciousness', lambda: _try_file_profile(probe, profiles)),
        ('push_narrative', lambda: _try_push_narrative(probe, narratives)),
        ('organism_directive', lambda: _try_organism_directive(probe, root)),
    ]

    for name, strategy in strategies:
        try:
            result = strategy()
            if result:
                return result
        except Exception:
            continue

    return None


def resolve_all_pending(root: Path, auto_write: bool = True) -> dict:
    """Resolve all pending probes. Returns summary.

    auto_write=True writes resolutions to probe_resolutions.jsonl.
    Unresolvable probes are left pending for operator.
    """
    from .probe_surface import harvest_pending_probes

    root = Path(root)
    pending = harvest_pending_probes(root)

    resolved = []
    unresolved = []

    for probe in pending:
        resolution = resolve_probe(root, probe)
        if resolution:
            if auto_write:
                write_resolution(root, probe, resolution)
            resolved.append({
                'module': probe['module'],
                'question': probe['question'],
                'answer': resolution['answer'],
                'source': resolution['source'],
                'confidence': resolution['confidence'],
            })
        else:
            unresolved.append({
                'module': probe['module'],
                'question': probe['question'],
                'candidates': probe.get('candidates', []),
                'context': probe.get('context', ''),
            })

    return {
        'total_pending': len(pending),
        'resolved': len(resolved),
        'unresolved': len(unresolved),
        'resolutions': resolved,
        'needs_operator': unresolved,
    }
