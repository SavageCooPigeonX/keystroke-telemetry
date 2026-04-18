"""修f_sf_s013_v012_d0402_初写谱净拆_λVR_scan_cross_file_coupling_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import os
import re

def _scan_cross_file_coupling(root: Path, registry: dict) -> list[dict]:
    """Build import graph and find high-coupling modules."""
    import_graph: dict[str, set] = {}  # file -> set of files it imports from
    name_to_path: dict[str, str] = {}  # module stem -> registry path

    for entry in registry:
        stem = Path(entry['path']).stem
        # Strip pigeon metadata to get base module name
        base = re.sub(r'_seq\d+.*$', '', stem)
        name_to_path[base] = entry['path']
        name_to_path[stem] = entry['path']

    for entry in registry:
        fp = root / entry['path']
        if not fp.exists():
            continue
        try:
            tree = ast.parse(fp.read_text(encoding='utf-8'))
        except Exception:
            continue
        deps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                # Extract the leaf module name
                parts = node.module.split('.')
                leaf = parts[-1]
                base_leaf = re.sub(r'_seq\d+.*$', '', leaf)
                target = name_to_path.get(leaf) or name_to_path.get(base_leaf)
                if target and target != entry['path']:
                    deps.add(target)
        import_graph[entry['path']] = deps

    # Find files with high fan-in (many dependents)
    fan_in: dict[str, int] = {}
    for src_file, deps in import_graph.items():
        for dep in deps:
            fan_in[dep] = fan_in.get(dep, 0) + 1

    problems = []
    for path, count in sorted(fan_in.items(), key=lambda x: -x[1]):
        if count >= 5:
            problems.append({
                'type': 'high_coupling',
                'file': path,
                'fan_in': count,
                'severity': 'info',
                'fix': f'Module has {count} dependents — changes here break many files',
            })

    return problems, import_graph
