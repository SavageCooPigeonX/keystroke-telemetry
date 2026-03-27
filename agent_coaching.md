# Agent Execution Observation Report

## Graph: 175 nodes, 337 edges

- Bottleneck: **streaming_layer** (in_degree=16)
- Bottleneck: **prediction_scorer** (in_degree=14)
- Bottleneck: **cognitive_reactor** (in_degree=12)

## Deaths: 10 total, 80% critical
- **graph_heat_map**: 2 deaths
- **plan_parser**: 1 deaths
- **dynamic_prompt**: 1 deaths
- Causes: {'exception': 3, 'loop': 3, 'timeout': 2, 'stale_import': 2}

---
Generate 3-5 specific actions to reduce deaths.