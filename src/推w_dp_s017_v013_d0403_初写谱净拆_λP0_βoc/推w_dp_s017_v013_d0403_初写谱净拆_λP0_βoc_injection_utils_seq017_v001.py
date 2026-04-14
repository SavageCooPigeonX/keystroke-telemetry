"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_injection_utils_seq017_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v001 | 21 lines | ~172 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

def _strip_task_context_blocks(text: str) -> str:
    pat = re.compile(
        r'(?ms)^\s*<!-- pigeon:task-context -->\s*$\n.*?^\s*<!-- /pigeon:task-context -->\s*$\n?',
    )
    return pat.sub('', text).rstrip() + '\n'


def _find_task_context_anchor(text: str) -> int:
    for marker in (
        '<!-- pigeon:task-queue -->',
        '<!-- pigeon:operator-state -->',
        '<!-- pigeon:prompt-telemetry -->',
        '<!-- pigeon:auto-index -->',
    ):
        idx = text.find(marker)
        if idx >= 0:
            return idx
    return -1
