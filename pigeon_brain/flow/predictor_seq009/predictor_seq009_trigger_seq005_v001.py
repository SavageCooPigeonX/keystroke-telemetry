"""predictor_seq009_trigger_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json

def should_predict(root: Path, prompt_count: int, interval: int = DEFAULT_PREDICTION_INTERVAL) -> bool:
    """Check if we should fire a prediction cycle."""
    if prompt_count > 0 and prompt_count % interval == 0:
        return True
    # Also check for module clustering
    journal = root / "logs" / "prompt_journal.jsonl"
    trend = extract_cognitive_trend(journal, n_recent=5)
    if len(trend.get("modules", [])) >= MODULE_CLUSTER_THRESHOLD:
        return True
    return False
