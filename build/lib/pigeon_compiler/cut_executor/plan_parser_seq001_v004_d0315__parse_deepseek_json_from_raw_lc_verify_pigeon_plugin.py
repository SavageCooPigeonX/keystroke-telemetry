"""plan_parser_seq001_v001.py — Parse DeepSeek JSON from raw response.

Handles markdown code fences, trailing commas, and validation.
Returns a clean dict or raises ValueError.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v004 | 44 lines | ~371 tokens
# DESC:   parse_deepseek_json_from_raw
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import json, re


def parse_plan(raw_response: dict) -> dict:
    """Extract structured plan from DeepSeek response dict."""
    content = raw_response.get("response", {}).get("content", "")
    if not content:
        content = raw_response.get("content", "")
    return _extract_json(content)


def _extract_json(text: str) -> dict:
    """Pull JSON from text, stripping markdown fences."""
    # Strip ```json ... ``` wrappers
    m = re.search(r'```(?:json)?\s*\n(.*?)```', text, re.S)
    blob = m.group(1).strip() if m else text.strip()
    # Fix trailing commas before } or ]
    blob = re.sub(r',\s*([}\]])', r'\1', blob)
    plan = json.loads(blob)
    _validate(plan)
    return plan


def _validate(plan: dict):
    """Ensure plan has required keys."""
    for key in ("source_file", "cuts", "init_exports"):
        if key not in plan:
            raise ValueError(f"Plan missing required key: {key}")
    for i, cut in enumerate(plan["cuts"]):
        if "new_file" not in cut:
            raise ValueError(f"Cut #{i} missing 'new_file'")
