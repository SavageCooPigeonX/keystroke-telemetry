"""CLI wrapper for file interview mode."""
from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from src._resolve import src_import

    interview_main = src_import("file_interview_mode_seq001", "main")

    return interview_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
