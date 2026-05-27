# Regression tests

These are the former root-level `test_*.py` files. They stay together here so
the repo root only carries the public smoke runner, `test_all.py`, while the
deeper pytest suite remains discoverable under `tests/`.

The odd names and facade loaders are intentional. Some tests exercise legacy
pigeon-compiled modules by name, and several generated/interlink tests share
basenames with these files. Pytest uses importlib mode from `pyproject.toml` so
those duplicate basenames do not fight each other during collection.

The default `py -m pytest` lane excludes `tests/generated`, `tests/interlink`,
and `tests/archive`; run those folders explicitly when their contracts are the
work in front of you.
