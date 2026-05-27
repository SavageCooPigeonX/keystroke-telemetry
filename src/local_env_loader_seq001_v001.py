"""Load trusted local env files without printing secrets."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

DEFAULT_KEYS = {
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_CODING_MODEL",
    "DEEPSEEK_FAST_MODEL",
    "DEEPSEEK_AUTONOMOUS_PROMPT_WRITES",
    "RESEND_API_KEY",
    "RESEND_FROM",
    "FILE_EMAIL_DELIVERY",
    "RESEND_USER_AGENT",
}


def load_local_env(
    root: Path,
    keys: Iterable[str] | None = None,
    *,
    override: bool = False,
) -> dict[str, str]:
    """Load allowed env vars from this repo and trusted sibling repos.

    Returns key -> source path, never key -> secret value.
    """
    allowed = set(keys or DEFAULT_KEYS)
    loaded: dict[str, str] = {}
    for path in env_search_paths(root):
        if not path.exists() or path.name.startswith(".env.example"):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line in lines:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            key = key.strip().lstrip("\ufeff")
            if key not in allowed:
                continue
            if key in os.environ and not override:
                continue
            clean = value.strip().strip("'\"")
            if not clean:
                continue
            os.environ[key] = clean
            loaded[key] = str(path)
    return loaded


def env_search_paths(root: Path) -> list[Path]:
    root = Path(root).resolve()
    home = Path.home()
    candidates = [
        root / ".env",
        root / "logs" / "file_email.env",
        root.parent / ".env",
    ]
    if _allow_trusted_repo_fallback(root):
        candidates.extend([
            home / "LinkRouter.ai" / ".env",
            home / "keystroke-telemetry" / ".env",
            home / "keystroke_telemetry" / ".env",
            home / "Savagecoopigeonx" / ".env",
        ])
    out: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def _allow_trusted_repo_fallback(root: Path) -> bool:
    if os.environ.get("PIGEON_TRUSTED_ENV_FALLBACK"):
        return True
    return (root / ".git").exists() or (root / ".env.example").exists()


def has_env_key(root: Path, key: str) -> bool:
    if os.environ.get(key):
        return True
    load_local_env(root, keys={key})
    return bool(os.environ.get(key))


__all__ = ["DEFAULT_KEYS", "env_search_paths", "has_env_key", "load_local_env"]
