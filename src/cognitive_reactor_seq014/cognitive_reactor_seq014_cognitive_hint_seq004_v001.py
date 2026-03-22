"""cognitive_reactor_seq014_cognitive_hint_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _inject_cognitive_hint(
    root: Path, module_key: str, avg_hes: float,
    dominant_state: str, patch: str | None
):
    """For severe streaks, inject a one-liner into copilot-instructions."""
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists():
        return
    try:
        text = cp.read_text('utf-8')
        marker = '<!-- /pigeon:operator-state -->'
        if marker not in text:
            return
        hint = (
            f'\n> **Cognitive reactor fired on `{module_key}`** '
            f'(hes={avg_hes}, state={dominant_state}). '
            f'Simplify interactions with this module.\n'
        )
        if hint in text:
            return  # already injected
        text = text.replace(marker, marker + hint)
        cp.write_text(text, encoding='utf-8')
    except Exception:
        pass
