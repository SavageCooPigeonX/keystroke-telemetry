"""Allow `py -m pigeon_brain <command>`."""

from __future__ import annotations

import importlib
import re
from pathlib import Path

_CLI_SEQ_RE = re.compile(r'(?:^|_)(?:seq|s)009(?:$|_)', re.IGNORECASE)


def _load_cli_module():
    package = __package__ or 'pigeon_brain'
    package_dir = Path(__file__).resolve().parent
    candidates = sorted(
        py.stem
        for py in package_dir.glob('令*.py')
        if py.stem != '__main__' and _CLI_SEQ_RE.search(py.stem)
    )
    if not candidates:
        raise ImportError('No pigeon_brain CLI module matching seq009 was found')
    return importlib.import_module(f'{package}.{candidates[-1]}')


_load_cli_module().main()
