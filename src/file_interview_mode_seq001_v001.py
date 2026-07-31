"""Command-line facade for split file interviews."""

from .file_interview_mode_seq001_v001_compiled import (
    DEFAULT_QUESTIONS,
    interview_files,
    main,
)

__all__ = ["DEFAULT_QUESTIONS", "interview_files", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
