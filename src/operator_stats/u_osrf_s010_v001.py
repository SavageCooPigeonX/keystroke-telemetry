"""operator_stats_render_full_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from datetime import datetime, timezone, timedelta
import json
import time as _time

def _render_full_markdown(history, write_every):
    """Render the full markdown stats file from accumulated history."""
    h = history
    n = len(h)

    lines = [
        "# Operator Cognitive Profile",
        "",
        f"*Auto-updated every {write_every} messages · {n} messages ingested*",
        f"*Last update: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
    ]
    lines += _render_ranges_table(h)
    lines += _render_state_distribution(h)
    lines += _render_timeframes(h, n)
    lines += _render_observations(h)
    lines += _render_recent_messages(h)

    lines += [
        "",
        "<!--",
        "DATA",
        json.dumps({"history": h}, separators=(",", ":")),
        "DATA",
        "-->",
    ]

    return "\n".join(lines) + "\n"
