"""backward_seq007_deepseek_analyze_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v002 | 65 lines | ~616 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import json
import re

def _deepseek_analyze_backward(
    task_seed: str, path: list[str], accumulated: list[dict],
    journal_entry: dict[str, Any], loss: float,
) -> dict[str, Any]:
    """Use DeepSeek to generate rich backward-pass analysis.

    Returns {node_analyses: [{node, summary, directive, failure_reason}...],
             system_insight: str, cost: float}
    Falls back to empty analysis if DeepSeek unavailable.
    """
    try:
        import importlib, re
        _ds_dir = __import__('pathlib').Path(__file__).resolve().parents[2] / 'pigeon_compiler' / 'integrations'
        _ds_pat = re.compile(r'^deepseek_adapter_seq001_v\d+', re.I)
        _ds_mod = next((f.stem for f in _ds_dir.iterdir() if f.suffix == '.py' and _ds_pat.match(f.stem)), None)
        if _ds_mod is None: raise ImportError('no deepseek adapter')
        deepseek_query = getattr(importlib.import_module(f'pigeon_compiler.integrations.{_ds_mod}'), 'deepseek_query')
    except (ImportError, ValueError, StopIteration):
        return {"node_analyses": [], "system_insight": "", "cost": 0.0}

    node_block = "\n".join(
        f"  - {n.get('node','?')}: dual={n.get('dual_score',0):.2f}, "
        f"fears={n.get('fears',[])[:2]}, relevance={n.get('relevance',0):.2f}"
        for n in accumulated[:15]
    )
    state = journal_entry.get("cognitive_state", "unknown")
    rework = journal_entry.get("rework_score", 0.0)
    prompt = f"""Backward pass analysis for a code-graph flow engine.

Task: "{task_seed}"
Path traversed: {' → '.join(path[:15])}
Loss: {loss:.3f} (0=perfect, 1=total failure)
Operator state after: {state}
Rework score: {rework:.2f}

Nodes that contributed:
{node_block}

For each node, write a 1-line contribution summary and 1-line behavioral directive.
If loss > 0.5, identify which node(s) failed and why.
End with a 1-line system-level insight.

Respond as JSON: {{"node_analyses": [{{"node": "...", "summary": "...", "directive": "...", "failure_reason": "..."}}], "system_insight": "..."}}"""

    try:
        result = deepseek_query(
            prompt=prompt,
            system="You are a neural graph backward-pass analyzer. Be precise and terse.",
            temperature=0.1,
            max_tokens=800,
        )
        text = result.get("content", "")
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            analysis = json.loads(match.group())
            analysis["cost"] = result.get("cost", 0.0)
            return analysis
    except Exception as e:
        logger.warning(f"[backward] DeepSeek analysis failed: {e}")

    return {"node_analyses": [], "system_insight": "", "cost": 0.0}
