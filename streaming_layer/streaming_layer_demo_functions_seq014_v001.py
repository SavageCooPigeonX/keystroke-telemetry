"""streaming_layer_demo_functions_seq014_v001.py — Pigeon-extracted by compiler."""
import time

def _run_demo_simulate_activity(server):
    import time
    from streaming_server import _sim_type, _sim_backspace
    
    server.start_message()
    buf = _sim_type(server, "Hello world, this is a test of the streaming layer")
    server.submit_message(buf)
    time.sleep(0.3)
    
    server.start_message()
    buf = _sim_type(server, "Waht is the ")
    buf = _sim_backspace(server, buf, 12)
    buf = _sim_type(server, "What is the meaning of everything?", buf)
    server.submit_message(buf)
    time.sleep(0.3)
    
    server.start_message()
    buf = _sim_type(server, "Actually never mind this whole thing")
    server.discard_message(buf)
    time.sleep(0.5)
def _run_demo_print_footer():
    print("\n" + "=" * 60)
    print("  DEMO COMPLETE ✓")
    print("=" * 60)
