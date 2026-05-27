"""Queue a DeepSeek push audit from manifest/file-sim state."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8")
    return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else Path.cwd()


def build_deepseek_push_audit(root: Path, *, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    changed = _git_changed_files(root)
    owner_root = Path(__file__).resolve().parents[1]
    if str(owner_root) not in sys.path:
        sys.path.insert(0, str(owner_root))
    from src.prompt_manifest_compiler_seq001_v001 import decode_file_intent

    folder_manifests = _folder_manifests(root, changed)
    latest_prompt_packet = _load_json(root / "logs" / "prompt_context_packet_latest.json") or {}
    packet = {
        "schema": "deepseek_push_code_audit/v1",
        "audit_id": "ds-push-" + _sha("|".join(changed) + datetime.now(timezone.utc).isoformat()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "state_contract": {
            "auditor": "deepseek",
            "verifier": "opus_master_manifest_session",
            "scope": "push_changed_files_plus_manifest_state",
            "write_policy": "advisory_packet_only",
        },
        "changed_files": changed[:120],
        "file_name_changelog": [decode_file_intent(rel) for rel in changed[:120]],
        "master_manifest": _read_limited(root / "MANIFEST.md", 12000),
        "folder_manifests": folder_manifests,
        "prompt_context_packet": {
            "path": "logs/prompt_context_packet_latest.json",
            "prompt_hash": latest_prompt_packet.get("prompt_hash"),
            "role_contract": latest_prompt_packet.get("role_contract"),
            "intent_key_encoding": latest_prompt_packet.get("intent_key_encoding"),
        },
        "deepseek_prompt": _render_deepseek_prompt(changed, folder_manifests),
        "opus_verification": {
            "status": "pending",
            "expected_output": "weaknesses, unsafe edits, missing tests, manifest comments, prompt repair notes",
        },
    }
    if write:
        _write_json(root / "logs" / "deepseek_push_audit_latest.json", packet)
        _append_jsonl(root / "logs" / "deepseek_push_audits.jsonl", packet)
        _append_jsonl(root / "logs" / "deepseek_prompt_jobs.jsonl", _job(packet))
    return packet


def _render_deepseek_prompt(changed: list[str], manifests: list[dict[str, Any]]) -> str:
    files = "\n".join(f"- {rel}" for rel in changed[:80]) or "- no changed files detected"
    folders = "\n".join(f"- {row['manifest']} touched={len(row['touched_files'])}" for row in manifests[:40])
    return "\n".join([
        "You are DeepSeek acting as folder manifest manager and push auditor.",
        "Audit code weakness from master manifest state, folder manifest state, filename intent encoding, and changed files.",
        "Do not mutate durable memory or write code. Emit findings for Opus/master manifest verification.",
        "",
        "Required sections:",
        "1. risky or incoherent mutations",
        "2. missing tests or stale manifest state",
        "3. file-name changelog mismatches",
        "4. suggested manifest comments",
        "5. prompt-box repair instructions for Codex/Copilot",
        "",
        "Changed files:",
        files,
        "",
        "Folder manifests:",
        folders or "- no folder manifests in scope",
    ]) + "\n"


def _folder_manifests(root: Path, changed: list[str]) -> list[dict[str, Any]]:
    folders = sorted({str(Path(rel).parent).replace("\\", "/") for rel in changed if Path(rel).parent.as_posix() != "."})
    rows = []
    for folder in folders[:50]:
        manifest = root / folder / "MANIFEST.md"
        rows.append({
            "folder": folder,
            "manifest": f"{folder}/MANIFEST.md",
            "exists": manifest.exists(),
            "touched_files": [rel for rel in changed if rel.startswith(folder.rstrip("/") + "/")][:40],
            "content_excerpt": _read_limited(manifest, 5000),
        })
    return rows


def _job(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "deepseek_prompt_job/v1",
        "job_id": packet["audit_id"],
        "mode": "deepseek_push_code_audit",
        "ts": packet["ts"],
        "status": "queued",
        "prompt": packet["deepseek_prompt"],
        "input_packet": "logs/deepseek_push_audit_latest.json",
        "expected_result": "logs/deepseek_push_audit_result_<job_id>.json",
    }


def _git_changed_files(root: Path) -> list[str]:
    out: list[str] = []
    commands = [["git", "diff", "--name-only"], ["git", "diff", "--name-only", "--cached"], ["git", "diff", "--name-only", "@{u}..HEAD"]]
    for cmd in commands:
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode == 0:
            out.extend(line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip())
    return [rel for rel in dict.fromkeys(out) if not rel.endswith("MANIFEST.md")]


def _read_limited(path: Path, limit: int) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-root", default="")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()
    root = Path(args.target_root).resolve() if args.target_root else _repo_root()
    packet = build_deepseek_push_audit(root, write=not args.no_write)
    print(f"deepseek_push_audit: {packet['audit_id']} files={len(packet['changed_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
