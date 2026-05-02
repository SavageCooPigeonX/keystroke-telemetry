"""Refresh changed MANIFEST.md files for the push contract."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

START = "<!-- manifest:push-intent-state -->"
END = "<!-- /manifest:push-intent-state -->"
FILE_SIM_START = "<!-- manifest:file-sim-state -->"
FILE_SIM_END = "<!-- /manifest:file-sim-state -->"


def _repo_root() -> Path:
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8")
    return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else Path.cwd()


def refresh_push_manifests(
    root: Path,
    *,
    folders: list[Path] | None = None,
    changed_files: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = Path(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    changed = changed_files or _git_changed_files(root)
    target_folders = folders or _folders_for_changed_files(root, changed)
    builder = _load_manifest_builder(root)
    rows = []
    for folder in target_folders:
        if not folder.exists() or not any(folder.glob("*.py")):
            continue
        content = builder.build_manifest(folder, root)
        if not content:
            continue
        rel_folder = _rel(root, folder)
        path = folder / "MANIFEST.md"
        old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        content = _append_state_block(root, _preserve_generated_stamp(content, old), rel_folder, changed, old)
        changed_manifest = old != content
        if changed_manifest and not dry_run:
            path.write_text(content, encoding="utf-8")
        rows.append({"path": _rel(root, path), "folder": rel_folder, "changed": changed_manifest})
    result = {
        "schema": "push_manifest_refresh/v1",
        "mode": "dry_run" if dry_run else "write",
        "ts": datetime.now(timezone.utc).isoformat(),
        "changed_files": changed[:80],
        "manifests": rows,
        "changed_count": sum(1 for row in rows if row["changed"]),
    }
    _write_json(root / "logs" / "push_manifest_refresh_latest.json", result)
    if not dry_run:
        _append_jsonl(root / "logs" / "push_manifest_refresh.jsonl", result)
    return result


def _load_manifest_builder(root: Path):
    path = root / "pigeon_compiler" / "rename_engine" / "谱建f_mb_s007_v003_d0314_观重箱重拆_λD.py"
    if not path.exists():
        return _FallbackBuilder()
    spec = importlib.util.spec_from_file_location("pigeon_manifest_builder_runtime", path)
    if not spec or not spec.loader:
        raise RuntimeError("manifest builder not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FallbackBuilder:
    def build_manifest(self, folder: Path, root: Path) -> str:
        rel = folder.relative_to(root).as_posix()
        lines = [f"# MANIFEST - {rel}", "", "## Files", "", "| File | Lines |", "|---|---:|"]
        for py in sorted(folder.glob("*.py")):
            lines.append(f"| {py.name} | {len(py.read_text(encoding='utf-8', errors='replace').splitlines())} |")
        return "\n".join(lines) + "\n"


def _git_changed_files(root: Path) -> list[str]:
    commands = [["git", "diff", "--name-only"], ["git", "diff", "--name-only", "--cached"], ["git", "diff", "--name-only", "@{u}..HEAD"]]
    out: list[str] = []
    for cmd in commands:
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            out.extend(line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip())
    return list(dict.fromkeys(out))


def _folders_for_changed_files(root: Path, changed: list[str]) -> list[Path]:
    folders: list[Path] = []
    for rel in changed:
        if not rel.endswith(".py"):
            continue
        path = root / rel
        if path.parent == root:
            continue
        if path.exists() and path.is_file() and "site-packages" not in path.as_posix():
            folders.append(path.parent)
    return list(dict.fromkeys(folders))


def _append_state_block(root: Path, content: str, folder: str, changed: list[str], old: str = "") -> str:
    content = re.sub(rf"\n?{re.escape(START)}.*?{re.escape(END)}\n?", "\n", content, flags=re.S).rstrip()
    block = "\n\n".join([START, _render_intent_keys(root, folder), _render_file_comments(root, folder, changed), _render_changelog(root, folder, changed), _render_numeric_boundary(), END])
    file_sim = _extract_block(old, FILE_SIM_START, FILE_SIM_END)
    if file_sim:
        block = block + "\n\n" + file_sim
    return content + "\n\n" + block + "\n"


def _extract_block(text: str, start: str, end: str) -> str:
    match = re.search(rf"{re.escape(start)}.*?{re.escape(end)}", text, flags=re.S)
    return match.group(0).strip() if match else ""


def _preserve_generated_stamp(content: str, old: str) -> str:
    pattern = r"\*Auto-generated by pigeon_compiler manifest_builder \| [^*]+\*"
    current = re.search(pattern, content)
    previous = re.search(pattern, old)
    if current and previous:
        return content[:current.start()] + previous.group(0) + content[current.end():]
    return content


def _render_intent_keys(root: Path, folder: str) -> str:
    rows = []
    statuses = _intent_statuses(root)
    for row in _load_jsonl(root / "logs" / "intent_keys.jsonl", 800):
        key = str(row.get("intent_key") or "")
        scope = str(row.get("scope") or "")
        manifest = str(row.get("manifest_path") or "")
        if manifest == f"{folder}/MANIFEST.md" or scope == folder or scope.startswith(folder + "/"):
            rows.append((row, statuses.get(key, "pending")))
    lines = ["## Push Intent Keys", "", "| Status | Intent key | Prompt |", "|---|---|---|"]
    for row, status in rows[-10:]:
        lines.append(f"| {status} | `{row.get('intent_key')}` | {_cell(row.get('prompt'))} |")
    if len(lines) == 4:
        lines.append("| pending | `none-linked-yet` | no recent intent key matched this manifest |")
    return "\n".join(lines)


def _render_file_comments(root: Path, folder: str, changed: list[str]) -> str:
    comments = []
    latest = _load_json(root / "logs" / "file_self_knowledge_latest.json") or {}
    for packet in latest.get("packets", []) if isinstance(latest, dict) else []:
        _collect_comment(comments, folder, packet, "file", "file_quote", "model_guide")
    sim = _load_json(root / "logs" / "batch_rewrite_sim_latest.json") or {}
    for proposal in sim.get("proposals", []) if isinstance(sim, dict) else []:
        _collect_comment(comments, folder, proposal, "path", "file_comment", "proposed_fix")
    comment_by_file = {}
    for file_path, comment in comments:
        comment_by_file.setdefault(file_path, comment)
    changed_set = {rel.replace("\\", "/").strip("/") for rel in changed}
    ordered = sorted(
        comment_by_file.items(),
        key=lambda item: (0 if item[0].replace("\\", "/").strip("/") in changed_set else 1, item[0]),
    )
    lines = ["## File Comments", "", "| File | Comment |", "|---|---|"]
    for file_path, comment in ordered[:10]:
        lines.append(f"| `{file_path}` | {_cell(comment)} |")
    if len(lines) == 4:
        lines.append("| `none` | no recent file-sim or self-knowledge comment matched this manifest |")
    return "\n".join(lines)


def _collect_comment(out: list[tuple[str, Any]], folder: str, row: dict[str, Any], path_key: str, *comment_keys: str) -> None:
    file_path = str(row.get(path_key) or row.get("file") or "")
    if _belongs(file_path, folder):
        comment = next((row.get(key) for key in comment_keys if row.get(key)), "")
        out.append((file_path, comment))


def _render_changelog(root: Path, folder: str, changed: list[str]) -> str:
    touched = [rel for rel in changed if _belongs(rel, folder)]
    lines = ["## Manifest Changelog", "", "- refreshed: `pre-push-stable`", "- commit: `pending-push`"]
    lines.append(f"- changed files in scope: `{len(touched)}`")
    for rel in touched[:8]:
        lines.append(f"  - `{rel}`")
    return "\n".join(lines)


def _render_numeric_boundary() -> str:
    return "\n".join(["## Numeric Encoding Boundary", "", "- numeric encoding stays in `logs/numeric_surface_seq001_v001.json` and prompt/history logs for forward-pass file matching", "- manifest stores structured `scope:verb:target:scale` intent keys and file comments for Copilot clearance"])


def _intent_statuses(root: Path) -> dict[str, str]:
    registry = _load_json(root / "logs" / "intent_loop_registry.json") or {}
    statuses: dict[str, str] = {}
    for bucket in ("open", "closed"):
        for row in registry.get(bucket, []) if isinstance(registry, dict) else []:
            key = str(row.get("intent_key") or "")
            if key:
                statuses[key] = str(row.get("status") or bucket)
    return statuses


def _belongs(file_path: str, folder: str) -> bool:
    clean = file_path.replace("\\", "/").strip("/")
    folder = folder.strip("/")
    return bool(clean) and (folder in {"", "."} or clean == folder or clean.startswith(folder + "/"))


def _load_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _cell(value: Any, limit: int = 160) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")[:limit]


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fail-on-write", action="store_true")
    args = parser.parse_args()
    root = _repo_root()
    folders = sorted({path.parent for path in root.rglob("*.py") if ".git" not in path.parts and "__pycache__" not in path.parts}) if args.all else None
    result = refresh_push_manifests(root, folders=folders, dry_run=args.dry_run)
    print(f"Push manifests: {result['changed_count']} changed / {len(result['manifests'])} checked")
    return 3 if args.fail_on_write and result["changed_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
