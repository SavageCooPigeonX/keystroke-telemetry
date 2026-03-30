"""predictor_seq009_seed_synthesizer_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any

def synthesize_phantom_seed(trend: dict[str, Any]) -> str:
    """Create a task seed from cognitive profile instead of a real task."""
    parts: list[str] = []
    state = trend.get("dominant_state", "unknown")
    modules = trend.get("modules", [])
    state_map = {
        "frustrated": "Operator frustrated, likely needs debugging help",
        "focused": "Operator in flow, likely building new feature",
        "hesitant": "Operator uncertain, likely needs guidance",
    }
    parts.append(state_map.get(state, "Predict operator's next need"))
    if modules:
        parts.append(f"Module focus: {', '.join(modules[:3])}")
    if trend.get("avg_del", 0) > 0.3:
        parts.append("High deletion ratio suggests rework/frustration")
    return ". ".join(parts)
