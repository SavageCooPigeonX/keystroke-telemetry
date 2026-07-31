"""Compatibility facade for the split root sim-key index."""

from .root_sim_key_file_seq001_v001_compiled import (
    DEFAULT_ATTENTION_LIMIT,
    ROOT_KEY,
    build_root_sim_key_file,
    render_root_sim_key_file,
)

__all__ = [
    "DEFAULT_ATTENTION_LIMIT",
    "ROOT_KEY",
    "build_root_sim_key_file",
    "render_root_sim_key_file",
]
