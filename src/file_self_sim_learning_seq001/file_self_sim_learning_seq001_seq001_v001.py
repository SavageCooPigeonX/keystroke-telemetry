"""file_self_sim_learning_seq001_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq002_v001 import _load_signal_sources
from .file_self_sim_learning_seq001_seq002_v001 import _merge_config
from .file_self_sim_learning_seq001_seq003_v001 import _drop_stale_runtime_sources
from .file_self_sim_learning_seq001_seq004_v001 import _intent_model
from .file_self_sim_learning_seq001_seq005_v001 import _select_candidates
from .file_self_sim_learning_seq001_seq010_v001 import _wake_node
from .file_self_sim_learning_seq001_seq011_v001 import _learning_packet
from .file_self_sim_learning_seq001_seq012_v001 import _diagnosis_flow
from .file_self_sim_learning_seq001_seq013_v001 import _interlink_plan
from .file_self_sim_learning_seq001_seq014_v001 import _backward_learning_plan
from .file_self_sim_learning_seq001_seq015_v001 import _architecture_sequence_registry
from .file_self_sim_learning_seq001_seq016_v001 import _weighted_relationship_graph
from .file_self_sim_learning_seq001_seq017_v001 import _overcap_split_jobs
from .file_self_sim_learning_seq001_seq019_v001 import _write_learning_outputs
from .file_self_sim_learning_seq001_seq041_v001 import SCHEMA
from .file_self_sim_learning_seq001_seq041_v001 import _now
from pathlib import Path
from typing import Any
import json
import re

def simulate_file_self_learning(
    root: Path,
    intent: str = "",
    limit: int | None = None,
    write: bool = True,
    source_result: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the learning-only self-sim pass.

    No source file is overwritten here. The output is a set of durable learning
    packets and profile updates that a later approved rewrite pass can consume.
    """
    root = Path(root)
    settings = _merge_config(config)
    limit = int(limit or settings.get("max_packets") or 8)
    sources = _load_signal_sources(root, source_result)
    if intent and source_result is None:
        _drop_stale_runtime_sources(intent, sources)
    architecture_registry = _architecture_sequence_registry(root, settings)
    sources["architecture_registry"] = architecture_registry
    intent_model = _intent_model(root, intent, sources)
    candidates = _select_candidates(root, intent_model, sources, limit, settings)
    wake_order = [
        _wake_node(root, row, index, intent_model, sources, settings)
        for index, row in enumerate(candidates)
    ]
    diagnosis_flow = _diagnosis_flow(wake_order)
    packets = [
        _learning_packet(root, node, intent_model, sources, settings)
        for node in wake_order
    ]
    relationship_graph = _weighted_relationship_graph(root, sources, wake_order, packets)
    split_jobs = _overcap_split_jobs(root, wake_order, packets, architecture_registry, relationship_graph, settings)
    interlink_plan = _interlink_plan(root, wake_order, packets, intent_model, settings, split_jobs)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "root": str(root),
        "mode": settings["mode"],
        "write_policy": "no_source_overwrite_learning_packets_only",
        "target_state": settings["target_state"],
        "intent": intent_model,
        "candidate_sources": sources["source_counts"],
        "wake_order": wake_order,
        "diagnosis_flow": diagnosis_flow,
        "learning_packets": packets,
        "relationship_graph": relationship_graph,
        "architecture_sequence_registry": architecture_registry,
        "overcap_split_jobs": split_jobs,
        "interlink_plan": interlink_plan,
        "backward_learning_pass": _backward_learning_plan(packets),
        "paths": {
            "latest": "logs/file_self_sim_learning_latest.json",
            "history": "logs/file_self_sim_learning.jsonl",
            "markdown": "logs/file_self_sim_learning.md",
            "deepseek_learning_packets": "logs/deepseek_learning_packets.jsonl",
            "relationship_graph": "logs/file_relationship_graph.json",
            "architecture_sequence_registry": "logs/file_identity_registry.json",
            "overcap_split_jobs": "logs/overcap_split_jobs.json",
            "profiles": "file_profiles.json",
            "outcomes": "logs/file_self_sim_learning_outcomes.jsonl",
        },
    }
    if write:
        _write_learning_outputs(root, result, settings)
    return result
