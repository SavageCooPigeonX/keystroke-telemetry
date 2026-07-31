"""Command-line facade for the split prompt behavior analyzer."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.analyze_prompt_behavior_compiled import (
    NEGATIVE_PATTERNS,
    POSITIVE_PATTERNS,
    PromptRow,
    SCHEMA,
    STOPWORDS,
    analyze,
    main,
)

__all__ = [
    "NEGATIVE_PATTERNS",
    "POSITIVE_PATTERNS",
    "PromptRow",
    "SCHEMA",
    "STOPWORDS",
    "analyze",
    "main",
]

if __name__ == "__main__":
    raise SystemExit(main())
