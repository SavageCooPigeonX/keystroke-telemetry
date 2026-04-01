"""Token-optimized auto-index builder for copilot-instructions.md.

Rewrites the auto-index to use the Chinese keymap from symbol_dictionary.
Before: `prediction_scorer_seq014_post_commit_scorer_seq012*` | auto extracted by pigeon compiler | ~607
After:  算14/post_commit_12 607t

Saves ~5,000+ tokens per prompt from the auto-index section alone.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys

# --- Load keymap from symbol_dictionary ---
def _load_keymap(root: Path) -> dict[str, str]:
    """Load Chinese char keymap from symbol_dictionary module."""
    # Try dictionary.pgd first (has module_glyphs section)
    pgd = root / 'dictionary.pgd'
    if pgd.exists():
        try:
            d = json.loads(pgd.read_text('utf-8'))
            mg = d.get('module_glyphs', {})
            # Invert: {glyph: name} -> {name: glyph}
            return {name: glyph for glyph, name in mg.items()}
        except Exception:
            pass
    
    # Fallback: hardcoded from _MNEMONIC_MAP
    return {
        'self_fix': '修', 'prediction_scorer': '算', 'context_budget': '境',
        'flow_engine': '流', 'file_heat_map': '热', 'drift_watcher': '漂',
        'compliance': '正', 'cognitive_reactor': '思', 'push_narrative': '叙',
        'import_rewriter': '引', 'logger': '录', 'resistance_bridge': '桥',
        'query_memory': '忆', 'dynamic_prompt': '推', 'streaming_layer': '层',
        'operator_stats': '控', 'research_lab': '研', 'models': '型',
        'graph_extractor': '图', 'file_writer': '写', 'scanner': '扫',
        'validator': '审', 'file_consciousness': '觉', 'rework_detector': '测',
        'symbol_dictionary': '典', 'glyph_compiler': '编', 'copilot_prompt_manager': '管',
        'mutation_scorer': '变', 'unsaid': '隐', 'training_writer': '训',
        'voice_style': '声', 'session_handoff': '递', 'staleness_alert': '警',
        'shard_manager': '片', 'context_router': '路', 'push_cycle': '环',
        'task_queue': '队', 'pulse_harvest': '脉', 'unified_signal': '合',
        'training_pairs': '对', 'rework_backfill': '补', 'unsaid_recon': '探',
        'timestamp_utils': '时', 'context_packet': '包', 'backward': '逆',
        'node_memory': '存', 'predictor': '预', 'learning_loop': '学',
        'demo_sim': '仿', 'dual_substrate': '双', 'live_server': '服',
        'traced_runner': '跑', 'trace_hook': '钩', 'cli': '令',
        'adapter': '适', 'drift': '偏', 'graph_heat_map': '描',
        'call_graph': '演', 'ast_parser': '查', 'deepseek_plan_prompt': '核',
        'deepseek_adapter': '谱', 'ether_map_builder': '拆',
        'import_fixer': '踪', 'heal': '追', 'execution_logger': '读',
        'func_decomposer': '译', 'class_decomposer': '织',
        'core_formatters': '联', 'aim_utils': '规', 'failure_detector': '缩',
        'loop_detector': '环检', 'observer_synthesis': '观',
        'node_awakener': '唤', 'path_selector': '择', 'task_writer': '任',
        'vein_transport': '脉运', 'dev_plan': '分', 'node_conversation': '话',
    }


def _find_glyph(name: str, keymap: dict[str, str]) -> str:
    """Find the glyph for a module name, checking parent prefixes."""
    if name in keymap:
        return keymap[name]
    # Check if this is a child module — try stripping suffixes
    # e.g. "self_fix_seq013_scan_hardcoded" -> try "self_fix"
    parts = name.split('_seq')
    if len(parts) > 1:
        parent = parts[0]
        if parent in keymap:
            return keymap[parent]
    # Try longest prefix match
    sorted_keys = sorted(keymap.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if name.startswith(key + '_') or name == key:
            return keymap[key]
    return ''


def _child_suffix(name: str, parent_name: str) -> str:
    """Extract the child-specific part of a name.
    
    e.g. 'self_fix_seq013_scan_hardcoded' parent='self_fix' -> 'scan_hardcoded'
         'backward_seq007_loss_compute' parent='backward' -> 'loss_compute'
    """
    # Try stripping parent_name_seqNNN_ prefix
    import re
    m = re.match(rf'^{re.escape(parent_name)}_seq\d+_(.+)$', name)
    if m:
        return m.group(1)
    # Try stripping parent_ prefix
    if name.startswith(parent_name + '_'):
        rest = name[len(parent_name) + 1:]
        # Strip leading seq\d+_ if present  
        rest = re.sub(r'^seq\d+_', '', rest)
        return rest if rest else name
    return name


def _is_child_module(name: str, folder: str) -> bool:
    """Check if this module is a child (inside a compiled package folder)."""
    # Children live in folders like backward_seq007/ or self_fix_seq013/
    parts = folder.replace('\\', '/').split('/')
    if len(parts) >= 2:
        last = parts[-1]
        if '_seq' in last:
            return True
    return False


def _build_compressed_index(root: Path, registry: dict, processed: int) -> str:
    """Build a token-compressed auto-index using Chinese keymap.
    
    Format:
      Root modules:     修13 one shot self fix 5.8K
      Child modules:    └ scan_hardcoded(1) loss_compute(2) ...
    
    Groups by folder, deduplicates, collapses children into parent lines.
    """
    keymap = _load_keymap(root)
    
    # Parse registry
    files = registry.get('files', []) if isinstance(registry, dict) else []
    if not files and isinstance(registry, dict):
        files = [{'path': k, **v} for k, v in registry.items() if isinstance(v, dict)]
    
    # Group by folder
    groups: dict[str, list[dict]] = {}
    seen: set[str] = set()
    
    for entry in files:
        if not isinstance(entry, dict):
            continue
        name = entry.get('name', '')
        seq = entry.get('seq', 0)
        path = entry.get('path', '')
        
        dedup_key = f"{name}_seq{seq:03d}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        
        folder = str(Path(path).parent).replace('\\', '/')
        if folder == '.':
            folder = '(root)'
        
        groups.setdefault(folder, []).append({
            'name': name,
            'seq': seq,
            'desc': (entry.get('desc') or '').replace('_', ' ')[:40],
            'tokens': entry.get('tokens', 0),
            'glyph': _find_glyph(name, keymap),
            'is_child': _is_child_module(name, folder),
            'folder': folder,
        })
    
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    total_modules = sum(len(v) for v in groups.values())
    
    lines = [
        '<!-- pigeon:auto-index -->',
        f'*{today} · {total_modules} modules · {processed} touched*',
        f'*Key: glyph·seq desc tokens | dictionary decodes glyphs*',
        '',
    ]
    
    # Identify parent folders (folders that contain child packages)
    child_folders = set()
    parent_lookup: dict[str, str] = {}  # child_folder -> parent_module_name
    for folder in groups:
        parts = folder.replace('\\', '/').split('/')
        if len(parts) >= 2 and '_seq' in parts[-1]:
            child_folders.add(folder)
            # Extract parent module name from folder name
            import re
            m = re.match(r'^(\w+)_seq\d+', parts[-1])
            if m:
                parent_lookup[folder] = m.group(1)
    
    for folder in sorted(groups.keys()):
        items = sorted(groups[folder], key=lambda x: (x['seq'], x['name']))
        
        if folder in child_folders:
            # Collapse children into a single line
            parent_name = parent_lookup.get(folder, '')
            g = _find_glyph(parent_name, keymap) if parent_name else ''
            total_tok = sum(i['tokens'] for i in items)
            tok_str = f"{total_tok/1000:.1f}K" if total_tok >= 1000 else f"{total_tok}"
            
            # Show child names compactly: scan_hardcoded(1) loss_compute(2)
            child_parts = []
            for item in items:
                suffix = _child_suffix(item['name'], parent_name)
                # Trim common prefixes like the parent seq
                suffix = suffix.replace(parent_name + '_', '')
                child_parts.append(f"{suffix}({item['seq']})")
            
            children_str = ' '.join(child_parts)
            if g:
                lines.append(f'  {g}└ {children_str} [{tok_str}]')
            else:
                lines.append(f'  └ {children_str} [{tok_str}]')
        else:
            # Regular folder header
            folder_display = folder.rstrip('/') 
            # Count children that will be collapsed under this folder
            child_count = 0
            for cf in child_folders:
                if cf.startswith(folder + '/'):
                    child_count += sum(1 for _ in groups.get(cf, []))
            
            header_count = len(items) + child_count
            lines.append(f'**{folder_display}** ({header_count})')
            
            for item in items:
                g = item['glyph']
                seq = item['seq']
                tok = item['tokens']
                desc = item['desc']
                
                # Strip useless descriptions
                if desc in ('auto extracted by pigeon compiler', 'pigeon extracted by compiler'):
                    desc = ''
                
                tok_str = f"{tok/1000:.1f}K" if tok >= 1000 else f"{tok}"
                
                if g:
                    if desc:
                        lines.append(f'{g}{seq} {desc} {tok_str}')
                    else:
                        lines.append(f'{g}{seq} {tok_str}')
                else:
                    short_name = item['name'][:16]
                    if desc:
                        lines.append(f'{short_name}·{seq} {desc} {tok_str}')
                    else:
                        lines.append(f'{short_name}·{seq} {tok_str}')
        
        # Only add blank line between top-level folders
        if folder not in child_folders:
            lines.append('')
    
    # Infrastructure (non-pigeon) — compact list
    infra_dirs = ['client', 'vscode-extension']
    infra_files: list[str] = []
    for folder in infra_dirs:
        fp = root / folder
        if fp.is_dir():
            for py in sorted(fp.glob('*.py')):
                if not py.name.startswith('__'):
                    infra_files.append(f'{folder}/{py.name}')
    root_py = sorted(
        p.name for p in root.glob('*.py')
        if not p.name.startswith('__') and '_seq' not in p.name
    )
    if infra_files or root_py:
        lines.append('**infra:** ' + ', '.join(root_py[:10]) + (', ...' if len(root_py) > 10 else ''))
        if infra_files:
            lines.append('**client:** ' + ', '.join(f.split('/')[-1] for f in infra_files))
        lines.append('')
    
    lines.append('<!-- /pigeon:auto-index -->')
    return '\n'.join(lines)


def measure_savings(root: Path) -> dict:
    """Measure token savings from compressed vs current auto-index."""
    ci_path = root / '.github' / 'copilot-instructions.md'
    if not ci_path.exists():
        return {'error': 'copilot-instructions.md not found'}
    
    ci = ci_path.read_text('utf-8')
    
    # Extract current auto-index
    import re
    m = re.search(
        r'<!-- pigeon:auto-index -->.*?<!-- /pigeon:auto-index -->',
        ci, re.DOTALL
    )
    current_chars = len(m.group(0)) if m else 0
    current_est_tokens = current_chars // 4
    
    # Build compressed version
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        return {'error': 'registry not found'}
    reg = json.loads(reg_path.read_text('utf-8'))
    
    compressed = _build_compressed_index(root, reg, 0)
    compressed_chars = len(compressed)
    compressed_est_tokens = compressed_chars // 4
    
    return {
        'current_chars': current_chars,
        'current_est_tokens': current_est_tokens,
        'compressed_chars': compressed_chars,
        'compressed_est_tokens': compressed_est_tokens,
        'savings_chars': current_chars - compressed_chars,
        'savings_tokens': current_est_tokens - compressed_est_tokens,
        'compression_ratio': f"{current_chars / compressed_chars:.1f}x" if compressed_chars else "N/A",
    }


if __name__ == '__main__':
    root = Path('.')
    
    # Measure savings
    savings = measure_savings(root)
    print("=== Token Savings Measurement ===")
    for k, v in savings.items():
        print(f"  {k}: {v}")
    
    # Show preview of compressed index
    reg = json.loads((root / 'pigeon_registry.json').read_text('utf-8'))
    compressed = _build_compressed_index(root, reg, 0)
    print(f"\n=== Compressed Auto-Index Preview ({len(compressed)} chars) ===")
    for line in compressed.split('\n')[:60]:
        print(line)
    if compressed.count('\n') > 60:
        print(f"... ({compressed.count(chr(10)) - 60} more lines)")
