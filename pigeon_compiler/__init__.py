"""pigeon_compiler — Self-Documenting Codebase Engine.

Filenames mutate on every commit to carry intent, description,
version, and token metadata.  The filename IS the changelog.

  noise_filter_seq007_v004_d0316__filter_live_noise_lc_fixed_timeout.py
  ├─ filter_live_noise     = what the file DOES  (from docstring)
  └─ fixed_timeout         = what was LAST DONE  (from commit message)

Components:
  - git_plugin       — Post-commit hook: auto-rename + prompt box + session log
  - session_logger   — Per-file JSONL mutation audit trail
  - pre_commit_audit — Advisory compliance checking (never blocks)
  - rename_engine    — Registry, import rewriter, manifest builder
  - cli              — `pigeon init/status/heal/sessions/uninstall`
  - state_extractor  — AST analysis, produces Ether Map JSON
  - cut_executor     — Deterministic file splitting + import fixing
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from types import ModuleType
from typing import Any

__version__ = "1.0.0"
__author__ = "SavageCooPigeonX"

_SEQ_TOKEN_RE = re.compile(r'(?:^|_)(?:seq|s)(?P<seq>\d{3})(?:$|_)', re.IGNORECASE)
_MODULE_CACHE: dict[str, ModuleType] = {}


def _normalize_seq_token(seq_token: str) -> str:
    token = seq_token.strip().lower()
    if token.startswith('seq'):
        token = token[3:]
    elif token.startswith('s'):
        token = token[1:]
    if len(token) != 3 or not token.isdigit():
        raise ValueError(f'Invalid seq token: {seq_token!r}')
    return token


def _iter_package_candidates(package_dir: Path) -> list[str]:
    names: list[str] = []
    for child in package_dir.iterdir():
        if child.name == '__pycache__':
            continue
        if child.is_file() and child.suffix == '.py' and child.stem != '__init__':
            names.append(child.stem)
            continue
        if child.is_dir() and (child / '__init__.py').exists():
            names.append(child.name)
    return names


def _matches_seq_token(name: str, seq_token: str) -> bool:
    match = _SEQ_TOKEN_RE.search(name)
    return bool(match and match.group('seq') == seq_token)


def _load_module(module_name: str) -> ModuleType:
    module = _MODULE_CACHE.get(module_name)
    if module is None:
        module = importlib.import_module(module_name)
        _MODULE_CACHE[module_name] = module
    return module


def _resolve_package_module_name(
    package_name: str,
    package_dir: Path,
    seq_token: str,
    attrs: tuple[str, ...] = (),
) -> str:
    seq = _normalize_seq_token(seq_token)
    candidates = sorted(
        name
        for name in _iter_package_candidates(package_dir)
        if _matches_seq_token(name, seq)
    )
    if not candidates:
        raise ImportError(
            f'No module matching seq token {seq_token!r} found in {package_dir}'
        )

    last_error: Exception | None = None
    if attrs:
        for name in reversed(candidates):
            module_name = f'{package_name}.{name}'
            try:
                module = _load_module(module_name)
            except Exception as exc:
                last_error = exc
                continue
            if all(hasattr(module, attr) for attr in attrs):
                return module_name

    for name in reversed(candidates):
        module_name = f'{package_name}.{name}'
        try:
            _load_module(module_name)
            return module_name
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise ImportError(
            f'No importable module matching seq token {seq_token!r} found in {package_dir}'
        ) from last_error
    raise ImportError(
        f'No usable module matching seq token {seq_token!r} found in {package_dir}'
    )


def _load_package_attrs(
    package_name: str,
    package_dir: Path,
    seq_token: str,
    *attrs: str,
) -> Any:
    module_name = _resolve_package_module_name(package_name, package_dir, seq_token, attrs)
    module = _load_module(module_name)
    if not attrs:
        return module
    if len(attrs) == 1:
        return getattr(module, attrs[0])
    return tuple(getattr(module, attr) for attr in attrs)

build_ether_map = _load_package_attrs(
    'pigeon_compiler.state_extractor',
    Path(__file__).resolve().parent / 'state_extractor',
    's006',
    'build_ether_map',
)

__all__ = ["build_ether_map"]
