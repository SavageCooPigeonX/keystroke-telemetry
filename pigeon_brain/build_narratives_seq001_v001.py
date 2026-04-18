"""Parse push narratives into JSON for the UI to load."""
import re
import json
from pathlib import Path

NARRATIVES_DIR = Path(__file__).resolve().parent.parent / "docs" / "push_narratives"
OUTPUT = Path(__file__).resolve().parent / "ui" / "public" / "narratives.json"


def parse_narrative(path: Path) -> dict:
    """Extract per-module narrative paragraphs from a push narrative .md file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    # Extract date + commit from filename: 2026-03-23_465cbfa.md
    stem = path.stem  # e.g. "2026-03-23_465cbfa"
    parts = stem.split("_", 1)
    date = parts[0] if parts else ""
    commit = parts[1] if len(parts) > 1 else ""

    # Extract intent
    intent_m = re.search(r"\*\*Intent\*\*:\s*(.+)", text)
    intent = intent_m.group(1).strip() if intent_m else ""

    # Extract per-module paragraphs: **module_name** (seqNNN vNNN): ...
    # Also handles: I am **module_name**, ...
    modules = {}
    # Pattern 1: **name** (seqN vN): text...
    for m in re.finditer(
        r"\*\*(\w+)\*\*\s*\(seq\d+\s+v\d+\):\s*(.+?)(?=\n\*\*\w+\*\*|\nREGRESSION|\nThe operator|\Z)",
        text, re.DOTALL
    ):
        name = m.group(1).strip()
        body = m.group(2).strip()
        # Clean up body — collapse whitespace
        body = re.sub(r"\s+", " ", body)
        modules[name] = body

    # Pattern 2: I am **full_filename**, ... (single long paragraph)
    if not modules:
        for m in re.finditer(
            r"I am \*\*(\w+)\*\*[,.](.+?)(?=\nI am \*\*|\nREGRESSION|\nThe operator|\Z)",
            text, re.DOTALL
        ):
            raw_name = m.group(1).strip()
            # Extract base module name (before _seq)
            base = re.sub(r"_seq\d+.*", "", raw_name)
            body = m.group(2).strip()
            body = re.sub(r"\s+", " ", body)
            if base not in modules:
                modules[base] = body

    return {"date": date, "commit": commit, "intent": intent, "modules": modules}


def build_narratives_seq001_v001_json():
    """Build aggregated narratives.json — latest narrative per module wins."""
    if not NARRATIVES_DIR.exists():
        print(f"No narratives dir: {NARRATIVES_DIR}")
        return

    files = sorted(NARRATIVES_DIR.glob("*.md"))
    result = {}  # module_name -> { text, date, commit, intent }

    for f in files:
        parsed = parse_narrative(f)
        for mod, text in parsed["modules"].items():
            # Later files overwrite earlier — keeps latest narrative
            result[mod] = {
                "text": text,
                "date": parsed["date"],
                "commit": parsed["commit"],
                "intent": parsed["intent"],
            }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(result)} module narratives to {OUTPUT}")


if __name__ == "__main__":
    build_narratives_seq001_v001_json()
