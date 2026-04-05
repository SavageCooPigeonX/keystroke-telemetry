"""Scan Python file compression ratios and intent extraction payload."""
import ast, os, json, sys
from pathlib import Path

src = Path('src')
results = []

for f in sorted(src.glob('*.py')):
    try:
        raw = f.read_text(encoding='utf-8')
        lines = raw.splitlines()
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        tree = ast.parse(raw)
        funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        
        # Docstrings line count
        docstrings = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    if isinstance(node.body[0].value.value, str):
                        docstrings += len(node.body[0].value.value.split('\n'))
        
        chars = len(raw)
        tokens_est = chars // 4
        total = len(lines)
        blank = total - len(code_lines)
        noise = (len(imports) + docstrings + blank) / max(total, 1)
        semantic_density = 1 - noise
        intent_density = (len(funcs) + len(classes)) / max(len(code_lines), 1)
        
        results.append({
            'file': f.name[:50],
            'lines': total,
            'code': len(code_lines),
            'funcs': len(funcs),
            'imports': len(imports),
            'docstrings': docstrings,
            'noise': round(noise, 3),
            'sem_density': round(semantic_density, 3),
            'intent_per_line': round(intent_density, 4),
            'tokens_est': tokens_est,
            'compressed_est': int(tokens_est * semantic_density),
        })
    except Exception as e:
        pass

results.sort(key=lambda x: x['sem_density'], reverse=True)

densities = [r['sem_density'] for r in results]
print(f"=== {len(results)} src/*.py files scanned ===\n")
print("SEMANTIC DENSITY DISTRIBUTION:")
print(f"  Max:    {max(densities):.3f}")
print(f"  Min:    {min(densities):.3f}")
print(f"  Mean:   {sum(densities)/len(densities):.3f}")
print(f"  Median: {sorted(densities)[len(densities)//2]:.3f}")

total_tokens = sum(r['tokens_est'] for r in results)
total_compressed = sum(r['compressed_est'] for r in results)
total_funcs = sum(r['funcs'] for r in results)
total_imports = sum(r['imports'] for r in results)
total_docstrings = sum(r['docstrings'] for r in results)
total_lines = sum(r['lines'] for r in results)
total_code = sum(r['code'] for r in results)

print(f"\nCOMPRESSION MATH:")
print(f"  Total lines:             {total_lines:,}")
print(f"  Code lines:              {total_code:,} ({total_code/total_lines*100:.1f}%)")
print(f"  Total tokens (est):      {total_tokens:,}")
print(f"  After noise strip:       {total_compressed:,}")
print(f"  Compression ratio:       {total_tokens/max(total_compressed,1):.2f}x")
print(f"  Tokens saved:            {total_tokens - total_compressed:,} ({(total_tokens-total_compressed)/total_tokens*100:.1f}%)")

print(f"\nNOISE BREAKDOWN:")
print(f"  Imports:                 {total_imports} lines")
print(f"  Docstrings:              {total_docstrings} lines")
print(f"  Blank/comment:           {total_lines - total_code} lines")
print(f"  Total noise:             {total_imports + total_docstrings + (total_lines - total_code)} lines ({(total_imports + total_docstrings + (total_lines - total_code))/total_lines*100:.1f}%)")

print(f"\nINTENT EXTRACTION PAYLOAD:")
print(f"  Total functions:         {total_funcs}")
print(f"  Funcs per 1K tokens:     {total_funcs/(total_tokens/1000):.2f}")
print(f"  Funcs per 1K compressed: {total_funcs/(total_compressed/1000):.2f}")
print(f"  Intent amplification:    {(total_funcs/(total_compressed/1000))/(total_funcs/(total_tokens/1000)):.2f}x")
print(f"  Bytes per intent unit:   {total_tokens * 4 / total_funcs:.0f}")

# Theoretical maximum: strip ALL noise, keep only function bodies
print(f"\nTHEORETICAL MAX COMPRESSION:")
pure_code_tokens = total_code * 10  # ~10 tokens per code line average
min_tokens = total_funcs * 15  # absolute minimum: function signature + 1 line body
print(f"  Pure code tokens:        ~{pure_code_tokens:,}")
print(f"  Skeleton tokens:         ~{min_tokens:,} (sig + 1-line body)")
print(f"  Max compression ratio:   {total_tokens/max(min_tokens,1):.1f}x")
print(f"  But meaning retained:    ~{min_tokens/total_tokens*100:.1f}% of tokens carry {100:.0f}% of intent")

print(f"\nTOP 10 DENSEST (already maximally compressed):")
for r in results[:10]:
    sd = r['sem_density']
    ipl = r['intent_per_line']
    name = r['file']
    print(f"  {sd:.3f} | {ipl:.3f} i/L | {name}")

print(f"\nBOTTOM 10 (most compressible — highest noise):")
for r in results[-10:]:
    sd = r['sem_density']
    n = r['noise']
    name = r['file']
    print(f"  {sd:.3f} | noise={n:.3f} | {name}")

# The AGI question: information-theoretic bound
print(f"\n{'='*60}")
print(f"ENTROPY / AGI MATH:")
print(f"{'='*60}")
import math
# Shannon entropy of the codebase as a symbol system
# Each function is a "symbol" — its information content = -log2(freq)
# If all functions equally likely: H = log2(N)
H_max = math.log2(total_funcs)
# Actual entropy depends on call frequency (we don't have that), so bound it
print(f"  Function symbol space:   {total_funcs} symbols")
print(f"  Max entropy (uniform):   {H_max:.2f} bits")
print(f"  Tokens per bit of intent: {total_tokens / (H_max * total_funcs):.1f}")
print(f"  Compressed tokens/bit:   {total_compressed / (H_max * total_funcs):.1f}")
print(f"")
print(f"  The 'AGI payload' question:")
print(f"  If meaning = intent extraction per token,")
print(f"  and compression = noise removal,")
print(f"  then max meaning per token = {total_funcs / total_compressed * 1000:.2f} intents/Ktok")
print(f"  Current meaning per token = {total_funcs / total_tokens * 1000:.2f} intents/Ktok")
print(f"  Meaning amplification via compression: {(total_funcs/total_compressed)/(total_funcs/total_tokens):.2f}x")
print(f"")
print(f"  Entropy drop explanation:")
print(f"  Global H was 0.295. After 4 explicit shed blocks,")
print(f"  confidence rises → H = 1 - conf → H drops.")
print(f"  This means: the system is LEARNING which modules")
print(f"  it understands vs doesn't. The shed blocks are")
print(f"  calibration signals — each one narrows uncertainty.")
print(f"  More sheds = lower global H = more precise targeting.")
