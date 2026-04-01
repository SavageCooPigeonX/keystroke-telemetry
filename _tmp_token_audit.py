"""Token audit of copilot-instructions.md"""
from pathlib import Path
import re

ci = Path('.github/copilot-instructions.md').read_text(encoding='utf-8', errors='replace')

# Find auto-index section
start = ci.find('<!-- pigeon:auto-index -->')
end = ci.find('<!-- /pigeon:auto-index -->')
auto_index = ci[start:end]

# Count search pattern entries
patterns = re.findall(r'\| `([^`]+)`', auto_index)
print(f'Total search patterns in auto-index: {len(patterns)}')

avg_len = sum(len(p) for p in patterns) / len(patterns) if patterns else 0
print(f'Average pattern length: {avg_len:.1f} chars')
print(f'Total pattern chars: {sum(len(p) for p in patterns):,}')

print(f'\nLongest patterns:')
sorted_p = sorted(patterns, key=len, reverse=True)[:10]
for p in sorted_p:
    print(f'  {len(p):3d} chars: {p}')

# Show redundancy - patterns that share the same seq base
seq_bases = {}
for p in patterns:
    m = re.match(r'(\w+_seq\d+)', p)
    if m:
        base = m.group(1)
        seq_bases.setdefault(base, []).append(p)

dupes = {k: v for k, v in seq_bases.items() if len(v) > 1}
print(f'\nDuplicate seq bases (same module, multiple patterns): {len(dupes)}')
for base, pats in sorted(dupes.items(), key=lambda x: -len(x[1]))[:5]:
    print(f'  {base}: {len(pats)} entries')
    for p in pats:
        print(f'    {p}')

# Dictionary glyph analysis
dict_start = ci.find('[PIGEON DICT')
dict_end = ci.find('[/DICT]')
if dict_start > 0:
    dict_section = ci[dict_start:dict_end]
    # Chinese char mappings
    cn_maps = re.findall(r'([\u4e00-\u9fff])=(\w+)', dict_section)
    # ASCII 2-letter maps
    ascii_maps = re.findall(r'\b([A-Z]{2})=(\w+)', dict_section)
    print(f'\nDictionary: {len(cn_maps)} Chinese chars, {len(ascii_maps)} ASCII abbreviations')
    
    # Show all Chinese mappings
    print('\nChinese keymap:')
    for char, name in cn_maps:
        print(f'  {char} = {name}')

# Compute potential savings
print('\n=== POTENTIAL SAVINGS ===')
# Current: full pattern like `prediction_scorer_seq014_post_commit_scorer_seq012*`
# Compressed: `算_post_commit_seq012*` or just `算12*`
total_current = sum(len(p) for p in patterns)
# Estimate compressed: Chinese char (1) + _seq (4) + digits (2-3) + * (1) = ~9 chars avg
est_compressed = len(patterns) * 12  # generous estimate
print(f'Current total pattern chars: {total_current:,}')
print(f'Estimated compressed chars: {est_compressed:,}')
print(f'Savings: {total_current - est_compressed:,} chars ({(1 - est_compressed/total_current)*100:.0f}%)')
print(f'Estimated token savings: ~{(total_current - est_compressed) // 4:,} tokens')

# Also measure description column waste
descs = re.findall(r'\| ([^|]+) \| ~', auto_index)
desc_chars = sum(len(d.strip()) for d in descs)
print(f'\nDescription column: {desc_chars:,} chars (~{desc_chars//4:,} tokens)')

# Token column
tokens = re.findall(r'\| ~([\d,]+) \|', auto_index)
token_col_chars = sum(len(t) + 3 for t in tokens)  # ~NNN
print(f'Token column: {token_col_chars:,} chars')

# Table overhead (pipes, headers, folder headers)
overhead = len(auto_index) - total_current - desc_chars - token_col_chars
print(f'Table overhead (pipes, headers, whitespace): {overhead:,} chars')
