# Agent Execution Observation Report

## Graph: 125 nodes, 72 edges

- Bottleneck: **compliance_seq008_audit_decomposed** (in_degree=13)
- Bottleneck: **source_slicer** (in_degree=5)
- Bottleneck: **deepseek_adapter** (in_degree=4)

## Deaths: 4 total, 75% critical
- **plan_parser**: 1 deaths
- **dynamic_prompt**: 1 deaths
- **copilot_prompt_manager_seq020_block_utils**: 1 deaths
- Causes: {'exception': 3, 'loop': 1}

---
Generate 3-5 specific actions to reduce deaths.