"""分f_dvp_s010_v002_d0328_唤脉运观_λR_orchestrator_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 131 lines | ~1,185 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path

def generate_dev_plan(root: Path) -> str:
    """
    Generate a self-development plan from accumulated learning data.

    Returns Markdown string and writes to pigeon_brain/dev_plan.md.
    """
    policies = get_all_policies(root)
    memory = load_memory(root)
    fix_mem = load_fix_memory(root)
    predictions = load_predictions(root)
    journal = root / "logs" / "prompt_journal.jsonl"
    trend = extract_cognitive_trend(journal)

    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"# Self-Development Plan")
    lines.append(f"*Auto-generated {now} from {len(policies)} node policies*")
    lines.append("")

    # Section 1: Node Performance Rankings
    lines.append("## Node Performance")
    lines.append("")
    if policies:
        ranked = sorted(
            policies.items(),
            key=lambda kv: kv[1].get("rolling_score", 0),
            reverse=True,
        )
        lines.append("| Node | Score | Confidence | Samples | Directive |")
        lines.append("|---|---:|---:|---:|---|")
        for node, pol in ranked:
            lines.append(
                f"| {node} | {pol.get('rolling_score', 0):.3f}"
                f" | {pol.get('confidence', 0):.2f}"
                f" | {pol.get('sample_count', 0)}"
                f" | {pol.get('behavioral_directive', '-')[:60]} |"
            )
        lines.append("")
    else:
        lines.append("*No node policies yet — run backward passes to accumulate.*")
        lines.append("")

    # Section 2: Nodes Needing Training
    lines.append("## Nodes Needing More Data")
    lines.append("")
    undertrained = [
        (n, p) for n, p in policies.items()
        if p.get("confidence", 0) < 0.5
    ]
    if undertrained:
        for node, pol in sorted(undertrained, key=lambda x: x[1].get("confidence", 0)):
            lines.append(
                f"- **{node}**: {pol.get('sample_count', 0)} samples"
                f" (confidence {pol.get('confidence', 0):.2f})"
            )
        lines.append("")
    else:
        lines.append("*All active nodes have sufficient training data.*")
        lines.append("")

    # Section 3: Struggling Nodes
    lines.append("## Struggling Nodes")
    lines.append("")
    struggling = [
        (n, p) for n, p in policies.items()
        if p.get("rolling_score", 0.5) < 0.3 and p.get("sample_count", 0) >= 3
    ]
    if struggling:
        for node, pol in sorted(struggling, key=lambda x: x[1].get("rolling_score", 1)):
            lines.append(
                f"- **{node}** score={pol.get('rolling_score', 0):.3f}:"
                f" {pol.get('behavioral_directive', 'no directive')}"
            )
        lines.append("")
    else:
        lines.append("*No nodes are critically struggling.*")
        lines.append("")

    # Section 4: Fix Patterns
    lines.append("## Known Fix Patterns")
    lines.append("")
    patterns = fix_mem.get("patterns", {})
    if patterns:
        top = sorted(patterns.items(), key=lambda kv: kv[1].get("count", 0), reverse=True)[:10]
        for sig, data in top:
            rate = data.get("successes", 0) / max(data.get("count", 1), 1)
            lines.append(
                f"- `{sig}` — {data.get('count', 0)}x seen,"
                f" {rate:.0%} success rate"
            )
        lines.append("")
    else:
        lines.append("*No fix patterns recorded yet.*")
        lines.append("")

    # Section 5: Cognitive Trend
    lines.append("## Operator Cognitive Trend")
    lines.append("")
    lines.append(f"- **Dominant state:** {trend.get('dominant_state', 'unknown')}")
    lines.append(f"- **Avg WPM:** {trend.get('avg_wpm', 0)}")
    lines.append(f"- **Avg deletion ratio:** {trend.get('avg_del', 0):.3f}")
    modules = trend.get("modules", [])
    if modules:
        lines.append(f"- **Module clusters:** {', '.join(modules)}")
    lines.append("")

    # Section 6: Recent Predictions
    lines.append("## Recent Predictions")
    lines.append("")
    if predictions:
        recent = predictions[-5:]
        for pred in recent:
            conf = pred.get("confidence", 0)
            seed = pred.get("phantom_seed", "?")[:80]
            lines.append(f"- [{pred.get('mode', '?')}] conf={conf:.2f}: {seed}")
        lines.append("")
    else:
        lines.append("*No predictions cached yet.*")
        lines.append("")

    # Write to file
    content = "\n".join(lines)
    p = _plan_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

    return content
