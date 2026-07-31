"""Compatibility facade for the split batch rewrite simulator."""

from .batch_rewrite_sim_seq001 import (
    DEFAULT_CONFIG,
    RISKY_BITS,
    RISKY_SUFFIXES,
    SCHEMA,
    SOURCE_SUFFIXES,
    STOP,
    VERBS,
    compile_intent,
    load_file_sim_config,
    merge_file_sim_config,
    render_batch_rewrite_sim,
    should_fire_file_sim,
    simulate_batch_rewrites,
)

__all__ = [
    "DEFAULT_CONFIG",
    "RISKY_BITS",
    "RISKY_SUFFIXES",
    "SCHEMA",
    "SOURCE_SUFFIXES",
    "STOP",
    "VERBS",
    "compile_intent",
    "load_file_sim_config",
    "merge_file_sim_config",
    "render_batch_rewrite_sim",
    "should_fire_file_sim",
    "simulate_batch_rewrites",
]
