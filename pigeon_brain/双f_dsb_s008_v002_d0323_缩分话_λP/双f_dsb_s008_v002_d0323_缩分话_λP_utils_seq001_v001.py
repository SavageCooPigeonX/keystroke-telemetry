"""双f_dsb_s008_v002_d0323_缩分话_λP_utils_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 46 lines | ~332 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from .描p_ghm_s004_v002_d0323_缩环检意_λP import HEAT_STORE
from pathlib import Path
import json

def _load_human_heat_raw(root: Path) -> dict:
    """Load raw file_heat_map.json (not the summary)."""
    heat_path = root / "file_heat_map.json"
    if not heat_path.exists():
        return {}
    try:
        return json.loads(heat_path.read_text("utf-8"))
    except Exception:
        return {}


def _load_agent_heat_raw(root: Path) -> dict:
    """Load raw graph_heat_map.json keyed by node name."""
    heat_path = root / HEAT_STORE
    if not heat_path.exists():
        return {}
    try:
        return json.loads(heat_path.read_text("utf-8"))
    except Exception:
        return {}


def _load_file_profiles(root: Path) -> dict:
    """Load file_profiles.json for personality/fears/partners."""
    path = root / "file_profiles.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:
        return {}


def _load_registry_entries(root: Path) -> list[dict]:
    """Load pigeon_registry.json for intent chain extraction."""
    reg = root / 'pigeon_registry.json'
    if not reg.exists():
        return []
    try:
        return json.loads(reg.read_text('utf-8', errors='ignore')).get('files', [])
    except Exception:
        return []


def extract_intent_chain_for_node(name: str, registry_entries: list[dict]) -> dict:
    """Extract churn_velocity + intent_volatility from registry history.

    Returns {intent_chain, churn_velocity, intent_volatility}.
    Matches by name prefix so 'self_fix' matches 'self_fix_seq013_v006...'.
    """
    import re
    matches = [e for e in registry_entries
               if e.get('name', '') == name or e.get('name', '').startswith(name + '_')]
    if not matches:
        return {'intent_chain': [], 'churn_velocity': 0.0, 'intent_volatility': 0}
    entry = max(matches, key=lambda e: len(e.get('history', [])))
    history = entry.get('history', [])
    path = entry.get('path', '')
    slugs: list[str] = []
    dates: list[str] = []
    for h in history:
        slug = h.get('intent', '') or ''
        if not slug:
            m = re.search(r'_lc_([a-z0-9_]+)', h.get('path', ''), re.IGNORECASE)
            if m:
                slug = m.group(1)
        if slug and (not slugs or slug != slugs[-1]):
            slugs.append(slug)
        if h.get('date'):
            dates.append(str(h['date']))
    m = re.search(r'_lc_([a-z0-9_]+)', path, re.IGNORECASE)
    if m:
        current = m.group(1)
        if not slugs or current != slugs[-1]:
            slugs.append(current)
    ver = entry.get('ver', 1)
    days_alive = max(len(set(dates)), 1)
    return {
        'intent_chain': slugs,
        'churn_velocity': round(ver / days_alive, 3),
        'intent_volatility': len(set(slugs)),
    }


def _count_lines(root: Path, rel_path: str) -> int:
    """Count lines in a source file."""
    if not rel_path:
        return 0
    try:
        return len((root / rel_path).read_text("utf-8").splitlines())
    except Exception:
        return 0
