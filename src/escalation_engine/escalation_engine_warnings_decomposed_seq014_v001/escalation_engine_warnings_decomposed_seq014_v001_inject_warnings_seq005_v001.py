"""escalation_engine_warnings_decomposed_seq014_v001_inject_warnings_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 70 lines | ~703 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path

def inject_warnings(root: Path, state: dict):
    """Inject escalation warnings into copilot-instructions.md."""
    warnings = []
    for mod_name, mod_state in state.get('modules', {}).items():
        level = mod_state.get('level', 0)
        if level >= 3:
            countdown = mod_state.get('countdown', WARN_COUNTDOWN)
            bug_type = mod_state.get('bug_type', 'unknown')
            conf = mod_state.get('confidence', 0)
            passes = mod_state.get('passes_ignored', 0)
            if level == 3:
                warnings.append(
                    f"- **⚠️ AUTONOMOUS FIX PENDING** — `{mod_name}` "
                    f"({bug_type}, conf={conf:.2f}, ignored={passes} passes) "
                    f"will self-fix in {countdown} commit(s)"
                )
            elif level == 4:
                result = mod_state.get('fix_result', {})
                desc = result.get('description', 'unknown')
                warnings.append(
                    f"- **🔧 SELF-FIXED** — `{mod_name}` ({bug_type}): {desc}. "
                    f"Rollback available."
                )
            elif level == 5:
                result = mod_state.get('fix_result', {})
                if result.get('success'):
                    warnings.append(
                        f"- **✅ VERIFIED** — `{mod_name}` self-fix confirmed. "
                        f"Tests pass. You're welcome."
                    )
                else:
                    warnings.append(
                        f"- **❌ ROLLED BACK** — `{mod_name}` self-fix failed. "
                        f"Needs human help: {result.get('description', '?')}"
                    )

    if not warnings:
        return

    block = (
        f"{WARN_BLOCK_START}\n"
        f"## Autonomous Escalation Warnings\n\n"
        f"*{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
        f"{len(warnings)} module(s) escalated*\n\n"
        + '\n'.join(warnings) + '\n'
        + f"{WARN_BLOCK_END}"
    )

    ci = root / '.github' / 'copilot-instructions.md'
    if not ci.exists():
        return
    text = ci.read_text(encoding='utf-8')
    if WARN_BLOCK_START in text:
        import re
        text = re.sub(
            rf'{re.escape(WARN_BLOCK_START)}.*?{re.escape(WARN_BLOCK_END)}',
            block, text, flags=re.DOTALL,
        )
    else:
        # insert before organism health
        marker = '<!-- pigeon:organism-health -->'
        if marker in text:
            text = text.replace(marker, block + '\n' + marker)
        else:
            text += '\n' + block + '\n'
    ci.write_text(text, encoding='utf-8')
