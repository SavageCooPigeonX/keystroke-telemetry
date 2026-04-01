"""Symbol dictionary generator for Pigeon Code v4.0 Glyph System.

Reads pigeon_registry.json + git log and generates dictionary.pgd —
a symbol-to-meaning mapping that overlays the existing long filenames.

Filenames stay long. The dictionary is an additional layer for LLM
context compression: ~300-500 tokens to encode the entire codebase
architecture vs thousands of tokens reading raw filenames.
"""
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-01T04:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  initial symbol dictionary generator
# EDIT_STATE: harvested
# ── /pulse ──

from __future__ import annotations
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# ── Greek uppercase pool for top-level modules ──
_GREEK_UPPER = list(
    'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'
)
# Extended pool if we run out of 24 Greek letters
_EXTENDED_POOL = list(
    'ℵℶℷℸ𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ'
)

# ── Mnemonic hints: try to match glyph to module meaning ──
_MNEMONIC_MAP = {
    'prediction_scorer': 'Ψ',   # psi → prediction
    'self_fix': 'Σ',            # sigma → self
    'context_budget': 'Θ',     # theta → threshold/budget
    'dynamic_prompt': 'Δ',     # delta → dynamic
    'push_narrative': 'Ω',     # omega → output/push
    'cognitive_reactor': 'Φ',  # phi → cognition
    'flow_engine': 'Λ',        # lambda → flow
    'pigeon_compiler': 'Π',    # pi → pigeon
    'graph_extractor': 'Γ',    # gamma → graph
    'logger': 'Λ',             # (will be reassigned if conflict)
    'models': 'Μ',             # mu → models
    'drift_watcher': 'Δ',      # (will be reassigned if conflict)
    'streaming_layer': 'Σ',    # (will be reassigned if conflict)
    'resistance_bridge': 'Ρ',  # rho → resistance
    'operator_stats': 'Ο',     # omicron → operator
    'file_heat_map': 'Η',      # eta → heat
    'research_lab': 'Ρ',       # (will be reassigned if conflict)
}

# ── Intent lambda codes ──
_INTENT_PREFIXES = {
    'dynamic_import_resolvers': 'λR',
    'pigeon_split_3': 'λS',
    'organism_health_system': 'λH',
    'gemini_flash_enricher': 'λF',
    '8888_word_backpropagation': 'λB',
    'windows_max_path': 'λW',
    'desc_upgrade': 'λD',
    'mutation_patch_pipeline': 'λM',
    'intent_deletion_pipeline': 'λI',
    'staleness_alerts_bg': 'λA',
    'pigeon_brain_system': 'λP',
    'push_narratives_timeout': 'λT',
    'research_lab_autonomous': 'λL',
    'task_queue_system': 'λQ',
    'pulse_telemetry_prompt': 'λΠ',
    'import_rewriter_now': 'λΞ',
    'rework_signal_0': 'λρ',
    'stage_78_hook': 'λ7',
    'wpm_outlier_filter': 'λω',
    'fire_full_post': 'λφ',
    'fix_bare_globals': 'λγ',
    'fix_push_cycle': 'λπ',
    'flow_engine_context': 'λε',
    'gemini_chat_dead': 'λχ',
    'implement_all_18': 'λ18',
    'multi_line_import': 'λμ',
    'per_prompt_deleted': 'λδ',
    'readme_update_7': 'λ7u',
    'trigger_pigeon_rename': 'λτ',
    'verify_pigeon_plugin': 'λν',
}


def _get_git_log(root: Path, n: int = 20) -> list[dict]:
    """Get recent git commits as change history."""
    try:
        result = subprocess.run(
            ['git', 'log', f'-{n}', '--format=%H|%ai|%s'],
            capture_output=True, text=True, cwd=str(root),
            timeout=10
        )
        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 2)
            if len(parts) == 3:
                commits.append({
                    'hash': parts[0][:8],
                    'date': parts[1][:10],
                    'msg': parts[2][:80]
                })
        return commits
    except Exception:
        return []


def _assign_module_glyphs(
    top_modules: list[str],
) -> dict[str, str]:
    """Assign Greek glyphs to top-level modules.

    Uses mnemonics where possible, sequential assignment otherwise.
    """
    assigned: dict[str, str] = {}
    used_glyphs: set[str] = set()

    # First pass: mnemonic assignments
    for mod in top_modules:
        if mod in _MNEMONIC_MAP:
            glyph = _MNEMONIC_MAP[mod]
            if glyph not in used_glyphs:
                assigned[mod] = glyph
                used_glyphs.add(glyph)

    # Second pass: sequential for unassigned
    pool_idx = 0
    full_pool = _GREEK_UPPER + _EXTENDED_POOL
    for mod in top_modules:
        if mod in assigned:
            continue
        while pool_idx < len(full_pool) and full_pool[pool_idx] in used_glyphs:
            pool_idx += 1
        if pool_idx < len(full_pool):
            assigned[mod] = full_pool[pool_idx]
            used_glyphs.add(full_pool[pool_idx])
            pool_idx += 1
        else:
            # Fallback: use first 2 chars uppercase
            assigned[mod] = mod[:2].upper()

    return assigned


def _assign_intent_glyphs(intents: list[str]) -> dict[str, str]:
    """Assign lambda codes to intents."""
    assigned: dict[str, str] = {}
    used: set[str] = set()
    fallback_idx = 0

    for intent in intents:
        if intent in _INTENT_PREFIXES:
            code = _INTENT_PREFIXES[intent]
            assigned[intent] = code
            used.add(code)
        else:
            # Generate from first letter
            while True:
                code = f'λ{chr(97 + fallback_idx)}'
                if code not in used:
                    break
                fallback_idx += 1
            assigned[intent] = code
            used.add(code)
            fallback_idx += 1

    return assigned


def _extract_top_modules(files: list[dict]) -> list[str]:
    """Extract top-level (root) module names.

    A root module is a name that appears in the registry and is NOT
    a decomposed child (child names contain their parent's name as prefix).
    """
    all_names = sorted(set(f['name'] for f in files))
    # Identify children: names like "self_fix_seq013_scan_hardcoded"
    # whose prefix matches another module "self_fix"
    children = set()
    for name in all_names:
        for other in all_names:
            if other != name and name.startswith(other + '_seq'):
                children.add(name)
                break
    # Also identify streaming_layer_* pattern children
    for name in all_names:
        for other in all_names:
            if other != name and name.startswith(other + '_'):
                if other not in children:
                    children.add(name)
                    break
    roots = [n for n in all_names if n not in children]
    return sorted(roots)


def _build_module_entries(
    files: list[dict],
    module_glyphs: dict[str, str],
    intent_glyphs: dict[str, str],
) -> dict:
    """Build per-module dictionary entries."""
    modules = {}
    # Sort module names longest-first for greedy prefix matching
    sorted_mods = sorted(module_glyphs.keys(), key=len, reverse=True)

    for f in files:
        name = f['name']

        # Find the longest module name that is a prefix of this file's name
        matched_module = None
        matched_glyph = None
        for mod in sorted_mods:
            if name == mod or name.startswith(mod + '_'):
                matched_module = mod
                matched_glyph = module_glyphs[mod]
                break

        # Exact match fallback
        if not matched_module and name in module_glyphs:
            matched_module = name
            matched_glyph = module_glyphs[name]

        # Last resort: assign to '?' group
        if not matched_module:
            matched_module = name
            matched_glyph = module_glyphs.get(name, '?')

        glyph_key = matched_glyph
        if glyph_key not in modules:
            modules[glyph_key] = {
                'name': matched_module,
                'folder': str(Path(f['path']).parent).replace('\\', '/'),
                'files': [],
            }

        intent_code = intent_glyphs.get(f.get('intent', ''), '')
        history = []
        for h in f.get('history', []):
            history.append({
                'v': h.get('ver', '?'),
                'd': h.get('date', '?'),
                'action': h.get('action', '?'),
            })

        modules[glyph_key]['files'].append({
            'name': name,
            'seq': f.get('seq', 0),
            'ver': f.get('ver', 1),
            'date': f.get('date', ''),
            'desc': f.get('desc', '').replace('_', ' '),
            'intent': intent_code,
            'tokens': f.get('tokens', 0),
            'path': f['path'].replace('\\', '/'),
            'history': history,
        })

    return modules


def generate_dictionary(root: Path) -> dict:
    """Generate the full .pgd dictionary from registry + git."""
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        return {'error': 'pigeon_registry.json not found'}

    reg = json.loads(reg_path.read_text('utf-8'))
    files = reg.get('files', [])

    # Extract top-level modules from registry names (not folders)
    top_modules = _extract_top_modules(files)
    intents = sorted(set(
        f.get('intent', '') for f in files if f.get('intent')
    ))

    # Assign glyphs
    module_glyphs = _assign_module_glyphs(top_modules)
    intent_glyphs = _assign_intent_glyphs(intents)

    # Build module entries
    module_entries = _build_module_entries(files, module_glyphs, intent_glyphs)

    # Get git history
    git_log = _get_git_log(root)

    # Build the dictionary
    now = datetime.now(timezone.utc).isoformat()
    dictionary = {
        'version': '0.1.0',
        'generated': now,
        'stats': {
            'total_files': len(files),
            'modules': len(module_entries),
            'intents': len(intent_glyphs),
            'total_glyphs': len(module_glyphs) + len(intent_glyphs),
        },
        'module_glyphs': {
            g: m for m, g in sorted(
                module_glyphs.items(), key=lambda x: x[1]
            )
        },
        'intent_glyphs': {
            g: i for i, g in sorted(
                intent_glyphs.items(), key=lambda x: x[1]
            )
        },
        'modules': module_entries,
        'recent_changes': git_log[:10],
        'meta_glyphs': {
            '·': 'field separator',
            'v': 'version prefix',
            'd': 'date prefix (MMDD)',
            '†': 'auto-extracted by pigeon compiler',
            '‡': 'manually created',
            '→': 'return / produces',
            '←': 'imports from / depends on',
        },
    }

    return dictionary


def generate_compact_injection(dictionary: dict) -> str:
    """Generate a tight injection block for copilot context.

    Target: ~300-500 tokens. Dense lookup table + change summary.
    """
    lines = []
    stats = dictionary['stats']
    lines.append(
        f'[PIGEON DICT v0.1.0 | {stats["total_files"]} files '
        f'| {stats["modules"]} modules | {stats["total_glyphs"]} glyphs]'
    )

    # Module glyph table — one line per glyph, dense
    mg = dictionary.get('module_glyphs', {})
    # Group into rows of 4 for density
    items = [f'{g}={n}' for g, n in mg.items()]
    for i in range(0, len(items), 4):
        lines.append(' | '.join(items[i:i+4]))

    # Intent glyph table — one dense line
    ig = dictionary.get('intent_glyphs', {})
    int_items = [f'{g}={n}' for g, n in ig.items()]
    lines.append('')
    lines.append('Intents: ' + ', '.join(int_items))

    # Change history — top 10 most-churned modules only
    lines.append('')
    lines.append('Hot:')
    churn_ranked = []
    for glyph, data in dictionary.get('modules', {}).items():
        changed = [
            f for f in data.get('files', [])
            if len(f.get('history', [])) > 1
        ]
        if not changed:
            continue
        total_tok = sum(f.get('tokens', 0) for f in data.get('files', []))
        max_v = max(f.get('ver', 0) for f in data.get('files', []))
        total_hist = sum(len(f.get('history', [])) for f in changed)
        chains = []
        for cf in changed[:2]:
            hist = cf.get('history', [])
            chain = '→'.join(f'v{h["v"]}' for h in hist[-3:])
            chains.append(chain)
        churn_ranked.append((
            total_hist, glyph, data['name'], max_v, total_tok, chains
        ))
    churn_ranked.sort(reverse=True)
    for _, glyph, name, max_v, tok, chains in churn_ranked[:10]:
        lines.append(
            f'{glyph} {name} v{max_v} {tok}tok [{" ".join(chains)}]'
        )

    # Recent git commits — just 3
    lines.append('')
    for c in dictionary.get('recent_changes', [])[:3]:
        lines.append(f'{c["hash"]} {c["msg"][:50]}')

    lines.append('[/DICT]')
    return '\n'.join(lines)


DICT_BLOCK_START = '<!-- pigeon:dictionary -->'
DICT_BLOCK_END = '<!-- /pigeon:dictionary -->'
COPILOT_PATH = '.github/copilot-instructions.md'


def inject_dictionary_block(root: Path) -> bool:
    """Regenerate the symbol dictionary and inject into copilot-instructions.md."""
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False

    dictionary = generate_dictionary(root)
    compact = generate_compact_injection(dictionary)
    block = f'{DICT_BLOCK_START}\n## Symbol Dictionary\n\n```\n{compact}\n```\n{DICT_BLOCK_END}'

    text = cp_path.read_text(encoding='utf-8')

    # Use same upsert logic as other managed blocks
    import re
    pattern = re.compile(
        rf'(?ms)^\s*{re.escape(DICT_BLOCK_START)}\s*$\n.*?^\s*{re.escape(DICT_BLOCK_END)}\s*$',
    )
    if pattern.search(text):
        new_text = pattern.sub(block, text)
    else:
        # Insert before auto-index (first managed block in the Module Map section)
        anchor = '<!-- pigeon:auto-index -->'
        if anchor in text:
            idx = text.index(anchor)
            new_text = text[:idx] + block + '\n' + text[idx:]
        else:
            new_text = text.rstrip() + '\n\n' + block + '\n'

    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')

    # Also write standalone files
    (root / 'dictionary.pgd').write_text(
        json.dumps(dictionary, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    (root / 'dictionary_compact.txt').write_text(compact, encoding='utf-8')
    return True


def write_dictionary(root: Path) -> Path:
    """Generate and write dictionary.pgd to the project root."""
    dictionary = generate_dictionary(root)
    out_path = root / 'dictionary.pgd'
    out_path.write_text(
        json.dumps(dictionary, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    # Also write the compact injection version
    compact = generate_compact_injection(dictionary)
    compact_path = root / 'dictionary_compact.txt'
    compact_path.write_text(compact, encoding='utf-8')

    return out_path


if __name__ == '__main__':
    root = Path('.')
    pgd = write_dictionary(root)
    # Print compact version to stdout
    dictionary = json.loads(pgd.read_text('utf-8'))
    print(generate_compact_injection(dictionary))
