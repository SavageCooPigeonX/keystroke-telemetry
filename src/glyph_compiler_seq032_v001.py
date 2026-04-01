"""Glyph compiler: Python → maximum symbolic compression.

Takes a .py file + the live dictionary and compresses it into
a .psg (Pigeon Symbolic Glyph) file where:
- Module references → single glyphs (Σ, Φ, Δ)
- Functions → module.ƒN scoped IDs
- Variables → Greek lowercase (μ, γ, δ, ε...)
- Operators → symbolic (→, ∀, ∃, ∅, ⊕)
- Types → superscript (ᵀ, ˢ, ⁿ, ᵇ, ˡ, ᵈ)
- Control flow → compressed notation
- String literals → kept (semantic anchors)
- Numeric literals → kept

The output is UNREADABLE without the dictionary.
That's the point.
"""
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-01T04:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  initial glyph compiler for max compression
# EDIT_STATE: harvested
# ── /pulse ──

from __future__ import annotations
import ast
import json
import re
import textwrap
from pathlib import Path
from collections import OrderedDict


# ── Operator glyph table ──
OP_GLYPHS = {
    'return': '→',
    'yield': '⟿',
    'import': '⊕',
    'from': '←',
    'None': '∅',
    'True': '⊤',
    'False': '⊥',
    'not': '¬',
    'and': '∧',
    'or': '∨',
    'in': '∈',
    'not in': '∉',
    'is': '≡',
    'is not': '≢',
    'for': '∀',
    'if': '⟨?',
    'elif': '⟨??',
    'else': '⟨!',
    'while': '⟳',
    'try': '⟨⚡',
    'except': '⟨✗',
    'finally': '⟨∞',
    'with': '⟨⊃',
    'as': '↦',
    'class': '◈',
    'def': 'ƒ',
    'self': '@',
    'append': '←+',
    'extend': '←++',
    'len': '|·|',
    'isinstance': '∈?',
    'hasattr': '∃.',
    'getattr': '⊙.',
    'setattr': '⊙.=',
    'enumerate': '∀#',
    'sorted': '↕',
    'dict': '⟪⟫',
    'list': '⟨⟩',
    'set': '⟬⟭',
    'tuple': '⟮⟯',
    'str': 'ˢ',
    'int': 'ⁿ',
    'float': 'ʳ',
    'bool': 'ᵇ',
    'Path': 'Ṗ',
}

# Variable glyph pool — Greek lowercase + math symbols
VAR_POOL = list('αβγδεζηθικλμνξοπρστυφχψωℓ')
PARAM_POOL = list('αβγδεζηθικλμνξοπρστυφχψω')


def _load_module_glyphs(root: Path) -> dict[str, str]:
    """Load module→glyph map from dictionary.pgd."""
    pgd = root / 'dictionary.pgd'
    if not pgd.exists():
        return {}
    data = json.loads(pgd.read_text('utf-8'))
    mg = data.get('module_glyphs', {})
    # Invert: glyph→name to name→glyph
    return {v: k for k, v in mg.items()}


def _load_intent_glyphs(root: Path) -> dict[str, str]:
    """Load intent→lambda code map."""
    pgd = root / 'dictionary.pgd'
    if not pgd.exists():
        return {}
    data = json.loads(pgd.read_text('utf-8'))
    ig = data.get('intent_glyphs', {})
    return {v: k for k, v in ig.items()}


class GlyphCompiler:
    """Compiles a Python file into maximum glyph-compressed form."""

    def __init__(self, root: Path):
        self.root = root
        self.mod_glyphs = _load_module_glyphs(root)
        self.intent_glyphs = _load_intent_glyphs(root)
        # Per-file state (functions are file-scoped)
        self.func_glyphs: dict[str, str] = {}
        self._func_idx = 0
        self._func_names = 'ƒαβγδεζηθκλμνξπρστυφχψω'
        # Per-function scoped (reset per function for glyph reuse)
        self.var_glyphs: dict[str, str] = {}
        self.param_glyphs: dict[str, str] = {}
        self._var_idx = 0
        self._param_idx = 0
        # Tracking: all scoped dicts for dictionary output
        self._all_scoped: dict[str, dict[str, str]] = {}  # func→{name: glyph}
        self._current_func: str | None = None
        # Dictionary entries generated during compilation
        self.dictionary: OrderedDict[str, str] = OrderedDict()

    def _assign_func_glyph(self, name: str) -> str:
        if name in self.func_glyphs:
            return self.func_glyphs[name]
        if self._func_idx < len(self._func_names):
            g = self._func_names[self._func_idx]
        else:
            g = f'ƒ{self._func_idx}'
        self._func_idx += 1
        self.func_glyphs[name] = g
        return g

    def _assign_var_glyph(self, name: str) -> str:
        if name in self.var_glyphs:
            return self.var_glyphs[name]
        if self._var_idx < len(VAR_POOL):
            g = VAR_POOL[self._var_idx]
        else:
            g = f'v{self._var_idx}'
        self._var_idx += 1
        self.var_glyphs[name] = g
        return g

    def _assign_param_glyph(self, name: str) -> str:
        if name == 'self':
            return '@'
        if name in self.param_glyphs:
            return self.param_glyphs[name]
        if self._param_idx < len(PARAM_POOL):
            g = PARAM_POOL[self._param_idx]
        else:
            g = f'p{self._param_idx}'
        self._param_idx += 1
        self.param_glyphs[name] = g
        return g

    def _compress_module_ref(self, name: str) -> str:
        """Replace module references with dictionary glyphs."""
        # Extract base module name from pigeon filename
        base = re.sub(r'_seq\d+.*$', '', name)
        if base in self.mod_glyphs:
            return self.mod_glyphs[base]
        # Try exact match
        if name in self.mod_glyphs:
            return self.mod_glyphs[name]
        return name

    def _compress_import(self, line: str) -> str:
        """Compress import statements to glyph form."""
        # from src.module_seq... import X, Y
        m = re.match(
            r'^(\s*)(from\s+)([\w.]+)\s+(import\s+)(.*)',
            line,
        )
        if m:
            indent = m.group(1)
            mod_path = m.group(3)
            imports = m.group(5)
            # Try to resolve the module path to a glyph
            parts = mod_path.split('.')
            leaf = parts[-1]
            base = re.sub(r'_seq\d+.*$', '', leaf)
            glyph = self.mod_glyphs.get(base, leaf)
            # Compress imported names
            import_names = [n.strip() for n in imports.split(',')]
            compressed_names = []
            for n in import_names:
                if n in OP_GLYPHS:
                    compressed_names.append(OP_GLYPHS[n])
                else:
                    compressed_names.append(n)
            return f'{indent}⊕ {", ".join(compressed_names)} ← {glyph}'

        # import module
        m2 = re.match(r'^(\s*)(import\s+)([\w.]+)', line)
        if m2:
            indent = m2.group(1)
            mod_path = m2.group(3)
            parts = mod_path.split('.')
            leaf = parts[-1]
            base = re.sub(r'_seq\d+.*$', '', leaf)
            glyph = self.mod_glyphs.get(base, leaf)
            return f'{indent}⊕ {glyph}'

        return line

    def _compress_line(self, line: str) -> str:
        """Apply maximum compression to a single line."""
        stripped = line.lstrip()
        indent = line[:len(line) - len(stripped)]
        indent_level = len(indent) // 4 if indent else 0
        new_indent = '·' * indent_level  # Single-char indent

        if not stripped:
            return ''
        # Strip ALL comments — meaning is in dictionary
        if stripped.startswith('#'):
            return ''

        result = stripped

        # Replace self. FIRST (before operator glyphs transform 'self')
        result = result.replace('self.', '@')
        result = result.replace('self', '@')

        # Apply operator glyphs (longest first to avoid partial matches)
        for word, glyph in sorted(OP_GLYPHS.items(), key=lambda x: -len(x[0])):
            if word == 'self':
                continue  # Already handled above
            result = re.sub(rf'\b{re.escape(word)}\b', glyph, result)

        # Replace known variable names (longest first)
        for var, glyph in sorted(self.var_glyphs.items(), key=lambda x: -len(x[0])):
            result = re.sub(rf'\b{re.escape(var)}\b', glyph, result)

        # Replace known param names (longest first)
        for param, glyph in sorted(self.param_glyphs.items(), key=lambda x: -len(x[0])):
            result = re.sub(rf'\b{re.escape(param)}\b', glyph, result)

        # Replace known function names
        for func, glyph in sorted(self.func_glyphs.items(), key=lambda x: -len(x[0])):
            result = re.sub(rf'\b{re.escape(func)}\b', glyph, result)

        # Replace module references
        for mod, glyph in sorted(self.mod_glyphs.items(), key=lambda x: -len(x[0])):
            result = re.sub(rf'\b{re.escape(mod)}\b', glyph, result)

        # Compress common Python patterns
        result = result.replace('.replace', '.ℛ')
        result = result.replace('.startswith', '.⊢')
        result = result.replace('.endswith', '.⊣')
        result = result.replace('.splitlines', '.⫾')
        result = result.replace('.readlines', '.⫾')
        result = result.replace('.read_text', '.⊲')
        result = result.replace('.write_text', '.⊳')
        result = result.replace('.rglob', '.⊛')
        result = result.replace('.glob', '.⊛')
        result = result.replace('.exists', '.∃')
        result = result.replace('.mkdir', '.⊞')
        result = result.replace('.is_dir', '.⊡')
        result = result.replace('.relative_to', '.⊖')
        result = result.replace('.strip()', '.⊘')
        result = result.replace('.lstrip()', '.⊘l')
        result = result.replace('.rstrip()', '.⊘r')
        result = result.replace('.split(', '.⊘s(')
        result = result.replace('.count(', '.#(')
        result = result.replace('.items()', '.⊙')
        result = result.replace('.keys()', '.⊙k')
        result = result.replace('.values()', '.⊙v')
        result = result.replace('.get(', '.⊙g(')
        result = result.replace('.setdefault(', '.⊙d(')
        result = result.replace('encoding=', 'enc=')
        result = result.replace("'utf-8'", 'U8')
        result = result.replace('continue', '⟳')
        result = result.replace('break', '⊘⟳')
        result = result.replace('raise ', '⚡ ')
        result = result.replace('Exception', '⚡X')
        result = result.replace('ImportError', '⚡⊕')

        # Strip trailing whitespace
        result = result.rstrip()
        if not result:
            return ''

        return f'{new_indent}{result}'

    def compile_file(self, filepath: Path) -> tuple[str, dict]:
        """Compile a Python file to maximum glyph compression.

        Returns (compressed_source, dictionary_entries).
        """
        text = filepath.read_text('utf-8')
        tree = ast.parse(text)
        lines = text.splitlines()

        # Phase 1: Extract all names from AST
        self._extract_names(tree)

        # Phase 2: Build the glyph header
        header = self._build_header(filepath)

        # Phase 3: Compress source line by line
        compressed = []
        in_docstring = False
        for line in lines:
            stripped = line.strip()

            # Skip ALL pigeon headers, pulse blocks, empty lines
            if stripped.startswith('# ──') or stripped.startswith('# SEQ:') or \
               stripped.startswith('# DESC:') or stripped.startswith('# INTENT:') or \
               stripped.startswith('# LAST:') or stripped.startswith('# SESSIONS:') or \
               stripped.startswith('# EDIT_TS:') or stripped.startswith('# EDIT_HASH:') or \
               stripped.startswith('# EDIT_WHY:') or stripped.startswith('# EDIT_STATE:'):
                continue

            # Skip ALL docstrings — meaning is in dictionary
            if '"""' in stripped:
                if stripped.count('"""') >= 2:
                    continue  # Single-line docstring
                in_docstring = not in_docstring
                continue
            if in_docstring:
                continue

            # Skip empty lines
            if not stripped:
                continue

            # Handle imports
            if stripped.startswith(('import ', 'from ')):
                compressed.append(self._compress_import(line))
                continue

            # Handle function/class defs
            if stripped.startswith('def '):
                m = re.match(r'^(\s*)def\s+(\w+)\s*\((.*?)\)', line, re.DOTALL)
                if m:
                    indent_level = len(m.group(1)) // 4
                    indent = '·' * indent_level
                    fname = m.group(2)
                    # Reset var/param pool for THIS function (per-function scoping)
                    self._enter_function(fname, tree, lines)
                    params = m.group(3)
                    fglyph = self.func_glyphs.get(fname, fname)
                    cp = self._compress_params(params)
                    compressed.append(f'{indent}ƒ {fglyph}({cp}):')
                    continue

            if stripped.startswith('class '):
                m = re.match(r'^(\s*)class\s+(\w+)', line)
                if m:
                    indent = '·' * (len(m.group(1)) // 4)
                    cname = m.group(2)
                    compressed.append(f'{indent}◈ {cname}:')
                    continue

            # General line compression
            c = self._compress_line(line)
            if c.strip('·').strip():  # Skip blank lines
                compressed.append(c)

        # Phase 4: Build dictionary entries
        dict_entries = self._build_dict_entries(filepath)

        # Assemble output
        output_lines = [header, ''] + compressed
        output = '\n'.join(output_lines)

        return output, dict_entries

    def _extract_names(self, tree: ast.AST):
        """Walk AST and assign glyphs to all functions.
        Variable/param glyphs assigned per-function during compression.
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._assign_func_glyph(node.name)

    def _enter_function(self, func_name: str, tree: ast.AST, text_lines: list[str]):
        """Reset variable/param pools for a new function scope.
        This is what gives us glyph reuse — α,β,γ reset per function.
        """
        self._current_func = func_name
        self.var_glyphs = {}
        self.param_glyphs = {}
        self._var_idx = 0
        self._param_idx = 0

        # Walk just this function's AST to pre-assign params
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                for arg in node.args.args:
                    if arg.arg != 'self':
                        self._assign_param_glyph(arg.arg)
                if node.args.kwonlyargs:
                    for arg in node.args.kwonlyargs:
                        self._assign_param_glyph(arg.arg)
                # Walk body for variable assignments
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                self._assign_var_glyph(target.id)
                            elif isinstance(target, ast.Tuple):
                                for elt in target.elts:
                                    if isinstance(elt, ast.Name):
                                        self._assign_var_glyph(elt.id)
                    if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                        self._assign_var_glyph(child.target.id)
                    # For comprehension variables
                    if isinstance(child, ast.comprehension) and isinstance(child.target, ast.Name):
                        self._assign_var_glyph(child.target.id)
                break

        # Save scope for dictionary
        scope = {}
        scope.update(self.param_glyphs)
        scope.update(self.var_glyphs)
        self._all_scoped[func_name] = scope

    def _compress_params(self, params_str: str) -> str:
        """Compress function parameters to glyph form."""
        if not params_str.strip():
            return ''
        parts = []
        for p in params_str.split(','):
            p = p.strip()
            if not p:
                continue
            # Handle defaults: name=value or name: type = value
            name_part = p.split('=')[0].split(':')[0].strip()
            rest = p[len(name_part):]
            if name_part == 'self':
                parts.append('@')
            elif name_part in self.param_glyphs:
                parts.append(self.param_glyphs[name_part] + rest)
            else:
                g = self._assign_param_glyph(name_part)
                parts.append(g + rest)
        return ', '.join(parts)

    def _build_header(self, filepath: Path) -> str:
        """Build compressed file header."""
        stem = filepath.stem
        # Extract module glyph
        base = re.sub(r'_seq\d+.*$', '', stem)
        mod_g = self.mod_glyphs.get(base, base)

        # Extract seq/ver/date
        seq_m = re.search(r'_seq(\d+)', stem)
        ver_m = re.search(r'_v(\d+)', stem)
        date_m = re.search(r'_d(\d+)', stem)
        intent_m = re.search(r'_lc_(.+)$', stem)

        seq = seq_m.group(1) if seq_m else '?'
        ver = ver_m.group(1) if ver_m else '?'
        date = date_m.group(1) if date_m else '?'
        intent = ''
        if intent_m:
            intent_name = intent_m.group(1)
            intent = self.intent_glyphs.get(intent_name, intent_name)

        parts = [f'{mod_g}{seq}']
        parts.append(f'v{ver}')
        if date != '?':
            parts.append(date)
        if intent:
            parts.append(intent)

        return f'# {".".join(parts)}.psg'

    def _build_dict_entries(self, filepath: Path) -> dict:
        """Build dictionary entries for this compilation."""
        entries = OrderedDict()

        # Module-level
        stem = filepath.stem
        base = re.sub(r'_seq\d+.*$', '', stem)
        mod_g = self.mod_glyphs.get(base, base)

        # Functions (file-scoped)
        for name, glyph in self.func_glyphs.items():
            entries[f'{mod_g}.{glyph}'] = name

        # Per-function scoped vars/params
        for func_name, scope in self._all_scoped.items():
            fglyph = self.func_glyphs.get(func_name, func_name)
            for name, glyph in scope.items():
                entries[f'{mod_g}.{fglyph}.{glyph}'] = name

        return entries


def compile_to_glyph(root: Path, filepath: Path) -> tuple[str, dict]:
    """Public API: compile a Python file to maximum glyph compression."""
    compiler = GlyphCompiler(root)
    return compiler.compile_file(filepath)


def compile_and_write(root: Path, filepath: Path) -> Path:
    """Compile a Python file and write the .psg output + dictionary."""
    compressed, dict_entries = compile_to_glyph(root, filepath)

    # Write .psg file alongside original
    out_path = filepath.with_suffix('.psg')
    out_path.write_text(compressed, encoding='utf-8')

    # Append to dictionary
    dict_path = root / 'dictionary_per_file.json'
    existing = {}
    if dict_path.exists():
        try:
            existing = json.loads(dict_path.read_text('utf-8'))
        except Exception:
            pass

    existing[filepath.name] = dict_entries
    dict_path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )

    return out_path


if __name__ == '__main__':
    import sys
    root = Path('.')
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        # Default: compile the longest src/ file
        target = max(
            root.glob('src/self_fix_seq013*.py'),
            key=lambda f: len(f.read_text('utf-8')),
        )

    print(f'Compiling: {target}')
    print(f'Lines: {len(target.read_text("utf-8").splitlines())}')

    out, dictionary = compile_to_glyph(root, target)
    out_path = target.with_suffix('.psg')
    out_path.write_text(out, encoding='utf-8')

    print(f'\nOutput: {out_path}')
    print(f'Compressed lines: {len(out.splitlines())}')
    print(f'Original chars: {len(target.read_text("utf-8"))}')
    print(f'Compressed chars: {len(out)}')
    ratio = len(target.read_text('utf-8')) / max(len(out), 1)
    print(f'Compression ratio: {ratio:.1f}x')
    print(f'\nDictionary entries: {len(dictionary)}')
    print(f'\n--- DICTIONARY ---')
    for k, v in dictionary.items():
        print(f'  {k} = {v}')
    print(f'\n--- COMPRESSED OUTPUT (first 80 lines) ---')
    for line in out.splitlines()[:80]:
        print(line)
