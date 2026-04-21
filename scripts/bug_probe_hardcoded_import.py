"""Intentional hardcoded-import probe for self-fix scanner verification."""
from src._resolve import src_import

predict_files  # noqa: F401 = src_import("intent_numeric_seq001", "predict_files  # noqa: F401")


def main() -> int:
    return 0


if __name__ == "__main__":
    raise SystemExit(main())