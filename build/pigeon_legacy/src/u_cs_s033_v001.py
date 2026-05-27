"""Per-module Copilot confidence scorer.

Composes rework rate, self-fix issues, cognitive heat, file size,
and recency into a single confidence state per module:
  ✓ confident — low rework, no issues, recent, small
  ~ uncertain — some rework or medium heat
  ! degraded  — known issues or high rework
  ? blind     — no data or never touched

Also computes a Copilot meta-state line for prompt injection.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──


from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

# ── Confidence states ──
CONFIDENT = '✓'   # low rework, no issues, recent, small
UNCERTAIN = '~'   # some rework or medium heat
DEGRADED  = '!'   # known issues or high rework
BLIND     = '?'   # no data

# ── Thresholds ──
OVERSIZE_TOKENS = 3000
HIGH_HES = 0.7
REWORK_MISS_THRESHOLD = 0.05  # >5% miss rate = degraded


def _load_json(path: Path) -> dict | list:
    if path.exists():
        try:
            return json.loads(path.read_text('utf-8'))
        except Exception:
            return {}
    return {}


def _parse_self_fix_issues(root: Path) -> dict[str, list[str]]:
    """Parse most recent self-fix report for per-module issues."""
    sf_dir = root / 'docs' / 'self_fix'
    if not sf_dir.exists():
        return {}
    reports = sorted(sf_dir.glob('*.md'))
    if not reports:
        return {}
    latest = reports[-1]
    text = latest.read_text('utf-8', errors='replace')
    issues: dict[str, list[str]] = {}
    current_severity = ''
    for line in text.split('\n'):
        if line.startswith('### ') and '[CRITICAL]' in line:
            current_severity = 'CRITICAL'
        elif line.startswith('### ') and '[WARNING]' in line:
            current_severity = 'WARNING'
        elif line.startswith('### ') and '[INFO]' in line:
            current_severity = 'INFO'
        elif line.startswith('- **File**:'):
            fpath = line.split(':', 1)[1].strip()
            # Extract module name from path
            fname = Path(fpath).stem
            # Find root module name (before _seq)
            parts = fname.split('_seq')
            mod_name = parts[0].lstrip('.')
            if mod_name not in issues:
                issues[mod_name] = []
            issues[mod_name].append(current_severity)
    return issues


def _compute_rework_rates(root: Path) -> dict[str, float]:
    """Compute per-module rework miss rate from rework_log.json."""
    rework = _load_json(root / 'rework_log.json')
    if not isinstance(rework, list):
        return {}
    module_stats: dict[str, dict] = {}
    for entry in rework:
        hint = entry.get('query_hint', '')
        if hint.startswith('bg:'):
            continue
        verdict = entry.get('verdict', 'ok')
        # Try to extract module from hint
        mod = hint.split(':')[0] if ':' in hint else hint
        mod = mod.strip()
        if not mod:
            continue
        if mod not in module_stats:
            module_stats[mod] = {'total': 0, 'miss': 0}
        module_stats[mod]['total'] += 1
        if verdict in ('miss', 'partial'):
            module_stats[mod]['miss'] += 1
    rates = {}
    for mod, stats in module_stats.items():
        if stats['total'] > 0:
            rates[mod] = stats['miss'] / stats['total']
    return rates


def _get_heat_scores(root: Path) -> dict[str, float]:
    """Get latest hesitation score per module from heat map."""
    hm = _load_json(root / 'file_heat_map.json')
    if not isinstance(hm, dict):
        return {}
    scores = {}
    for mod, data in hm.items():
        samples = data.get('samples', [])
        if samples:
            scores[mod] = samples[-1].get('hes', 0.5)
    return scores


def score_module_confidence(
    root: Path,
    registry_modules: dict[str, dict] | None = None,
) -> dict[str, str]:
    """Score every known module with a confidence state.

    Returns {module_name: state_symbol}.
    """
    # Load all data sources
    sf_issues = _parse_self_fix_issues(root)
    rework_rates = _compute_rework_rates(root)
    heat = _get_heat_scores(root)

    # Load registry for token counts
    reg = _load_json(root / 'pigeon_registry.json')
    files = reg.get('files', []) if isinstance(reg, dict) else []
    module_tokens: dict[str, int] = {}
    all_modules: set[str] = set()
    for f in files:
        name = f.get('name', '')
        tok = f.get('tokens', 0)
        all_modules.add(name)
        if name not in module_tokens or tok > module_tokens[name]:
            module_tokens[name] = tok

    # Also include modules from registry_modules if provided
    if registry_modules:
        all_modules.update(registry_modules.keys())

    # Score each module
    scores: dict[str, str] = {}
    for mod in sorted(all_modules):
        # Start optimistic
        state = CONFIDENT

        # Check self-fix issues
        issues = sf_issues.get(mod, [])
        critical_count = issues.count('CRITICAL')
        warning_count = issues.count('WARNING')
        if critical_count >= 2:
            state = DEGRADED
        elif critical_count >= 1 or warning_count >= 2:
            state = max(state, UNCERTAIN, key=lambda s: [CONFIDENT, UNCERTAIN, DEGRADED, BLIND].index(s))

        # Check rework rate
        rr = rework_rates.get(mod, 0.0)
        if rr > REWORK_MISS_THRESHOLD:
            state = DEGRADED

        # Check cognitive heat
        hes = heat.get(mod, 0.0)
        if hes >= HIGH_HES and state == CONFIDENT:
            state = UNCERTAIN

        # Check oversize
        tok = module_tokens.get(mod, 0)
        if tok > OVERSIZE_TOKENS:
            if state == CONFIDENT:
                state = UNCERTAIN

        # If we have zero data points, mark blind
        has_data = mod in sf_issues or mod in rework_rates or mod in heat or mod in module_tokens
        if not has_data:
            state = BLIND

        scores[mod] = state

    return scores


def compute_copilot_meta_state(scores: dict[str, str]) -> dict:
    """Compute Copilot's own meta-state from confidence distribution."""
    total = len(scores)
    if total == 0:
        return {'state': BLIND, 'confident_pct': 0, 'degraded_pct': 0, 'blind_pct': 100}
    counts = {CONFIDENT: 0, UNCERTAIN: 0, DEGRADED: 0, BLIND: 0}
    for s in scores.values():
        counts[s] = counts.get(s, 0) + 1
    confident_pct = round(100 * counts[CONFIDENT] / total, 1)
    degraded_pct = round(100 * counts[DEGRADED] / total, 1)
    blind_pct = round(100 * counts[BLIND] / total, 1)

    if confident_pct >= 70:
        meta = CONFIDENT
    elif degraded_pct >= 20:
        meta = DEGRADED
    elif blind_pct >= 40:
        meta = BLIND
    else:
        meta = UNCERTAIN

    return {
        'state': meta,
        'confident_pct': confident_pct,
        'uncertain_pct': round(100 * counts[UNCERTAIN] / total, 1),
        'degraded_pct': degraded_pct,
        'blind_pct': blind_pct,
        'total_modules': total,
    }


def format_confidence_line(meta: dict) -> str:
    """Format a single-line Copilot meta-state for prompt injection."""
    s = meta['state']
    return (
        f"Copilot confidence: {s} "
        f"({meta['confident_pct']}% ✓ | {meta['uncertain_pct']}% ~ "
        f"| {meta['degraded_pct']}% ! | {meta['blind_pct']}% ?) "
        f"across {meta['total_modules']} modules"
    )
