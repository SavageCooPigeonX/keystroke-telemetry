"""codebase_detector_seq001_v001.py — pluggable codebase state detection.

Scans any project root for structured metadata files. Returns a compact
state representation that Gemini uses as context. Works with pigeon,
Python, Node.js, Rust, or any codebase with structured naming.

Zero LLM calls. Pure file scanning.

Usage:
    from src.codebase_detector_seq001_v001 import detect_codebase
    profile = detect_codebase(Path('.'))
    print(profile.state_text)  # compact context for LLM prompt
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path

_STRUCTURE_FILES = {
    'pigeon_registry': 'pigeon_registry.json',
    'file_profiles': 'file_profiles.json',
    'file_heat_map': 'file_heat_map.json',
    'operator_profile': 'operator_profile.md',
    'package_json': 'package.json',
    'pyproject': 'pyproject.toml',
    'cargo': 'Cargo.toml',
    'manifest': 'MANIFEST.md',
}


@dataclass
class CodebaseProfile:
    root: Path = field(default_factory=Path)
    name: str = ''
    kind: str = 'generic'
    modules: int = 0
    structured_files: dict = field(default_factory=dict)
    naming_pattern: str = 'standard'
    state_text: str = ''


def detect_codebase(root: Path) -> CodebaseProfile:
    """Scan root for structured metadata — returns compact profile."""
    profile = CodebaseProfile(root=root, name=root.name)
    for key, fname in _STRUCTURE_FILES.items():
        p = root / fname
        if p.exists():
            profile.structured_files[key] = p
    if 'pigeon_registry' in profile.structured_files:
        profile.kind = 'pigeon'
        profile.naming_pattern = 'semantic_glyph'
    elif 'cargo' in profile.structured_files:
        profile.kind = 'rust'
    elif 'package_json' in profile.structured_files:
        profile.kind = 'node'
    elif 'pyproject' in profile.structured_files:
        profile.kind = 'python'
    profile.modules = _count_modules(root, profile.kind)
    profile.state_text = _build_state_text(profile)
    return profile


def _count_modules(root: Path, kind: str) -> int:
    if kind == 'pigeon':
        reg = root / 'pigeon_registry.json'
        if reg.exists():
            try:
                data = json.loads(reg.read_text('utf-8', errors='ignore'))
                return len(data.get('files', []))
            except Exception:
                pass
    count = 0
    for pat in ('src/**/*.py', 'lib/**/*.py', 'src/**/*.ts', 'src/**/*.rs'):
        count += len(list(root.glob(pat)))
    return count


def _build_state_text(profile: CodebaseProfile) -> str:
    parts = [f'Project: {profile.name} ({profile.kind}, {profile.modules} modules, naming={profile.naming_pattern})']
    builders = {'pigeon': _pigeon_state, 'python': _python_state, 'node': _node_state}
    builder = builders.get(profile.kind)
    if builder:
        parts.extend(builder(profile))
    return '\n'.join(parts)


def _pigeon_state(profile: CodebaseProfile) -> list[str]:
    parts = []
    reg_path = profile.structured_files.get('pigeon_registry')
    if reg_path:
        try:
            data = json.loads(reg_path.read_text('utf-8', errors='ignore'))
            files = data.get('files', [])
            by_ver = sorted(files, key=lambda f: f.get('ver', 0), reverse=True)[:10]
            active = ', '.join(f"{f['name']}(v{f['ver']})" for f in by_ver)
            parts.append(f'Most active: {active}')
            intents = {}
            for f in files:
                ic = f.get('intent_code', 'OT')
                intents[ic] = intents.get(ic, 0) + 1
            top = sorted(intents.items(), key=lambda x: -x[1])[:5]
            parts.append(f'Intent spread: {", ".join(f"{k}={v}" for k,v in top)}')
        except Exception:
            pass
    heat_path = profile.structured_files.get('file_heat_map')
    if heat_path:
        try:
            heat = json.loads(heat_path.read_text('utf-8', errors='ignore'))
            hot = []
            for mod, d in heat.items():
                samples = d.get('samples', [])
                if samples:
                    avg = sum(s.get('hes', 0) for s in samples) / len(samples)
                    if avg > 0.5:
                        hot.append((mod, avg))
            hot.sort(key=lambda x: -x[1])
            if hot:
                parts.append(f'High cognitive load: {", ".join(f"{m}({h:.2f})" for m,h in hot[:5])}')
        except Exception:
            pass
    prof_path = profile.structured_files.get('file_profiles')
    if prof_path:
        try:
            profiles = json.loads(prof_path.read_text('utf-8', errors='ignore'))
            fears = {}
            for mod, p in profiles.items():
                for fear in p.get('fears', []):
                    fears[fear] = fears.get(fear, 0) + 1
            top_fears = sorted(fears.items(), key=lambda x: -x[1])[:5]
            if top_fears:
                parts.append(f'Common fears: {", ".join(f"{f}({c})" for f,c in top_fears)}')
        except Exception:
            pass
    return parts


def _python_state(profile: CodebaseProfile) -> list[str]:
    parts = []
    pp = profile.structured_files.get('pyproject')
    if pp:
        try:
            text = pp.read_text('utf-8', errors='ignore')
            for line in text.split('\n'):
                if line.strip().startswith('name'):
                    parts.append(f'Name: {line.split("=")[-1].strip().strip(chr(34))}')
                    break
        except Exception:
            pass
    return parts


def _node_state(profile: CodebaseProfile) -> list[str]:
    parts = []
    pkg = profile.structured_files.get('package_json')
    if pkg:
        try:
            data = json.loads(pkg.read_text('utf-8', errors='ignore'))
            parts.append(f'Name: {data.get("name", "?")}')
            deps = list(data.get('dependencies', {}).keys())[:10]
            if deps:
                parts.append(f'Deps: {", ".join(deps)}')
        except Exception:
            pass
    return parts
