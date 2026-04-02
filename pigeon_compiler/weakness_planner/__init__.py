"""weakness_planner/ — Layer 2: DeepSeek-powered strategic cut planning.

Takes ether maps from Layer 1, sends to DeepSeek for boundary decisions.
"""
from pathlib import Path

from pigeon_compiler import _load_package_attrs

build_plan_prompt, request_cut_plan = _load_package_attrs(
    __name__,
    Path(__file__).resolve().parent,
    's004',
    'build_plan_prompt',
    'request_cut_plan',
)

__all__ = ['build_plan_prompt', 'request_cut_plan']
