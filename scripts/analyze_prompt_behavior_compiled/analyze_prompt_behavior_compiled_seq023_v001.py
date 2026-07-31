"""analyze_prompt_behavior_compiled_seq023_v001.py — Auto-extracted by Pigeon Compiler."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import re

SCHEMA = "prompt_behavior_analysis/v1"


POSITIVE_PATTERNS = [
    r"\byes\b",
    r"\byes!\b",
    r"\bperfect\b",
    r"\bexactly\b",
    r"\bcloser\b",
    r"\bthat's it\b",
    r"\bthats it\b",
    r"\bfire\b",
    r"\bkiller task\b",
    r"\blooks like.?its working\b",
    r"\bdo that\b",
    r"\bgo ahead\b",
    r"\bpush\b",
    r"\bworks\b",
    r"\bgood\b",
    r"\bnice\b",
    r"\bliked\b",
]


NEGATIVE_PATTERNS = [
    r"\bwrong\b",
    r"\bnope\b",
    r"\bno no\b",
    r"\bnot quite\b",
    r"\bnot what\b",
    r"\bdont like\b",
    r"\bdoesn.?t work\b",
    r"\bdidnt actually\b",
    r"\byou guessed\b",
    r"\bliterally guessed\b",
    r"\bresearch\b",
    r"\bnot being a thinking partner\b",
    r"\bcannot use you to brainstorm\b",
    r"\bweak\b",
    r"\bridiculous\b",
    r"\brobotic\b",
    r"\bterrible\b",
    r"\blame\b",
    r"\bstupid\b",
    r"\bhate\b",
    r"\bshit\b",
    r"\bwtf\b",
    r"\bmistaking my intent\b",
]


STOPWORDS = {
    "the",
    "and",
    "that",
    "this",
    "with",
    "what",
    "have",
    "want",
    "like",
    "from",
    "your",
    "youre",
    "about",
    "should",
    "there",
    "still",
    "into",
    "they",
    "them",
    "then",
    "also",
    "because",
    "make",
    "work",
    "works",
    "when",
    "where",
    "which",
    "would",
    "could",
    "need",
    "needs",
    "itself",
    "really",
    "actual",
    "actually",
}


@dataclass
class PromptRow:
    raw: dict[str, Any]
    ts: datetime
    session_n: int
    msg: str
    themes: list[str]
    reinforcement: str
    cognitive_load: float
    tokens: list[str]
