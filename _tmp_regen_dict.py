"""Regenerate dictionary.pgd with new glyphs."""
from pathlib import Path
import sys, json
from src._resolve import src_import
sys.path.insert(0, '.')

generate_dictionary = src_import("symbol_dictionary_seq031", "generate_dictionary")

root = Path('.')
d = generate_dictionary(root)
out = root / 'dictionary.pgd'
out.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')

mg = d.get('module_glyphs', {})
print(f'Wrote dictionary.pgd: {len(mg)} glyphs, {d["stats"]["total_files"]} files')
print(f'\nAll glyphs:')
for g, n in sorted(mg.items()):
    print(f'  {g} = {n}')

# Count how many modules are still unmapped
unmapped = 0
for entry in d.get('modules', {}).values():
    for f in entry.get('files', []):
        pass  # all mapped if they're in modules dict

# Show stats
print(f'\nTotal module groups: {len(d.get("modules", {}))}')
