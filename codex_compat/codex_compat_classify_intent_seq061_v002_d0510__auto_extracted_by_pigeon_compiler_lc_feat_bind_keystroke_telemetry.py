"""codex_compat_classify_intent_seq061_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 061 | VER: v002 | 25 lines | ~303 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def _classify_intent(prompt: str) -> str:
    text = prompt.lower()
    if any(word in text for word in (
        "orchestrator", "10q", "consensus", "approval", "approve", "guard",
        "copilot", "deepseek", "file sim", "file_sim", "autonomous",
    )):
        return "orchestration"
    if any(word in text for word in ("email", "emails", "resend", "outbox", "alert", "alerts")):
        return "telemetry"
    if any(word in text for word in ("monitor", "watch", "observe", "observatory")):
        return "monitoring"
    if any(word in text for word in ("fix", "bug", "error", "broken", "wrong", "fail")):
        return "debugging"
    if any(word in text for word in ("add", "create", "build", "implement", "wire")):
        return "building"
    if any(word in text for word in ("refactor", "rename", "move", "split", "cleanup")):
        return "restructuring"
    if any(word in text for word in ("test", "verify", "check", "run")):
        return "testing"
    if any(word in text for word in ("why", "how", "what", "explain", "analyze", "inspect")):
        return "exploring"
    return "unknown"
