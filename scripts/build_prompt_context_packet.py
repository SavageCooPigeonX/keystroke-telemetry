"""Build the file-sim prompt packet before Codex/Copilot acts."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, encoding="utf-8")
    return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else Path.cwd()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="", help="operator prompt; defaults to latest prompt journal entry")
    parser.add_argument("--source", default="codex")
    parser.add_argument("--target-root", default="")
    parser.add_argument("--focus-file", action="append", default=[])
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--skip-micro-pulse", action="store_true")
    args = parser.parse_args()

    root = Path(args.target_root).resolve() if args.target_root else _repo_root()
    owner_root = Path(__file__).resolve().parents[1]
    if str(owner_root) not in sys.path:
        sys.path.insert(0, str(owner_root))
    micro_pulse = None
    if not args.skip_micro_pulse:
        from src.opus_micro_pulse_runtime_seq001_v001 import build_opus_micro_pulse_runtime

        micro_pulse = build_opus_micro_pulse_runtime(root, args.prompt or None, write=not args.no_write)

    from src.prompt_manifest_compiler_seq001_v001 import build_prompt_context_packet

    packet = build_prompt_context_packet(
        root,
        args.prompt,
        source=args.source,
        focus_files=args.focus_file or None,
        write=not args.no_write,
    )
    if not args.no_write:
        from src.root_sim_key_file_seq001_v001 import build_root_sim_key_file

        build_root_sim_key_file(root, write=True)
        from src.cannon_execution_gate_seq001_v001 import build_cannon_execution_gate

        gate_prompt = args.prompt or ((micro_pulse or {}).get("operator_prompt") or packet.get("operator_prompt") or "")
        gate = build_cannon_execution_gate(root, gate_prompt, write=True)
        if not gate["cleared"]:
            print("cannon_gate: blocked " + ", ".join(gate["blockers"]))
            return 2
    print(f"prompt_context_packet: {packet['prompt_hash']} files={len(packet['file_name_changelog'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
