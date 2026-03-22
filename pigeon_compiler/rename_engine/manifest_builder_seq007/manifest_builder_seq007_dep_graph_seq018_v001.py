"""manifest_builder_seq007_dep_graph_seq018_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _build_dep_graph(file_records: list[dict], folder: Path) -> list[str]:
    """Build a simple ASCII dependency graph between files in the folder."""
    # Map short stems to file names for intra-folder links
    stem_map = {}
    for rec in file_records:
        short = re.sub(r'_seq\d+.*', '', Path(rec['name']).stem)
        stem_map[short] = rec['name']

    graph_lines = []
    for rec in file_records:
        short_name = re.sub(r'_seq\d+.*', '', Path(rec['name']).stem)
        targets = [d for d in rec['deps'] if d in stem_map and d != short_name]
        if targets:
            arrow_targets = ', '.join(targets)
            graph_lines.append(f'{short_name} --> {arrow_targets}')
    return graph_lines
