"""seal_master_test — compute SHA of src/master_test.py and write to .master_test_sha.

Run after intentionally editing master_test.py. Commit the updated .master_test_sha.
An LLM modifying master_test.py WITHOUT running this script will break integrity check.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "src" / "master_test.py"
SHA_FILE = ROOT / ".master_test_sha"


def main() -> int:
    if not TARGET.exists():
        print(f"missing: {TARGET}", file=sys.stderr)
        return 1
    sha = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    SHA_FILE.write_text(sha + "\n", encoding="utf-8")
    print(f"sealed: {sha}")
    print(f"  wrote: {SHA_FILE.relative_to(ROOT)}")
    print("  commit this file to git. LLM edits to master_test.py will now break integrity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
