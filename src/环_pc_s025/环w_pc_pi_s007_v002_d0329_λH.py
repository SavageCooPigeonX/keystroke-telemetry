"""push_cycle_seq025_predictions_injector_decomposed_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

from datetime import datetime, timezone
from pathlib import Path

def _inject_predictions_into_prompt(root: Path, predictions: list[dict],
                                     coaching: dict) -> None:
    """Inject predictions + coaching into copilot-instructions.md.

    Writes a <!-- pigeon:predictions --> block so Copilot knows what
    the operator will likely want next and can prepare proactively.
    """
    if not predictions and not coaching:
        return

    lines = ["<!-- pigeon:predictions -->",
             "## Push Cycle Predictions",
             "",
             f"*Auto-generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC*",
             ""]

    if predictions:
        lines.append("**What you'll likely want next push:**")
        for i, p in enumerate(predictions, 1):
            seed = p.get("phantom_seed", p.get("prediction_id", "?"))
            conf = p.get("confidence", 0)
            mode = p.get("mode", "?")
            trend = p.get("trend", {})
            modules = trend.get("modules", [])
            lines.append(f"{i}. [{mode}] {seed[:120]} (conf={conf:.0%})")
            if modules:
                lines.append(f"   - hot modules: {', '.join(modules[:5])}")
        lines.append("")

    if coaching.get("operator_coaching"):
        lines.append("**Operator coaching:**")
        for tip in coaching["operator_coaching"]:
            lines.append(f"- {tip}")
        lines.append("")

    if coaching.get("agent_coaching"):
        lines.append("**Agent coaching (for Copilot):**")
        for tip in coaching["agent_coaching"]:
            lines.append(f"- {tip}")
        lines.append("")

    lines.append("<!-- /pigeon:predictions -->")
    block = "\n".join(lines)

    # Inject into copilot-instructions.md
    ci_path = root / ".github" / "copilot-instructions.md"
    if not ci_path.exists():
        return

    content = ci_path.read_text("utf-8")
    start_tag = "<!-- pigeon:predictions -->"
    end_tag = "<!-- /pigeon:predictions -->"

    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)

    if start_idx >= 0 and end_idx >= 0:
        content = content[:start_idx] + block + content[end_idx + len(end_tag):]
    else:
        # Insert before the operator-state block (or at end)
        op_marker = "<!-- pigeon:operator-state -->"
        op_idx = content.find(op_marker)
        if op_idx >= 0:
            content = content[:op_idx] + block + "\n\n" + content[op_idx:]
        else:
            content += "\n\n" + block

    ci_path.write_text(content, "utf-8")
