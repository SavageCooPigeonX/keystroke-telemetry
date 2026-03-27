"""Allow `py -m pigeon_brain <command>`."""
from glob import glob as _glob
from pathlib import Path
import importlib, os

_hits = _glob(str(Path(__file__).parent / "cli_seq009*"))
if not _hits:
    raise ImportError("cli_seq009* not found in pigeon_brain/")
_mod = importlib.import_module("pigeon_brain." + os.path.splitext(os.path.basename(_hits[0]))[0])
_mod.main()
