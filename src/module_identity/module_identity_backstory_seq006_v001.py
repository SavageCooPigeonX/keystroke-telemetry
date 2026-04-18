"""module_identity_backstory_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 23 lines | ~224 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re


def extract_intent_chain(entry: dict) -> dict:
    """Extract intent mutation trail from registry history + path _lc_ slugs.

    Returns:
        intent_chain: ordered list of intent slugs (oldest → newest)
        churn_velocity: ver / days_alive (renames per day)
        intent_volatility: count of distinct intent slugs
    """
    history = entry.get('history', [])
    path = entry.get('path', '')

    # Collect intent slugs from history entries
    slugs: list[str] = []
    dates: list[str] = []
    for h in history:
        slug = h.get('intent', '') or ''
        if not slug:
            # Fall back to _lc_ from path fragment if present
            m = re.search(r'_lc_([a-z0-9_]+)', h.get('path', ''), re.IGNORECASE)
            if m:
                slug = m.group(1)
        if slug and (not slugs or slug != slugs[-1]):
            slugs.append(slug)
        if h.get('date'):
            dates.append(str(h['date']))

    # Also pull from top-level path if not already captured
    current_slug = ''
    m = re.search(r'_lc_([a-z0-9_]+)', path, re.IGNORECASE)
    if m:
        current_slug = m.group(1)
        if not slugs or current_slug != slugs[-1]:
            slugs.append(current_slug)

    # churn_velocity = versions / days alive
    ver = entry.get('ver', 1)
    days_alive = max(len(set(dates)), 1)
    churn_velocity = round(ver / days_alive, 3)

    # intent_volatility = distinct slugs (higher = more unstable purpose)
    intent_volatility = len(set(slugs))

    return {
        'intent_chain': slugs,
        'churn_velocity': churn_velocity,
        'intent_volatility': intent_volatility,
    }


def _extract_backstory(root: Path, name: str) -> list[str]:
    """Extract per-module narrative fragments from push_narratives."""
    narr_dir = root / 'docs' / 'push_narratives'
    if not narr_dir.exists():
        return []
    fragments = []
    pattern = re.compile(rf'\b{re.escape(name)}\b', re.IGNORECASE)
    for f in sorted(narr_dir.glob('*.md'), reverse=True)[:20]:
        try:
            text = f.read_text('utf-8', errors='replace')
        except Exception:
            continue
        for para in text.split('\n\n'):
            if pattern.search(para) and len(para) > 40:
                cleaned = para.strip()[:500]
                fragments.append(cleaned)
                if len(fragments) >= 5:
                    return fragments
    return fragments
