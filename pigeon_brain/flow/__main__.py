# pigeon_brain/flow/__main__.py — CLI entry point
"""
Usage:
    py -m pigeon_brain.flow "Fix the hardcoded import in __main__.py"
    py -m pigeon_brain.flow --mode heat "self_fix keeps failing"
    py -m pigeon_brain.flow --multi "import rewriter breaks after rename"
    py -m pigeon_brain.flow --origin self_fix "analyze why v10 has high drama"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .flow_engine_seq003_v002_d0324__the_flow_engine_is_the_lc_flow_engine_context import run_flow, run_multi
from .task_writer_seq005_v002_d0324__the_river_delta_where_all_lc_flow_engine_context import write_task, write_multi


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flow engine — context-accumulating dataflow through the code graph"
    )
    parser.add_argument("task", help="The task/bug/question to flow through the graph")
    parser.add_argument("--mode", choices=["targeted", "heat", "failure"],
                        default="targeted", help="Path selection mode")
    parser.add_argument("--multi", action="store_true",
                        help="Run all 3 modes and merge perspectives")
    parser.add_argument("--origin", default=None,
                        help="Explicit start node (auto-detected if omitted)")
    parser.add_argument("--root", default=".", help="Project root")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if args.multi:
        packets = run_multi(root, args.task, origin=args.origin)
        output = write_multi(packets)
    else:
        packet = run_flow(root, args.task, mode=args.mode, origin=args.origin)
        output = write_task(packet)

    print(output)


if __name__ == "__main__":
    main()
