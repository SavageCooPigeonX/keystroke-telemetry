"""观f_os_s007_v003_d0401_读谱建册_λA_write_coaching_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 9 lines | ~103 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def write_agent_coaching(root: Path, observation: dict) -> Path:
    """Write agent_coaching.md from observation — like operator_coaching.md."""
    prompt = build_observer_prompt(observation)
    out = root / COACHING_PATH
    out.write_text(prompt, encoding="utf-8")
    return out
