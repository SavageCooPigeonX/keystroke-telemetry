"""Stable command-line facade for the split :mod:`codex_compat` package."""

from codex_compat import *  # noqa: F403
from codex_compat import main


if __name__ == "__main__":
    raise SystemExit(main())
