"""prediction_scorer_seq014/ — Pigeon-compliant module."""
import importlib, re
from pathlib import Path as _P

def _r(prefix, *attrs):
    d = _P(__file__).parent
    pat = re.compile(rf"^{re.escape(prefix)}_v\d+", re.I)
    for f in d.iterdir():
        if f.suffix == ".py" and f.stem != "__init__" and pat.match(f.stem):
            m = importlib.import_module(f".{f.stem}", __package__)
            return tuple(getattr(m, a) for a in attrs) if len(attrs) > 1 else getattr(m, attrs[0])
    raise ImportError(f"No module matching {prefix}")

CALIBRATION_FILE, EVAL_WINDOW, MAX_SCORED, SCORED_CACHE_FILE = _r(
    "prediction_scorer_seq014_constants_seq001",
    "CALIBRATION_FILE", "EVAL_WINDOW", "MAX_SCORED", "SCORED_CACHE_FILE",
)
extract_module_name = _r("prediction_scorer_seq014_module_extractor_seq005", "extract_module_name")
backfill_prediction_scores = _r("prediction_scorer_seq014_node_backfill_seq010", "backfill_prediction_scores")
score_predictions_post_commit = _r("prediction_scorer_seq014_post_commit_scorer_seq012", "score_predictions_post_commit")
score_predictions_post_edit = _r("prediction_scorer_seq014_post_edit_scorer_seq011", "score_predictions_post_edit")
score_prediction = _r("prediction_scorer_seq014_scoring_core_seq008", "score_prediction")
