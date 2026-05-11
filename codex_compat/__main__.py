"""Command entrypoint for the compiled codex_compat package."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "interview-files":
        root = Path.cwd()
        if "--root" in argv:
            index = argv.index("--root")
            if index + 1 < len(argv):
                root = Path(argv[index + 1]).resolve()
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from src._resolve import src_import

        interview_files = src_import("file_interview_mode_seq001", "interview_files")

        question = ""
        files: list[str] = []
        limit = 8
        write = True
        index = 1
        while index < len(argv):
            arg = argv[index]
            if arg == "--question" and index + 1 < len(argv):
                question = argv[index + 1]
                index += 2
            elif arg == "--file" and index + 1 < len(argv):
                files.append(argv[index + 1])
                index += 2
            elif arg == "--limit" and index + 1 < len(argv):
                limit = int(argv[index + 1])
                index += 2
            elif arg == "--no-write":
                write = False
                index += 1
            elif arg == "--root":
                index += 2
            else:
                index += 1
        result = interview_files(root, question=question, files=files, limit=limit, write=write)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    print("usage: py -m codex_compat interview-files [--question TEXT] [--file PATH] [--limit N]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
