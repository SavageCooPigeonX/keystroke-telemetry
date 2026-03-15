"""streaming_layer_orchestrator_seq017_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v002 | 17 lines | ~142 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────

def run_demo():
    """Run a standalone demo of the streaming server."""
    _run_demo_print_header()
    server = _run_demo_setup_server()
    _run_demo_simulate_activity(server)
    _run_demo_print_summary(server)
    _run_demo_print_footer()
