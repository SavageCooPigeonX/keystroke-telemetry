"""pigeon_compiler — Autonomous Code Decomposition Engine.

Transforms monolithic Python files into small, self-documenting,
manifest-tracked modules using AST analysis + AI planning.

Three layers:
  1. state_extractor  — Pure AST, zero API calls, produces Ether Map JSON
  2. weakness_planner — DeepSeek R1, plans the cuts from Ether Map
  3. cut_executor     — Deterministic file writing, import fixing, manifests
"""

__version__ = "0.2.1"
__author__ = "SavageCooPigeonX"

from pigeon_compiler.state_extractor import build_ether_map

__all__ = ["build_ether_map"]
