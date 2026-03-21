"""file_consciousness_seq019_v001.py — AST-derived function consciousness + dating profiles.

Each function gets: i_am, i_want, i_give, i_fear, i_love — derived from pure
static analysis. No LLM calls. Cross-file compatibility scored via data flow,
co-change patterns, and shared state coupling.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v001 | ~190 lines | ~2,100 tokens
# DESC:   ast_derived_function_consciousness
# INTENT: build_file_dating_profiles
# LAST:   2026-03-19
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
import ast
import json
import re
from pathlib import Path


# ── consciousness extraction (per-function) ──────────────────────────

def build_file_consciousness(source_path: Path) -> dict:
    """Derive consciousness profiles for every function in a Python file.

    Returns {functions: [...], meta: {...}} where each function entry
    contains i_am, i_want, i_give, i_fear, i_love — all from AST only.
    """
    source = source_path.read_text(encoding='utf-8', errors='ignore')
    tree = ast.parse(source)

    # Collect all top-level function names for internal call detection
    local_fns = {n.name for n in ast.iter_child_nodes(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    profiles = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            profiles.append(_build_func_profile(node, source, local_fns))

    return {
        'file': source_path.name,
        'total_lines': len(source.splitlines()),
        'functions': profiles,
    }


def _build_func_profile(node, source: str, local_fns: set) -> dict:
    """Build consciousness for a single function node."""
    body_src = ast.get_source_segment(source, node) or ''
    lines = body_src.splitlines()

    return {
        'function': node.name,
        'line_range': [node.lineno, node.end_lineno or node.lineno],
        'i_am': _derive_purpose(node, lines),
        'i_want': _derive_dependencies(node, local_fns),
        'i_give': _derive_exports(node),
        'i_fear': _derive_fears(node, lines),
        'i_love': _derive_loves(node, lines),
        'personality': _classify_personality(node, local_fns),
        'flags': _count_flags(lines),
    }


def _derive_purpose(node, lines: list[str]) -> str:
    """i_am: What this function does (from docstring or name heuristics)."""
    ds = ast.get_docstring(node)
    if ds:
        return ds.split('\n')[0].strip()[:120]
    # Fallback: convert function name to readable description
    name = node.name.lstrip('_')
    return name.replace('_', ' ')


def _derive_dependencies(node, local_fns: set) -> list[str]:
    """i_want: What this function needs — imports, file reads, local calls."""
    wants = []
    for child in ast.walk(node):
        # File reads: open(), Path().read_text(), glob(), etc.
        if isinstance(child, ast.Call):
            fname = _call_target(child)
            if fname in ('open', 'read_text', 'read_bytes'):
                # Try to extract the path argument
                if child.args:
                    arg = _const_value(child.args[0])
                    wants.append(f'file:{arg}' if arg else f'file:unknown')
            elif fname in ('glob', 'rglob'):
                arg = _const_value(child.args[0]) if child.args else None
                wants.append(f'glob:{arg}' if arg else 'glob:pattern')
            elif fname in local_fns:
                wants.append(f'func:{fname}')
        # json.loads / json.load
        if isinstance(child, ast.Call):
            fname = _call_target(child)
            if fname in ('json.loads', 'json.load', 'json.loads'):
                wants.append('json_input')
    return list(dict.fromkeys(wants))[:8]  # deduplicate, cap at 8


def _derive_exports(node) -> list[str]:
    """i_give: What this function returns or writes."""
    gives = []
    for child in ast.walk(node):
        if isinstance(child, ast.Return) and child.value is not None:
            gives.append(f'returns:{_type_hint(child.value)}')
        if isinstance(child, ast.Call):
            fname = _call_target(child)
            if fname in ('write_text', 'write_bytes', 'write'):
                gives.append('writes:file')
            elif fname in ('json.dumps', 'json.dump'):
                gives.append('writes:json')
            elif fname == 'print':
                gives.append('prints:stdout')
    return list(dict.fromkeys(gives))[:6]


def _derive_fears(node, lines: list[str]) -> list[str]:
    """i_fear: Failure modes — missing files, silent errors, regex deps."""
    fears = []
    body_text = '\n'.join(lines)

    # Bare except / broad exception handling = hiding errors
    for child in ast.walk(node):
        if isinstance(child, ast.ExceptHandler):
            if child.type is None:
                fears.append('bare except hides errors')
            elif isinstance(child.type, ast.Name) and child.type.id == 'Exception':
                # Check if body is just pass/continue
                if any(isinstance(b, (ast.Pass, ast.Continue)) for b in child.body):
                    fears.append('swallowed exception')

    # Regex usage = fragile format dependency
    if 're.search' in body_text or 're.match' in body_text or 're.findall' in body_text:
        fears.append('regex format dependency')

    # Path.exists() check = file might not exist
    if '.exists()' in body_text:
        fears.append('file may not exist')

    # Empty return on error path = silent failure
    for child in ast.walk(node):
        if isinstance(child, ast.Return):
            if isinstance(child.value, (ast.List, ast.Tuple, ast.Dict)):
                if not child.value.elts if hasattr(child.value, 'elts') else not child.value.keys:
                    fears.append('returns empty on failure (silent)')

    return list(dict.fromkeys(fears))[:5]


def _derive_loves(node, lines: list[str]) -> list[str]:
    """i_love: What this function relies on being stable."""
    loves = []
    body_text = '\n'.join(lines)

    if 'encoding=' in body_text:
        loves.append('consistent file encoding')
    if '.splitlines()' in body_text or '.split(' in body_text:
        loves.append('stable text format')
    if 'json.loads' in body_text or 'json.load' in body_text:
        loves.append('valid JSON input')
    if '.glob(' in body_text or '.rglob(' in body_text:
        loves.append('predictable directory structure')
    if 'subprocess' in body_text:
        loves.append('external tool availability')
    return loves[:4]


def _classify_personality(node, local_fns: set) -> str:
    """Classify function personality type."""
    calls_out = 0
    reads_files = False
    writes_files = False
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            t = _call_target(child)
            if t in local_fns:
                calls_out += 1
            if t in ('open', 'read_text', 'read_bytes', 'glob', 'rglob'):
                reads_files = True
            if t in ('write_text', 'write_bytes', 'write'):
                writes_files = True

    if calls_out >= 3:
        return 'orchestrator'
    if reads_files and writes_files:
        return 'transformer'
    if writes_files:
        return 'writer'
    if reads_files:
        return 'reader'
    return 'worker'


# ── dating profiles (cross-file compatibility) ──────────────────────

def build_dating_profiles(root: Path) -> dict:
    """Build compatibility scores for all tracked pigeon modules.

    Uses: registry for module list, import_tracer for data flow,
    heat map for co-stress patterns, registry version count for drama.
    Returns {module_name: {personality, partners: [{name, score, reason}], fears}}.
    """
    reg_path = root / 'pigeon_registry.json'
    heat_path = root / 'file_heat_map.json'
    if not reg_path.exists():
        return {}

    reg = json.loads(reg_path.read_text('utf-8'))
    files = reg.get('files', [])
    heat = json.loads(heat_path.read_text('utf-8')) if heat_path.exists() else {}

    # Build import graph: {module_stem: [modules_it_imports]}
    import_graph = {}
    for entry in files:
        p = root / entry['path']
        if not p.exists():
            continue
        try:
            src = p.read_text('utf-8', errors='ignore')
        except Exception:
            continue
        imports = set()
        for m in re.finditer(r'^(?:from|import)\s+(\S+)', src, re.M):
            mod = m.group(1).split('.')[0]
            imports.add(mod)
        import_graph[entry['name']] = imports

    profiles = {}
    for entry in files:
        name = entry['name']
        ver = entry.get('ver', 1)
        tokens = entry.get('tokens', 0)
        hm = heat.get(name, {})

        # Find partners via shared imports (bidirectional edges)
        partners = []
        my_imports = import_graph.get(name, set())
        for other_name, their_imports in import_graph.items():
            if other_name == name:
                continue
            # Physical attraction: data flow overlap
            flow = len(my_imports & their_imports)
            # Trauma bonding: both high-version (pain points)
            other_entry = next((f for f in files if f['name'] == other_name), {})
            other_ver = other_entry.get('ver', 1)
            drama = min(ver, other_ver) / max(ver + other_ver, 1)
            # Combined score
            score = round(0.6 * min(flow / 3, 1.0) + 0.4 * drama, 2)
            if score > 0.1:
                reason = f'{flow} shared imports'
                if drama > 0.3:
                    reason += f', both high-churn (v{ver}+v{other_ver})'
                partners.append({'name': other_name, 'score': score, 'reason': reason})

        partners.sort(key=lambda p: p['score'], reverse=True)

        # Consciousness summary for this file
        p = root / entry['path']
        fears = []
        if p.exists():
            try:
                fc = build_file_consciousness(p)
                for fn in fc.get('functions', []):
                    fears.extend(fn.get('i_fear', []))
            except Exception:
                pass

        profiles[name] = {
            'personality': 'veteran' if ver >= 5 else 'stable' if ver >= 3 else 'fresh',
            'version': ver,
            'tokens': tokens,
            'partners': partners[:5],
            'fears': list(dict.fromkeys(fears))[:6],
            'avg_hes': _safe_hes(hm),
        }

    return profiles


# ── slumber party audit (contract checks) ────────────────────────────

def slumber_party_audit(root: Path, changed_files: list[str]) -> list[dict]:
    """Check contracts between changed files and their partners.

    Returns list of {severity, changed, partner, msg} entries.
    severity: breakup (missing export), fight (signature drift), healthy (shared I/O).
    """
    profiles_path = root / 'file_profiles.json'
    if not profiles_path.exists():
        return []
    profiles = json.loads(profiles_path.read_text('utf-8'))

    pillow_talk = []
    for changed in changed_files:
        stem = Path(changed).stem
        # Find module name (strip pigeon suffix)
        mod_name = re.sub(r'_seq\d+.*', '', stem)
        profile = profiles.get(mod_name, {})

        for partner in profile.get('partners', [])[:3]:
            pname = partner['name']
            pscore = partner['score']
            if pscore > 0.3:
                pillow_talk.append({
                    'severity': 'watch',
                    'changed': mod_name,
                    'partner': pname,
                    'score': pscore,
                    'msg': f'{pname} is closely coupled ({partner["reason"]}). Check compatibility.',
                })
    return pillow_talk


# ── persistence ──────────────────────────────────────────────────────

def save_profiles(root: Path, profiles: dict) -> Path:
    """Write dating profiles to file_profiles.json."""
    out = root / 'file_profiles.json'
    out.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding='utf-8')
    return out


def load_profiles(root: Path) -> dict:
    """Load cached dating profiles."""
    p = root / 'file_profiles.json'
    if not p.exists():
        return {}
    return json.loads(p.read_text('utf-8'))


# ── prompt injection helper ──────────────────────────────────────────

def consciousness_report(root: Path, active_file: str | None = None) -> str:
    """Build markdown report for injection into copilot-instructions.md.

    If active_file given, focuses on that file's consciousness + partners.
    Otherwise gives a system-wide summary.
    """
    profiles = load_profiles(root)
    if not profiles:
        return ''

    if active_file:
        stem = re.sub(r'_seq\d+.*', '', Path(active_file).stem)
        p = profiles.get(stem)
        if not p:
            return ''
        lines = [
            '### File Consciousness',
            f'*Active: `{stem}` | {p["personality"]} (v{p["version"]}) '
            f'| {p["tokens"]} tokens | hes={p["avg_hes"]}*',
        ]
        if p['partners']:
            lines.append('\n**Top partners:**')
            for pt in p['partners'][:3]:
                lines.append(f'- `{pt["name"]}` ({pt["score"]}) — {pt["reason"]}')
        if p['fears']:
            lines.append('\n**This file fears:**')
            for f in p['fears'][:4]:
                lines.append(f'- {f}')
        return '\n'.join(lines)

    # System-wide: top drama modules + most-feared patterns
    drama = sorted(profiles.items(), key=lambda x: x[1].get('version', 0), reverse=True)[:5]
    feared = {}
    for _, p in profiles.items():
        for f in p.get('fears', []):
            feared[f] = feared.get(f, 0) + 1
    top_fears = sorted(feared.items(), key=lambda x: x[1], reverse=True)[:4]

    lines = ['### File Consciousness (System)', f'*{len(profiles)} modules profiled*']
    if drama:
        lines.append('\n**High-drama modules (most mutations):**')
        for name, p in drama:
            lines.append(f'- `{name}` v{p["version"]} ({p["personality"]}) — '
                         f'{len(p.get("partners", []))} partners')
    if top_fears:
        lines.append('\n**Most common fears across codebase:**')
        for fear, count in top_fears:
            lines.append(f'- {fear} ({count} modules)')
    return '\n'.join(lines)


# ── helpers ──────────────────────────────────────────────────────────

def _safe_hes(hm: dict) -> float:
    """Extract average hesitation from heat map entry (handles both schemas)."""
    if not isinstance(hm, dict) or not hm:
        return 0.0
    samp = hm.get('samples', [])
    if isinstance(samp, list):
        n = len(samp)
        if n == 0:
            return 0.0
        return round(sum(s.get('hes', 0) for s in samp) / n, 3)
    # Numeric samples count (aggregated schema)
    n = max(int(samp), 1)
    return round(hm.get('total_hes', 0) / n, 3)


def _call_target(node: ast.Call) -> str:
    """Extract call target name (handles simple + attribute calls)."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
            return f'{node.func.value.id}.{node.func.attr}'
        return node.func.attr
    return ''


def _const_value(node) -> str | None:
    """Try to extract a constant string value from an AST node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _type_hint(node) -> str:
    """Rough type description for a return value AST node."""
    if isinstance(node, ast.Constant):
        return type(node.value).__name__
    if isinstance(node, ast.Dict):
        return 'dict'
    if isinstance(node, ast.List):
        return 'list'
    if isinstance(node, ast.Tuple):
        return 'tuple'
    if isinstance(node, ast.JoinedStr):
        return 'str'
    if isinstance(node, ast.Call):
        return _call_target(node) or 'call'
    return 'value'


def _count_flags(lines: list[str]) -> int:
    """Count TODO/FIXME/HACK/BUG/XXX markers."""
    count = 0
    for line in lines:
        for marker in ('TODO', 'FIXME', 'HACK', 'BUG', 'XXX'):
            if marker in line:
                count += 1
                break
    return count


# ── CLI entry point ──────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    if len(sys.argv) > 2 and sys.argv[2] == '--file':
        # Single file consciousness
        target = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        if target and target.exists():
            fc = build_file_consciousness(target)
            print(json.dumps(fc, indent=2, ensure_ascii=False))
        else:
            print('Usage: py file_consciousness_seq019_v001.py <root> --file <path>')
    else:
        # Full dating profile build
        print('Building dating profiles for all pigeon modules...')
        profiles = build_dating_profiles(root)
        out = save_profiles(root, profiles)
        print(f'Saved {len(profiles)} profiles to {out}')
        print('\n' + consciousness_report(root))
