"""codex_compat_seq040_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _append_jsonl
from .codex_compat_seq001_v001 import _utc_now
from .codex_compat_seq002_v001 import _repo_root
from .codex_compat_seq031_v001 import refresh_state
from pathlib import Path
from typing import Any
import importlib.util
import sys


def _load_training_pair_capture(src_dir: Path):
    """Load the training-pair callable from either Pigeon layout."""
    candidates = sorted(src_dir.glob("*s027*"), key=lambda item: item.name)
    import_errors: list[str] = []

    # Current Pigeon decompositions expose their API from a same-named package.
    for index, candidate in enumerate(candidates):
        init_path = candidate / "__init__.py"
        if not init_path.is_file():
            continue
        module_name = f"_codex_training_pairs_{index}"
        spec = importlib.util.spec_from_file_location(
            module_name,
            init_path,
            submodule_search_locations=[str(candidate)],
        )
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except (ImportError, OSError, SyntaxError) as exc:
            sys.modules.pop(module_name, None)
            import_errors.append(f"{candidate.name}: {exc}")
            continue
        capture = getattr(module, "capture_training_pair", None)
        if callable(capture):
            return capture

    # Older layouts kept the implementation in one top-level module.
    for candidate in candidates:
        if not candidate.is_file() or candidate.suffix != ".py":
            continue
        text = candidate.read_text(encoding="utf-8", errors="ignore")
        if "def capture_training_pair" not in text:
            continue
        spec = importlib.util.spec_from_file_location("codex_training_pairs", candidate)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except (ImportError, OSError, SyntaxError) as exc:
            import_errors.append(f"{candidate.name}: {exc}")
            continue
        capture = getattr(module, "capture_training_pair", None)
        if callable(capture):
            return capture

    detail = f" ({'; '.join(import_errors)})" if import_errors else ""
    raise ImportError(f"No training pair API found under {src_dir}{detail}")

def capture_pair(root: Path) -> dict[str, Any] | None:
    root = Path(root)
    repo = _repo_root()
    src_dir = repo / "src"
    capture_training_pair = _load_training_pair_capture(src_dir)
    pair = capture_training_pair(root)
    refresh_state(root, "captured training pair")
    return pair


def record_entropy_shed(root: Path, module: str, confidence: float, note: str = "") -> dict[str, Any]:
    root = Path(root)
    entry = {
        "ts": _utc_now(),
        "module": module,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "note": note,
        "source": "codex_explicit",
    }
    _append_jsonl(root / "logs" / "entropy_sheds.jsonl", entry)
    refresh_state(root, f"recorded entropy shed for {module}")
    return entry
