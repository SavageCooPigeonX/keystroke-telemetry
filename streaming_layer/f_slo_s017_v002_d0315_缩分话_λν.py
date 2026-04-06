"""streaming_layer_orchestrator_seq017_v001.py — Pigeon-extracted by compiler."""


def run_demo():
    """Run a standalone demo of the streaming server."""
    _run_demo_print_header()
    server = _run_demo_setup_server()
    _run_demo_simulate_activity(server)
    _run_demo_print_summary(server)
    _run_demo_print_footer()
