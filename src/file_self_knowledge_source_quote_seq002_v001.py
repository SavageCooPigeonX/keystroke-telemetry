"""Extract a compact source-owned quote for file knowledge packets."""
from pathlib import Path


def read_source_quote(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    for line in text.splitlines()[:80]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(('"""', "'''", "#", "//", "<!--")):
            return stripped[:220]
    return text.strip().splitlines()[0][:220] if text.strip() else ""
