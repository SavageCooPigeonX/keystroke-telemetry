"""module_identity_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 27 lines | ~307 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

ARCHETYPES = {
    'veteran': {'trait': 'battle-tested', 'emoji': '🛡️', 'label': 'Veteran'},
    'hothead': {'trait': 'volatile', 'emoji': '🔥', 'label': 'Hothead'},
    'ghost': {'trait': 'unused', 'emoji': '👻', 'label': 'Ghost'},
    'anchor': {'trait': 'foundation', 'emoji': '⚓', 'label': 'Anchor'},
    'orphan': {'trait': 'abandoned', 'emoji': '🪦', 'label': 'Orphan'},
    'healer': {'trait': 'self-healing', 'emoji': '💊', 'label': 'Healer'},
    'bloated': {'trait': 'oversized', 'emoji': '🫧', 'label': 'Bloated'},
    'rookie': {'trait': 'new', 'emoji': '🌱', 'label': 'Rookie'},
    'stable': {'trait': 'steady', 'emoji': '✅', 'label': 'Stable'},
}


EMOTIONS = {
    'serene': {'color': '#3fb950', 'icon': '😌', 'label': 'Calm'},
    'anxious': {'color': '#d29922', 'icon': '😰', 'label': 'Anxious'},
    'frustrated': {'color': '#f85149', 'icon': '😤', 'label': 'Frustrated'},
    'depressed': {'color': '#8b949e', 'icon': '😔', 'label': 'Depressed'},
    'manic': {'color': '#bc8cff', 'icon': '🤪', 'label': 'Manic'},
    'confident': {'color': '#58a6ff', 'icon': '😎', 'label': 'Confident'},
}


MEMORY_DIR = 'logs/module_memory'
