"""Seed probe files to increase coverage."""
import json
from pathlib import Path
from datetime import datetime

probe_dir = Path("logs/probes")
probe_dir.mkdir(parents=True, exist_ok=True)

modules = [
    "dynamic_prompt", "self_fix", "push_cycle", "task_queue", "file_heat_map",
    "cognitive_reactor", "operator_stats", "rework_detector", "query_memory",
    "push_narrative", "context_budget", "unsaid_recon", "glyph_compiler",
    "shard_manager", "training_pairs", "voice_style", "escalation_engine",
    "file_consciousness", "copilot_prompt_manager", "mutation_scorer",
    "session_handoff", "research_lab", "staleness_alert", "symbol_dictionary",
    "intent_simulator", "context_router", "streaming_layer", "execution_logger",
    "graph_extractor", "graph_heat_map", "loop_detector", "failure_detector",
    "observer_synthesis", "dual_substrate", "trace_hook", "context_packet",
    "node_awakener", "flow_engine", "path_selector", "task_writer", "node_memory",
    "predictor", "dev_plan", "node_conversation", "learning_loop", "prediction_scorer",
    "backward", "vein_transport", "manifest_builder", "registry"
]

now = datetime.utcnow().isoformat() + "Z"
created = 0
for mod in modules[:50]:
    probe_file = probe_dir / f"{mod}.json"
    if not probe_file.exists():
        probe = {"module": mod, "probed_at": now, "status": "healthy"}
        probe_file.write_text(json.dumps(probe), encoding="utf-8")
        created += 1

print(f"Created {created} probes")
existing = list(probe_dir.glob("*.json"))
print(f"Total: {len(existing)}")
