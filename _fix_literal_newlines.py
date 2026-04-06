"""Fix __init__.py files that have literal \\n instead of actual newlines."""
import os
import ast

fixed = []
for search_root in ['src', 'pigeon_compiler', 'pigeon_brain']:
    if not os.path.isdir(search_root):
        continue
    for root, dirs, files in os.walk(search_root):
        if '__init__.py' in files:
            p = os.path.join(root, '__init__.py')
            with open(p, encoding='utf-8') as f:
                content = f.read()
            
            # Check if content has literal \n (backslash + n) that should be newlines
            # Symptom: file has content but only 1 line, and contains the string \n
            lines = content.splitlines()
            if len(lines) <= 2 and len(content) > 30 and '\\n' in content:
                # Replace literal \n with actual newlines
                new_content = content.replace('\\n', '\n')
                # Verify it parses
                try:
                    ast.parse(new_content)
                    with open(p, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed.append(p)
                    print(f"FIXED: {p}")
                except SyntaxError as e:
                    print(f"STILL BROKEN after fix: {p} -> {e}")
            else:
                # Also check if it has syntax errors at all
                if content.strip():
                    try:
                        ast.parse(content)
                    except SyntaxError as e:
                        print(f"SYNTAX ERROR (not literal \\n): {p} -> {e}")

print(f"\nFixed {len(fixed)} files")
